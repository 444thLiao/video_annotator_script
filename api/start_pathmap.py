from AnyQt import QtCore
from tqdm import tqdm

from api.init_project_within_terminal import *


def unchecked_all(videos):
    for row in range(videos.count):
        # 从上往下依次选择视频,并uncheck该视频
        item = videos._form.listWidget.item(row)
        item.setCheckState(QtCore.Qt.Unchecked)


def start_video_pathmap(project_path):
    myapp.load_project(project_path)
    pathmap_window = myapp.pathmap_window
    # <pythonvideoannotator_module_tracking.tracking_window.TrackingWindow at 0x7fc321d60318>
    datasetsdialog = pathmap_window.datasets_dialog
    # pythonvideoannotator_models_gui.dialogs.datasets.datasets.DatasetsDialog

    datasetsselectordialog = datasetsdialog._panel.value  # 没有value就只是ControlEmptyWidget,而不是dialog的实例
    # pythonvideoannotator_models_gui.dialogs.datasets.datasets_selector.DatasetsSelectorDialog
    select_video = datasetsselectordialog._videos
    select_obj = datasetsselectordialog._objects
    select_datasets = datasetsselectordialog._datasets

    for row in tqdm(range(select_video.count)):
        unchecked_all(select_video)
        # 从上往下依次选择视频,并check该视频
        item = select_video._form.listWidget.item(row)
        item.setCheckState(QtCore.Qt.Checked)
        # 应该有多个object
        for obj_row in range(select_obj.count):
            item = select_obj._form.listWidget.item(obj_row)
            if 'object' in item.text():
                item.setCheckState(QtCore.Qt.Checked)
                break
        # 应该有两个datasets
        for ds_row in range(select_datasets.count):
            item = select_datasets._form.listWidget.item(ds_row)
            if 'contour' in item.text():
                item.setCheckState(QtCore.Qt.Checked)
        # 选择完上面的video obj dataset,该选择workflow和mask了
        radius = pathmap_window._radius
        # 获取filter window
        radius.value = 27
        # 开始执行
        pathmap_window.process()
        unchecked_all(select_video)
        unchecked_all(select_datasets)
        unchecked_all(select_obj)
        myapp.save_project(project_path)


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
        for dir in glob(os.path.join(indir, '*')):
            basename = os.path.basename(dir)
            if os.path.isdir(dir):
                print("recursively process each directory: %s" % basename)
                start_video_pathmap(dir)
    else:
        start_video_pathmap(dir)
