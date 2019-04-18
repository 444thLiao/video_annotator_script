###
# Reading the output file of region filter.(batch or single)
# cal the time with given threshold.
###


import argparse
import os
import re
from ast import literal_eval
from datetime import timedelta
from glob import glob
from itertools import groupby
from operator import itemgetter

import cv2
import numpy as np
import pandas as pd
from shapely import wkt
from tqdm import tqdm
import os, base64, numpy as np

def cal_time(video, dir_path, threshold, rt):
    if os.path.isdir(dir_path):
        iter_ob = tqdm(glob(os.path.join(dir_path, '*.csv')))

    else:
        iter_ob = tqdm([dir_path])
        dir_path = os.path.dirname(dir_path)
    cap = cv2.VideoCapture(video)
    f_2_rt = processing_rt(rt, cap)
    num_frame_per_s = cap.get(5)
    dir_dir_path = os.path.dirname(dir_path)
    make_dir = os.path.join(dir_dir_path, 'cal_time_csv')
    if not os.path.isdir(make_dir):
        os.system('mkdir -p %s' % make_dir)

    for each_csv in iter_ob:
        data = pd.read_csv(each_csv, header=None, index_col=0, sep=';')
        data.columns = ['distance']
        data.index.name = 'time/s'
        data.loc[:, 'distance'] = [d if d >= 0 else -d for d in data.loc[:, 'distance']]
        time_frames = data.index[data.loc[:, 'distance'] <= int(threshold)]

        all_frames = []
        for k, g in groupby(enumerate(time_frames), lambda x: x[0] - x[1]):
            a_frame = list(map(itemgetter(1), g))
            if len(a_frame) > 1:
                duration = (a_frame[-1] - a_frame[0] + 1) / num_frame_per_s
                time_frame = [a_frame[0], a_frame[-1]]  # '%s - %s' % (a_frame[0], a_frame[-1])

                all_frames.append((time_frame, duration))

        result_df = output_df(all_frames, f_2_rt)
        new_name = os.path.join(make_dir, os.path.basename(each_csv))
        result_df.to_csv(new_name, index=False)


