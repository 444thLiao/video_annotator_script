import os
import random
import re
import string
from datetime import timedelta
from subprocess import check_call

import cv2
import pandas as pd
from tqdm import tqdm
from videoprops import get_video_properties

from utils import parse_metadata, data_parser


def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(stringLength))


def convert_time_with_rt(rt, video, times, cov_time=True):
    """
    rt mean real-time
    rt 形如 hh:mm:ss;frame, frame 一般是0,即人为的从视频的第一帧中获取现实时间(real time),从而校准现实时间与视频时间.
    输入的times可以是一串也可以是一个字符串,每个形如 hh:mm:ss
    cov_time是考虑到使用的小时制不一样导致的,如果为True,则+12小时,从12小时下的08pm转成成20. (不robust,但hh:mm:ss缺乏am,pm的信息,所以暂时这么写)
    输出一个list,长度等同于times (如果times是一个字符串,则输出一个长度为1的list)
    list内容为 现实时间所对应的帧数(frame)
    :param rt:
    :param video:
    :param times:
    :param cov_time:
    :return:
    """
    props = get_video_properties(video)
    total_frame = int(float(props['duration']) * float(eval(props['avg_frame_rate'])))
    num_frame_per_s = total_frame / float(props['duration'])
    if type(rt) == str:
        rt = [rt]
    if type(times) == str:
        times = [times]

    if rt is None:
        print('missing starting time')
    else:
        frames = []
        for each in rt:
            h, m, s, f = map(int, re.split('[:;]', each))
            start_frame_real_time = timedelta(hours=h, minutes=m, seconds=s)
            for t in times:
                h, m, s = map(int, re.split('[:;]', t))
                h = h + 12 if cov_time else h  # 12小时制转到24小时制,默认是下午的现实时间
                this_delta = timedelta(hours=h, minutes=m, seconds=s)

                delta_ = (this_delta - start_frame_real_time)
                if delta_.days < 0:
                    delta_seconds = 0
                else:
                    delta_seconds = delta_.seconds
                frames.append(delta_seconds * num_frame_per_s)
        return frames


def parse_rt_f(rt_f):
    """
    rt mean real time
    rt 形如 hh:mm:ss;frame, frame 一般是0,即人为的从视频的第一帧中获取现实时间(real time),从而校准现实时间与视频时间.
    解析rt文件, 例子可见example中的文件.(all_rt.txt)
    输出,每个视频文件所对应的rt
    :param rt_f:
    :return:
    """
    data = data_parser(rt_f, ft='csv')
    ori_files = [str(_) for _ in data.iloc[:, 0]]
    return dict(zip(ori_files,
                    data.iloc[:, 1]))


def _sub_split(indir, date, h, rt_dict, raw_stime, raw_etime, cov_time=False):
    """
    1. 构建video地址
    2. 获取rt_dict内的rt,从而校准视频时间与现实时间
    3. 现实时间 (起始时间), cov_time是考虑到使用的小时制不一样导致的
    :param indir: For 1
    :param date: For 1
    :param h: For 1
    :param rt_dict: For 2
    :param raw_stime: For 3
    :param raw_etime: For 3
    :param cov_time: For 3
    :return:
    """
    video = os.path.join(indir, str(date) + str(h) + '.avi')
    if not os.path.isfile(video):
        raise Exception
    rt = rt_dict[os.path.basename(video)]
    video_sframe, video_eframe = convert_time_with_rt(rt, video, [raw_stime, raw_etime], cov_time=cov_time)
    cap = cv2.VideoCapture(video)
    video_stime = str(timedelta(seconds=int(video_sframe / cap.get(5) + 3)))
    video_duration = str(timedelta(seconds=int((video_eframe - video_sframe) / cap.get(5))))
    if video_eframe < video_sframe:
        print("Some end frame is smaller than start frame, it may occur some errors.")
        import pdb
        pdb.set_trace()
    return video, video_stime, video_duration


def split_cmd(infile, ofile, stime, duration):
    cmd = "/usr/bin/ffmpeg -ss {stime} -i {infile} -c copy -t {duration} {ofile} -loglevel -8".format(stime=stime,
                                                                                                      infile=infile,
                                                                                                      ofile=ofile,
                                                                                                      duration=duration
                                                                                                      )
    return cmd


