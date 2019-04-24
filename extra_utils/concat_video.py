import os
from glob import glob
from subprocess import check_call

from tqdm import tqdm
import time

def concat_2(v1, v2, oname):
    """
    合并video1,video2 到oname
    :param v1:
    :param v2:
    :param oname:
    :return:
    """
    cmd = "/usr/bin/ffmpeg -i {infile} -qscale:v 1 -r 20 {ofile} -loglevel -8 ; ".format(infile=v1,
                                                                                         ofile=v1.rpartition('.')[
                                                                                                   0] + '.mpg')
    cmd += "/usr/bin/ffmpeg -i {infile} -qscale:v 1 -r 20 {ofile} -loglevel -8 ; ".format(infile=v2,
                                                                                          ofile=v2.rpartition('.')[
                                                                                                    0] + '.mpg')
    cmd += "cat %s %s > %s ; " % (v1.rpartition('.')[0] + '.mpg',
                                  v2.rpartition('.')[0] + '.mpg',
                                  "/tmp/tmp.mpg")
    cmd += "/usr/bin/ffmpeg -i {infile} -qscale:v 2 {ofile} -loglevel -8 ; ".format(infile="/tmp/tmp.mpg",
                                                                                    ofile=oname)
    return cmd


def concat_video(indir, odir, recursive=True):
    """
    合并视频,根据现有的录像机的格式进行合并. 使用ffmpeg进行合并.
    现有录像机的格式: 在indir下,有多个以yyyymmddhh命名的文件夹,每个文件夹下具有多个类似24M24S_1554726264命名的文件,每个长度最长为1min,

    该函数以小时为最小单位合并视频. (考虑到小时之间不一定连续,所以不合并为一整个视频文件.)
    该函数将视频inplace 转化为mpg,一方面进行规整格式,一方面便于合并
    合并后为一整个mpg,然后再进行格式转化为avi
    并以文件夹的名称,即yyyymmddhh为之命名.
    最后输出到odir下, 名称为yyyymmddhh.avi

    :param indir:
    :param odir:
    :param recursive:
    :return:
    """
    ori_suffix = '.mp4'
    intermediate_suffix = '.mpg'
    final_suffix = '.avi'
    rt_text = ''
    rt_file = os.path.join(odir, 'all_rt.txt')
    if recursive:
        all_videos = glob(os.path.join(indir, '**', '*' + ori_suffix))
        if not all_videos:
            raise Exception
        all_dirs = set([os.path.dirname(v) for v in all_videos])
        for dir_path in all_dirs:
            date = os.path.basename(dir_path)  # 提取文件夹的名称
            final_file = os.path.join(odir, str(date) + final_suffix)

            sub_video_files = glob(os.path.join(dir_path, '*' + ori_suffix))
            sub_video_min = [int(os.path.basename(_).split('M')[0]) for _ in sub_video_files]

            sorted_files = sorted(zip(sub_video_min,
                                      sub_video_files))
            first_time_stamp = int(str(os.path.basename(sorted_files[0][1])).replace(ori_suffix,'').split('_')[1])
            rt_text += "%s\t%s\n" % (time.strftime("%Y%m%d%H.avi", time.localtime(first_time_stamp)),
                                     time.strftime("%H:%M:%S;0", time.localtime(first_time_stamp)))
            if os.path.isfile(final_file):
                print("Detect final file %s" % final_file, 'pass it')
                continue
            for min, video_file in tqdm(sorted_files):
                cmd = "/usr/bin/ffmpeg -i {infile} -qscale:v 1 -r 20 {ofile} -loglevel -8".format(infile=video_file,
                                                                                                  ofile=video_file.replace(
                                                                                                      ori_suffix,
                                                                                                      intermediate_suffix))
                # print(cmd)
                if not os.path.isfile(video_file.replace(ori_suffix, intermediate_suffix)):
                    check_call(cmd, shell=True)
            print("itering all files and formatted it.")
            cmd2 = "cat %s > %s" % (
                ' '.join([video_file.replace(ori_suffix, intermediate_suffix) for min, video_file in sorted_files]),
                final_file.replace(final_suffix,
                                   intermediate_suffix))
            # print(cmd2)
            if not os.path.isfile(final_file.replace(final_suffix,
                                                     intermediate_suffix)):
                os.system(cmd2)
            print("Concat all formatted files")
            cmd3 = "/usr/bin/ffmpeg -i {infile} -qscale:v 2 {ofile} -loglevel -8; rm {infile}".format(
                infile=final_file.replace(final_suffix,
                                          intermediate_suffix),
                ofile=final_file)
            # print(cmd3)
            check_call(cmd3, shell=True)
            print("Transform the file into avi file.\n Get %s" % final_file)
    with open(rt_file,"w") as f1:
        f1.write(rt_text)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", '--input_dir', help="which directory you want to process",
                        type=str, )
    parser.add_argument("-o", "--output_dir",
                        help="The directory you want to save your project(could be non-exist)",
                        type=str)

    args = parser.parse_args()
    indir = os.path.abspath(args.input_dir)
    odir = os.path.abspath(args.output_dir)
    os.makedirs(odir, exist_ok=True)

    # indir = '/home/liaoth/data2/project/VD/data2/raw'
    # odir = '/home/liaoth/data2/project/VD/data2/raw'

    concat_video(indir, odir)
