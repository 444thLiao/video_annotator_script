"""
For Python Video Annotator

"""
from confapp import conf

conf += 'pythonvideoannotator.settings'
from pythonvideoannotator_models_gui.models.project_gui import ProjectGUI
from pythonvideoannotator.base_module import BaseModule
from pyforms_gui.appmanager import StandAloneContainer
from AnyQt.QtWidgets import QApplication

import sys

VideoAnnotator = type(
    'VideoAnnotator',
    tuple(conf.MODULES.find_class('module.Module') + [BaseModule]),
    {}
)

Project = type(
    'Project',
    tuple(conf.MODULES.find_class('models.Project') + [ProjectGUI]),
    {}
)

app = QApplication(sys.argv)
conf += 'pyforms_gui.settings'
mainwindow = StandAloneContainer(VideoAnnotator)

myapp = mainwindow.centralWidget()

############################################################
project = myapp._project

# mainwindow.showMaximized()
# app.exec_()

from glob import glob
import os


def load_videos(indir):
    for avi in glob(os.path.join(indir, '*.avi')):
        video = project.create_video()
        video._file.value = avi
        n_geo = 1 if '_A' in avi else 3
        name_geo = ['B'] if '_A' in avi else ['B', 'L', 'R']
        for _ in range(n_geo):
            geo = video.create_geometry()
            geo.name = name_geo[_]
        obj = video.create_object()
        p = obj.create_path()
        c = obj.create_contours()


if __name__ == '__main__':
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

    # indir = "/home/liaoth/data2/project/VD/data2/splitted/20190409"
    # odir = '/home/liaoth/Desktop/test2'
    overwrite = False

    if r:
        for dir in glob(os.path.join(indir,'*')):
            basename = os.path.basename(dir)
            print("recursively process each directory: %s" % basename)
            if os.path.isdir(dir):
                new_odir = os.path.join(odir,basename)
                if not os.path.isdir(odir) or overwrite:
                    load_videos(dir)
                    myapp.save_project(new_odir)
                    if overwrite:
                        print('overwritting it.')
    else:
        if not os.path.isdir(odir) or overwrite:
            load_videos(indir)
            myapp.save_project(odir)
            if overwrite:
                print('overwritting it.')