def split_video_trans(indir, date, rt_dict, raw_stime, raw_etime, fname, cov_time=True, keep_intermediate=False):
    s_h, s_m, s_s = map(int, re.split('[:;]', raw_stime))
    s_h = s_h + 12 if cov_time else s_h  # 12小时制转到24小时制,默认是下午的现实时间
    e_h, e_m, e_s = map(int, re.split('[:;]', raw_etime))
    e_h = e_h + 12 if cov_time else e_h  # 12小时制转到24小时制,默认是下午的现实时间
    video1, video_stime1, video_duration1 = _sub_split(indir, date, s_h, rt_dict, raw_stime, raw_etime,
                                                       cov_time=cov_time)
    video2, video_stime2, video_duration2 = _sub_split(indir, date, e_h, rt_dict, raw_stime, raw_etime,
                                                       cov_time=cov_time)
    random_name = randomString(5)
    odir = os.path.dirname(fname)
    tmp1 = os.path.join(odir, random_name + '_1.avi')
    tmp2 = os.path.join(odir, random_name + '_2.avi')
    cmd = split_cmd(infile=video1, ofile=tmp1, stime=video_stime1, duration=video_duration1) + ' ;'
    cmd += split_cmd(infile=video2, ofile=tmp2, stime=video_stime2, duration=video_duration2) + ' ;'
    from extra_utils.concat_video import concat_2
    cmd_concat = concat_2(tmp1, tmp2, fname)
    cmd += cmd_concat
    if not keep_intermediate:
        cmd += 'rm %s*' % os.path.join(odir, random_name + '*')
    return cmd


def split_video_single(indir, date, rt_dict, raw_stime, raw_etime, fname, cov_time=True):
    s_h, s_m, s_s = map(int, re.split('[:;]', raw_stime))
    s_h = s_h + 12 if cov_time else s_h  # 12小时制转到24小时制,默认是下午的现实时间

    video, video_stime, video_duration = _sub_split(indir, date, s_h, rt_dict, raw_stime, raw_etime, cov_time=cov_time)
    cmd = split_cmd(infile=video, ofile=fname, stime=video_stime, duration=video_duration)
    return cmd


def main(indir, odir, metadata, o_metadata, dry_run=False, keep_intermediate=False):
    """
    metadata主要是储存元数据,包括起始时间,rat ID,操作等 (这里的表头被写死,注意!!!!!) 例子可见example下的split_video.xlsx

    :param indir:
    :param odir:
    :param metadata:
    :param dry_run:
    :return:
    """
    rt_f = os.path.join(indir, 'all_rt.txt')
    rt_dict = parse_rt_f(rt_f)
    results, new_metadata = parse_metadata(metadata)
    for fname in tqdm(results.keys()):
        rat_id, date, action, raw_stime, raw_etime = map(str,results[fname])
        fname = os.path.join(odir, date, fname)
        os.makedirs(os.path.join(odir, date), exist_ok=True)

        s_h, s_m, s_s = map(int, re.split('[:;]', raw_stime))
        if s_h > 12:  # 由于混着用了12小时与24小时的输入方式。。。决定强制认为实验是晚上做的，所以这么写。。
            cov_time = False
        else:
            cov_time = True
        s_h = s_h + 12 if cov_time else s_h

        e_h, e_m, e_s = map(int, re.split('[:;]', raw_etime))
        e_h = e_h + 12 if cov_time else e_h
        if e_h != s_h and e_h > s_h:
            tqdm.write("Trans video detect, it may run in other ways. name is %s" % fname)
            cmd = split_video_trans(indir, date, rt_dict, raw_stime, raw_etime, fname, cov_time, keep_intermediate)
        else:
            cmd = split_video_single(indir, date, rt_dict, raw_stime, raw_etime, fname, cov_time)
        if dry_run:
            print(cmd)
        else:
            if os.path.isfile(fname):
                print("detect %s, pass it" % fname)
            else:
                check_call(cmd, shell=True)
    new_metadata.to_excel(o_metadata)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", '--input_dir', help="which directory you want to process",
                        type=str, )
    parser.add_argument("-o", "--output_dir",
                        help="The directory you want to save your project(could be non-exist)",
                        type=str)
    parser.add_argument("-m", "--metadata",
                        help="Metadata record the group info.",
                        type=str)
    args = parser.parse_args()
    indir = args.input_dir
    odir = args.output_dir
    metadata = args.metadata

    o_metadata = os.path.join(odir, str(os.path.basename(metadata).rpartition('.')[0]) + '_new.xlsx')
    # indir = '/home/liaoth/data2/project/VD/data2/raw'
    # odir = '/home/liaoth/data2/project/VD/data2/splitted'
    os.makedirs(odir, exist_ok=True)
    main(indir, odir, metadata, o_metadata, dry_run=False)
