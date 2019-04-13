import os
import shutil
from collections import defaultdict
from glob import glob


def repr_target(f, targets):
    if os.path.isfile(f):
        val = eval(open(f, 'r').read())
        if val:
            if '/B/' in f:
                targets['For B'] = f
            if '_1' in f:
                if '/L/' in f:
                    targets['For 1']['L'] = f
                if '/R/' in f:
                    targets['For 1']['R'] = f
            elif '_2' in f:
                if '/L/' in f:
                    targets['For 2']['L'] = f
                if '/R/' in f:
                    targets['For 2']['R'] = f


def replace_with_targets(file_name, targets):
    B_geo = os.path.join(file_name, "objects", "B", "data.geo")
    L_geo = os.path.join(file_name, "objects", "L", "data.geo")
    R_geo = os.path.join(file_name, "objects", "R", "data.geo")
    if not targets['For B'] or not targets['For 1']['L'] or not targets['For 1']['R'] or \
        not targets['For 2']['L'] or not targets['For 2']['R']:
        raise Exception("Some repr_target doesn't detect")
    if targets['For B'] != B_geo:
        shutil.copy(targets['For B'], B_geo)
    if '_1' in file_name:
        if targets['For 1']['L'] != L_geo:
            shutil.copy(targets['For 1']['L'], L_geo)
        if targets['For 1']['R'] != R_geo:
            shutil.copy(targets['For 1']['R'], R_geo)
    elif '_2' in file_name:
        if targets['For 2']['L'] != L_geo:
            shutil.copy(targets['For 2']['L'], L_geo)
        if targets['For 2']['R'] != R_geo:
            shutil.copy(targets['For 2']['R'], R_geo)


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

    args = parser.parse_args()
    indir = args.input_dir

    replicateing(indir)
