# -*- coding: UTF-8 -*-

###
# Reading the output file of region filter.(batch or single)
# cal the time with given threshold.
###

import argparse
import os
import time
import warnings
from glob import glob
from itertools import groupby
from operator import itemgetter

import cv2
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from pythonvideoannotator_models.models import Project
from shapely.geometry import Polygon, Point, MultiPolygon
from tqdm import tqdm

warnings.filterwarnings('ignore')


def main_load(project_path):
    project = Project()
    project.load({}, project_path)
    return project


def get_geo(video, name):
    for geo in video.geometries:
        if geo.name == name:
            return geo


def try_fix_path(proj_dir):
    project = main_load(proj_dir)
    videos = project.videos
    for video in videos:
        file_path = video.filepath
        if not os.path.exists(file_path):
            if os.path.exists(video.filepath.replace('\\', '/')):
                video.filepath = video.filepath.replace('\\', '/')
    project.save(project_path=proj_dir)


def cal_dis(L, R, FPS, contours, head_list=None):
    L_geo = Polygon(L._geometry[0][1])
    R_geo = Polygon(R._geometry[0][1])
    # convert to polygon
    if head_list:
        head2L = [L_geo.distance(Point(p)) for p in head_list]
        head2R = [R_geo.distance(Point(p)) for p in head_list]
        body2L = [L_geo.distance(Polygon(c)) for c in contours]
        body2R = [R_geo.distance(Polygon(c)) for c in contours]
        distance_df = pd.DataFrame(np.array([head2L, head2R, body2L, body2R]).T,
                                   columns=['head to L', 'head to R', 'body to L', 'body to R'])
        distance_df.insert(0, 'video time',
                           [time.strftime('%M:%S', time.localtime(_ / FPS)) for _ in range(distance_df.shape[0])])
    else:
        body2L = [L_geo.distance(Polygon(c)) for c in contours]
        body2R = [R_geo.distance(Polygon(c)) for c in contours]
        distance_df = pd.DataFrame(np.array([body2L, body2R]).T,
                                   columns=['body to L', 'body to R'])
        distance_df.insert(0, 'video time',
                           [time.strftime('%M:%S', time.localtime(_ / FPS)) for _ in range(distance_df.shape[0])])

    return distance_df


def view_status(L_geo, R_geo, contours, index):
    return MultiPolygon([L_geo, R_geo, Polygon(contours[index])])
    # view_status(L_geo,R_geo,contours,2420)


def extract_region(dis_df,FPS):
    result = []
    for k, g in groupby(enumerate(dis_df.index), lambda x: x[0] - x[1]):
        interval = list(map(itemgetter(1), g))
        if len(interval) >= 5:
            result.append(('%s - %s' % (interval[0], interval[-1]),
                           '%s - %s' % (time.strftime('%M:%S', time.localtime(interval[0] / FPS)),
                                         time.strftime('%M:%S', time.localtime(interval[1] / FPS))),
                           abs(interval[-1] - interval[0]),
                           round(abs(interval[-1] - interval[0])/FPS,2),
                           dis_df.loc[interval[0], 'accident'] if 'accident' in dis_df.columns else None
                           ))
    return result


def process_accident(dis_df, result_region, col):
    corrected_region = []
    for row in result_region:
        if type(row[-1]) == str:
            start_time = int(row[0].split(' - ')[0])
            mean_dis = []
            for idx in range(start_time - 20, start_time):
                dis2col = dis_df.loc[idx, col] - dis_df.loc[start_time, col]
                mean_dis.append(dis2col)
            mean_dis = np.mean(mean_dis)
            if mean_dis <= 0:
                # 说明在远离原来的物体col
                # 则去除
                continue
            corrected_region.append(row)
        else:
            corrected_region.append(row)
    return corrected_region


def subtract_dis(dis_df, ID, threshold=10,FPS=24):
    sub_L_df = dis_df.loc[dis_df.loc[:, 'body to L'] <= threshold, :]
    sub_R_df = dis_df.loc[dis_df.loc[:, 'body to R'] <= threshold, :]

    may_wrong_row = sub_L_df.loc[:, 'body to R'] <= threshold * 5
    if any(may_wrong_row):
        sub_L_df.loc[may_wrong_row, 'accident'] = 'too close to R'
    may_wrong_row = sub_R_df.loc[:, 'body to L'] <= threshold * 5
    if any(may_wrong_row):
        sub_R_df.loc[may_wrong_row, 'accident'] = 'too close to L'
    result_L = extract_region(sub_L_df,FPS)
    result_R = extract_region(sub_R_df,FPS)

    corrected_L = process_accident(dis_df, result_L, col='body to L')
    corrected_R = process_accident(dis_df, result_R, col='body to R')

    df_L = pd.DataFrame(corrected_L, columns=['start/f - end/f',
                                              'start - end(video time)',
                                              'duration/f',
                                              'duration/s',
                                              "accident"], index=['%s_L' % ID] * len(result_L))
    df_R = pd.DataFrame(corrected_R, columns=['start/f - end/f',
                                              'start - end(video time)',
                                              'duration/f',
                                              'duration/s',
                                              "accident"], index=['%s_R' % ID] * len(result_R))
    return pd.concat([df_L, df_R], axis=0)


