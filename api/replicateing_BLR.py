import os
import shutil
from collections import defaultdict
from glob import glob


def repr_target(f, targets):
    if os.path.isfile(f):
        val = eval(open(f, 'r').read())
        dir_name = os.path.basename(os.path.dirname(f))
        if val:
            if 'B' == dir_name:
                targets['For B'] = f
            if '_1' in f:
                targets['For 1'][dir_name] = f
            elif '_2' in f:
                targets['For 2'][dir_name] = f



def replace_with_targets(file_name, targets):
    B_geo = os.path.join(file_name, "objects", "B", "data.geo")
    L_geo = os.path.join(file_name, "objects", "L", "data.geo")
    R_geo = os.path.join(file_name, "objects", "R", "data.geo")
    ori_B = targets.get('For B','')
    ori_L_for1 = targets.get('For 1', {}).get('L','')
    ori_R_for1 = targets.get('For 1', {}).get('R', '')
    ori_L_for2 = targets.get('For 2', {}).get('L', '')
    ori_R_for2 = targets.get('For 2', {}).get('R', '')
    # if not targets['For B'] or not targets['For 1']['L'] or not targets['For 1']['R'] or \
    #     not targets['For 2']['L'] or not targets['For 2']['R']:
    #     import pdb;pdb.set_trace()
    #     raise Exception("Some repr_target doesn't detect")
    if ori_B != B_geo and ori_B:
        shutil.copy(ori_B, B_geo)
    if '_1' in file_name:
        if ori_L_for1 != L_geo and ori_L_for1:
            shutil.copy(ori_L_for1, L_geo)
        if ori_R_for1 != R_geo and ori_R_for1:
            shutil.copy(ori_R_for1, R_geo)
    elif '_2' in file_name:
        if ori_L_for2 != L_geo and ori_L_for2:
            shutil.copy(ori_L_for2, L_geo)
        if ori_R_for2 != R_geo and ori_R_for2:
            shutil.copy(ori_R_for2, R_geo)


def replicateing(indir):
    print("start replicateing B")
    targets = defaultdict(dict)
    for f in glob(os.path.join(indir, "videos", '*')):
        B_geo = os.path.join(f, "objects", "B", "data.geo")
        L_geo = os.path.join(f, "objects", "L", "data.geo")
        R_geo = os.path.join(f, "objects", "R", "data.geo")
        repr_target(B_geo, targets)
        repr_target(L_geo, targets)
        repr_target(R_geo, targets)
    # print(targets)
    # import pdb;pdb.set_trace()
    for f in glob(os.path.join(indir, "videos", '*')):
        replace_with_targets(f, targets)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", '--input_dir', help="which directory you want to process",
                        type=str, )
    parser.add_argument("-r", "--recursive",
                        help="recursive rename and move",
                        action="store_true")
    args = parser.parse_args()
    indir = os.path.abspath(args.input_dir)
    r = args.recursive
    if r:
        for dir in glob(os.path.join(indir,'*')):
            basename = os.path.basename(dir)
            if os.path.isdir(dir):
                print("recursively process each directory: %s" % basename)
                replicateing(dir)
    else:
        replicateing(indir)