def processing_rt(rt, cap):
    total_frame = cap.get(7)
    num_frame_per_s = cap.get(5)
    if rt is None:
        print('missing starting time')
    else:
        frame_time_indic = {}
        for each in rt:
            h, m, s, f = map(int, re.split('[:;]', each))
            frame_time_indic[f] = timedelta(hours=h,
                                            minutes=m,
                                            seconds=s)
        f_2_rt = frame_time_indic.copy()
        last_one = frame_time_indic[0]
        last_frame = 0
        for f in range(total_frame):
            if f in frame_time_indic and f == 0:
                f_2_rt[f] = frame_time_indic[0] + timedelta(seconds=f // num_frame_per_s)
            elif f in frame_time_indic and f != 0:
                f_2_rt[f] = frame_time_indic[f]
                last_one = frame_time_indic[f]
                last_frame = f
            else:
                f_2_rt[f] = last_one + timedelta(seconds=(f - last_frame) // num_frame_per_s)
        return f_2_rt


def output_df(time_frame, f_2_rt):
    tmp = []
    for each in time_frame:
        start, end = each[0]
        rt_start, rt_end = f_2_rt.get(start, ''), f_2_rt.get(end, '')
        row = ['%s - %s' % (start, end),
               '%s - %s' % (str(rt_start), str(rt_end)),
               # (rt_end-rt_start).seconds +1,
               each[1],
               end - start + 1]
        tmp.append(row)
    new_df = pd.DataFrame(tmp, columns=['start/f - end/f',
                                        'start(rt) - end(rt)',
                                        'duration/s',
                                        'duration/f'])
    return new_df


def read_points(proj_dir, video, name):
    default_path = '%s/videos/%s/objects/object*/datasets/%s/path.cvs' % (proj_dir, video, name)
    if not glob(default_path):
        print('wrong path %s, Please check the name' % default_path)
    else:
        file_path = list(glob(default_path))[0]
        data = pd.read_csv(file_path, sep=';', index_col=0)
        return data


def read_obj(proj_dir, name):
    default_path = os.path.join(proj_dir,
                                'videos',
                                '*',
                                'objects',
                                name,
                                'data.geo')
    if not glob(default_path):
        print('wrong path %s, Please check the name' % default_path)
        return
    else:
        # if name =='R':
        #     import pdb;pdb.set_trace()
        file_path = list(glob(default_path))[0]
        data = literal_eval(open(file_path).read())
        polygon_data = data[0][1]
        poly = wkt.loads('POLYGON((%s))' % ', '.join([' '.join([str(v) for v in _]) for _ in (polygon_data + [polygon_data[0]])]))
        return poly
        # pt = wkt.loads('POINT(711 287)')
        #
        # poly.distance(pt)
        # poly.boundary.distance(pt)
from pythonvideoannotator_models.models.video.objects.object2d.object2d_base import Object2dBase
from pythonvideoannotator_models.models.video.objects.object2d.datasets.contours import Contours
from pythonvideoannotator_models.models.video import Video
from pythonvideoannotator_models.models import Project


def main_load(project_path):
    project = Project()
    project.load({}, project_path)
    return project

def get_video(project,name):
    for v in project.videos:
        if name in v.name:
            return v

def load_contours():
    pass


def main(proj_dir, rt, video):
    project = main_load(proj_dir)
    videos = project.videos
    for video in videos:
        total_frame = video.total_frames
        for obj in video.objects2D:
            contour = [_ for _ in obj.datasets if 'contours' in _.name.lower()]
            if not contour:
                raise Exception
            contour = contour[0]
            extreme_points = map(contour.get_extreme_points,range(total_frame))


    ############################################################
    video_name = os.path.basename(video).rpartition('.')[0]
    p1_data = read_points(proj_dir, video_name, 'p1')
    p2_data = read_points(proj_dir, video_name, 'p2')

    L_obj = read_obj(proj_dir, 'L')
    R_obj = read_obj(proj_dir, 'R')

    # video = '/home/liaoth/data2/project/RD_VD/2018111509.mp4'
    cap = cv2.VideoCapture(video)
    f_2_rt = processing_rt(rt, cap)

    merged_data = p1_data.join(p2_data, rsuffix='_p2')
    tmp = []
    for frame, vals in tqdm(enumerate(merged_data.values)):
        if 'None' in vals:
            tmp.append([None, None, None, None])
            continue
        p1, p2 = wkt.loads('POINT(%s %s)' % tuple(vals[:2])), wkt.loads('POINT(%s %s)' % tuple(vals[2:]))
        ld1, ld2 = L_obj.distance(p1), L_obj.distance(p2)
        rd1, rd2 = R_obj.distance(p1), R_obj.distance(p2)
        tmp.append([ld1, ld2, rd1, rd2])

    for i in ["dis_L_p1", "dis_L_p2", "dis_R_p1", "dis_R_p2"]:
        merged_data.loc[:, i] = 0
    merged_data.loc[:, ["dis_L_p1", "dis_L_p2", "dis_R_p1", "dis_R_p2"]] = tmp
    return merged_data, f_2_rt, props

def match_times(merged_data, f_2_rt, props):
    diff_data = np.apply_along_axis(np.diff, 0, merged_data.values[:, -4:])
    diff_df = pd.DataFrame(np.append(diff_data, [[0, 0, 0, 0]], 0), index=merged_data.index, columns=merged_data.columns[-4:])
    # L obj
    L_bool_idx = (diff_df.loc[:, ['dis_L_p1', 'dis_L_p2']] <= 1).all(1) & (merged_data.loc[:, ['dis_L_p1', 'dis_L_p2']] <= 45).any(1)
    # R obj
    R_bool_idx = (diff_df.loc[:, ['dis_R_p1', 'dis_R_p2']] <= 1).all(1) & (merged_data.loc[:, ['dis_R_p1', 'dis_R_p2']] <= 45).any(1)

    L_time = merged_data.index[L_bool_idx]
    R_time = merged_data.index[R_bool_idx]

    total_frames = int(float(props['duration']) * float(props['avg_frame_rate'].split('/')[0]))
    num_frame_per_s = float(total_frames) / float(props['duration'])

    all_frames = []
    for k, g in groupby(enumerate(L_time), lambda x: x[0] - x[1]):
        a_frame = list(map(itemgetter(1), g))
        if len(a_frame) > 1:
            duration = (a_frame[-1] - a_frame[0] + 1) / num_frame_per_s
            time_frame = [a_frame[0], a_frame[-1]]  # '%s - %s' % (a_frame[0], a_frame[-1])

            all_frames.append((time_frame, duration))

    L_df = output_df(all_frames, f_2_rt)

    all_frames = []
    for k, g in groupby(enumerate(R_time), lambda x: x[0] - x[1]):
        a_frame = list(map(itemgetter(1), g))
        if len(a_frame) > 1:
            duration = (a_frame[-1] - a_frame[0] + 1) / num_frame_per_s
            time_frame = [a_frame[0], a_frame[-1]]  # '%s - %s' % (a_frame[0], a_frame[-1])

            all_frames.append((time_frame, duration))

    R_df = output_df(all_frames, f_2_rt)
    return L_df, R_df


def filtering_region(data_df, input_region):
    region_df = pd.read_csv(input_region)
    list_r = [list(map(int, _)) for _ in data_df.loc[:, 'start/f - end/f'].str.split(' - ')]
    s_f = [_[0] for _ in list_r]
    e_f = [_[1] for _ in list_r]

    regions = list(np.concatenate([np.arange(_[0], _[1]) for _ in region_df.values]))

    subset_data = data_df.loc[[_s in regions and _e in regions for _s, _e in zip(s_f, e_f)], :]
    return subset_data


def further_summary(data_df, input_region):
    region_df = pd.read_csv(input_region)
    list_r = [list(map(int, _)) for _ in data_df.loc[:, 'start/f - end/f'].str.split(' - ')]
    s_f = [_[0] for _ in list_r]
    e_f = [_[1] for _ in list_r]

    sto_dict = {}
    for intervals in [np.arange(_[0], _[1]) for _ in region_df.values]:
        subset_data = data_df.loc[[_s in intervals and _e in intervals for _s, _e in zip(s_f, e_f)], :]
        sto_dict[(intervals[0], intervals[1])] = subset_data
    return sto_dict


# def main():
#     pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("video", help="video you processed")
    parser.add_argument("dir", help="directory path which storage all csv output.")
    parser.add_argument("threshold",
                        help="threshold you should give. [default=40]",
                        default=40)
    parser.add_argument("-rt", nargs='*', help='indicating the time. Using the format like 10:43:15;0 to indicate 10 am 43 min 15 seconds at 0 frame.')

    args = parser.parse_args()
    rt = args.rt

    merged_data, f_2_rt, props = main('/home/liaoth/data2/project/RD_VD/project_test',
                                      rt,
                                      args.video)
    L_df, R_df = match_times(merged_data,
                             f_2_rt,
                             props)

    t_path = '/home/liaoth/data2/project/RD_VD/2018111509.csv'
    sub_L = filtering_region(L_df, t_path)
    sub_R = filtering_region(R_df, t_path)

    L_info = further_summary(sub_L, t_path)
    R_info = further_summary(sub_R, t_path)
