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
    pathmap_files = sorted(glob(os.path.join(indir, 'videos/*/objects/pathmap-1/pathmap-1.png')))
    B_files = sorted(glob(os.path.join(indir, 'videos/*/objects/B/data.geo')))
    L_files = sorted(glob(os.path.join(indir, 'videos/*/objects/L/data.geo')))
    R_files = sorted(glob(os.path.join(indir, 'videos/*/objects/R/data.geo')))
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    for pathmap, B, L, R in zip(pathmap_files,
                                B_files,
                                L_files,
                                R_files):
        B = open(B, 'r').read()
        B = eval('%s' % B, )
        L = open(L, 'r').read()
        L = eval('%s' % L, )
        R = open(R, 'r').read()
        R = eval('%s' % R, )
        img = add_geometry(pathmap, B, color=(0, 0, 255))
        img = add_geometry(img, L, color=(0, 0, 255))
        img = add_geometry(img, R, color=(0, 0, 255))

        filename = re.findall('videos/(.*)/objects', pathmap)[0]
        cv2.imwrite(os.path.join(outdir, filename + '.png'),
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
    indir = '/home/liaoth/project/VD/data/video/aft_med/3MIN'
    indir2 = '/home/liaoth/project/VD/data/video/aft_model/3MIN'
    outdir = '/home/liaoth/project/VD/data/pathmap/aft_med'
    outdir2 = '/home/liaoth/project/VD/data/pathmap/aft_model'

    iter_doc(indir, outdir)
    iter_doc(indir2, outdir2)