def main(proj_dir, odir, plot=True):
    project = main_load(proj_dir)
    DATE_name = os.path.basename(proj_dir)

    dis_df_outdir = os.path.join(odir, DATE_name)
    draw_outdir = os.path.join(odir,dis_df_outdir, 'draw')
    os.makedirs(dis_df_outdir, exist_ok=True)
    os.makedirs(draw_outdir, exist_ok=True)

    total_output_file = os.path.join(dis_df_outdir, "total info.csv")
    total_output_df = pd.DataFrame(columns=["total walk distance",
                                            "duration to L/f",
                                            "duration to R/f",
                                            "duration to L/s",
                                            "duration to R/s",
                                            ])
    # if exist total df, read it else create it
    for video in tqdm(project.videos):
        group_name = os.path.basename(video.filepath).split('.')[0]
        output_file = os.path.join(dis_df_outdir, str(group_name) + '_full.csv')
        # get group name and create dir
        cap = cv2.VideoCapture(video.filepath)
        total_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        FPS = cap.get(cv2.CAP_PROP_FPS)
        # get video basic info
        assert os.path.exists(video.filepath)
        L = get_geo(video, 'L')
        R = get_geo(video, 'R')
        obj = list(video.objects2D)[0]
        contour_obj = [_ for _ in obj.datasets if 'contours' in _.name.lower()]
        assert len(contour_obj) == 1
        contour_obj = contour_obj[0]
        # get L,R, contour object
        if '_1' in video.name or '_2' in video.name:
            # extreme_points = [contour_obj.get_extreme_points(_) for _ in tqdm(range(int(total_frame)),
            #                                                                   total=total_frame)]
            # get extreme points, it takes time!!!!!!!!!!!!!!1
            # head_list = [_[0] for _ in extreme_points if _[0]]
            contours = [_[:, 0, :] for _ in contour_obj._contours]
            distance_df = cal_dis(L, R, FPS, contours)
            region_df = subtract_dis(distance_df, group_name, threshold=10,FPS=FPS)
            distance_df.to_csv(output_file, index=1, index_label='frame')
            region_df.to_csv(output_file.replace("_full", "_region"), index=1, index_label='frame')
            if plot:
                draw_graph(distance_df, draw_outdir, group_name)
            total_output_df.loc[group_name, :] = (0,
                                                  region_df.loc[region_df.index.str.endswith('_L'), 'duration/f'].sum(),
                                                  region_df.loc[region_df.index.str.endswith('_R'), 'duration/f'].sum(),
                                                  region_df.loc[region_df.index.str.endswith('_L'), 'duration/s'].sum(),
                                                  region_df.loc[region_df.index.str.endswith('_R'), 'duration/s'].sum(),
                                                  )
        try:
            total_distance = contour_obj.calc_walked_distance(0)[0][-1]
        except:
            total_distance = None
        total_output_df.loc[group_name, "total walk distance"] = total_distance
    total_output_df.to_csv(total_output_file, index=1, index_label='groupID')


def draw_graph(dis_df, outimg_dir, basename):
    layout = dict(width=2500,
                  height=1200,
                  font=dict(size=25))
    fig = go.Figure(layout=layout)
    fig2 = go.Figure(layout=layout)
    col_dict = {'head to L': '#1764ab',  # deep blue
                'body to L': '#94c4df',  # shallow blue
                'head to R': '#bc141a',  # deep red
                "body to R": '#fc8a6a', }  # shallow red}
    for col in dis_df.columns:
        if col not in col_dict:
            continue
        fig.add_scatter(x=dis_df.index,
                        y=dis_df.loc[:, col],
                        mode='lines',
                        name=col,
                        marker=dict(color=col_dict[col]))
        fig2.add_box(y=dis_df.loc[:, col],
                     marker=dict(color=col_dict[col]),
                     name=col)
    pio.write_image(fig, os.path.join(outimg_dir, basename) + '_line.png', format='png')
    pio.write_image(fig2, os.path.join(outimg_dir, basename) + '_box.png', format='png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", '--input_dir', help="which directory you want to process",
                        type=str, )
    parser.add_argument("-o", "--output_dir",
                        help="The directory you want to save your project(could be non-exist)",
                        type=str)

    parser.add_argument("-p", "--plot",
                        help="draw figure base on distance df",
                        action="store_true")
    parser.add_argument("-r", "--recursive",
                        help="recursive rename and move",
                        action="store_true")
    args = parser.parse_args()
    indir = os.path.abspath(args.input_dir)
    odir = os.path.abspath(args.output_dir)
    r = args.recursive
    p = args.plot
    os.makedirs(odir, exist_ok=True)
    if r:
        for dir in glob(os.path.join(indir, '*')):
            basename = os.path.basename(dir)
            if os.path.isdir(dir):
                print("recursively process each directory: %s" % basename)
                main(dir, odir, plot=p)
    else:
        main(indir, odir, plot=p)

    # python /home/liaoth/project/VD/video_annotator_script/extra_utils/cal_time.py -i /home/liaoth/data2/project/VD/data2/analysis/20190411 -o /home/liaoth/data2/project/VD/data2/result/ -p
