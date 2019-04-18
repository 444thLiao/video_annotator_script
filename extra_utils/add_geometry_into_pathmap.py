import os
import re
from glob import glob

import cv2

"""
在生成pathmap后使用,通过之前标记的border从而 广播(broadcast)到对应pathmap上
"""


def iter_doc(indir, outdir):
    """
    pythonvideoannotator的固定输出格式
    注意pathmap-1应该有且只有-1的名称
    :param indir:
    :param outdir:
    :return:
    """
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    for pathmap in sorted(glob(os.path.join(indir, 'videos/*/objects/pathmap-1/*.png'))):
        sid = re.findall('videos/(.*)/objects', pathmap)[0]
        img = cv2.imread(pathmap)
        if '_A' in sid:
            iter_objs = ['B']
        elif '_1' in sid or '_2' in sid:
            iter_objs = ['B', 'L', 'R']
        else:
            raise Exception
        for obj in iter_objs:
            geo = os.path.join(indir, 'videos/%s/objects/%s/data.geo' % (sid, obj))
            val_cmd = open(geo, 'r').read()
            val = eval(val_cmd)
            img = add_geometry(img, val, color=border_color)

        cv2.imwrite(os.path.join(outdir, sid + '.png'),
                    img)


def add_geometry(img, shape_ord, color=(0, 0, 0)):
    if type(img) == str:
        img = cv2.imread(img)

    shape = shape_ord[0][1]
    start_point = shape[0]
    for s, e in zip(shape, shape[1:] + [start_point]):
        cv2.line(img, tuple(s), tuple(e), color, 2)
    return img


if __name__ == '__main__':
    border_color = (0, 0, 255)
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", '--input_dir', help="which directory you want to process",
                        type=str, )
    parser.add_argument("-o", "--output_dir",
                        help="The directory you want to save your project(could be non-exist)",
                        type=str)
    parser.add_argument("-r", "--recursive",
                        help="recursive rename and move",
                        action="store_true")
    args = parser.parse_args()
    indir = args.input_dir
    odir = args.output_dir
    r = args.recursive

    if r:
        for dir in glob(os.path.join(indir, '*')):
            basename = os.path.basename(dir)
            print("recursively process each directory: %s" % basename)
            new_odir = os.path.join(odir, basename)
            iter_doc(dir, new_odir)
    else:
        iter_doc(indir, odir)
