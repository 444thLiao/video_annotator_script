from AnyQt import QtCore
from tqdm import tqdm

from init_project_within_terminal import *


def unchecked_all(videos):
    for row in range(videos.count):
        # 从上往下依次选择视频,并uncheck该视频
        item = videos._form.listWidget.item(row)
        item.setCheckState(QtCore.Qt.Unchecked)


def start_video_tracking(project_path):
    myapp.load_project(project_path)
    tracking_window = myapp.tracking_window
    # <pythonvideoannotator_module_tracking.tracking_window.TrackingWindow at 0x7fc321d60318>
    datasetsdialog = tracking_window.input_dialog
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
        # 应该只有1个object
        item = select_obj._form.listWidget.item(0)
        item.setCheckState(QtCore.Qt.Checked)
        # 应该有两个datasets
        for ds_row in range(select_datasets.count):
            item = select_datasets._form.listWidget.item(ds_row)
            item.setCheckState(QtCore.Qt.Checked)
        # 选择完上面的video obj dataset,该选择workflow和mask了
        filter_window = tracking_window._filter
        # 获取filter window
        tracking_window._filter._imageflows.value = 'Adaptative threshold + mask'
        # 设置imageflow 到 该workflow  (validate by tracking_window._filter._imgfilters.value)
        imgfilter = tracking_window._filter._imgfilters.value
        # 获取新的image filter 窗口
        threshold_panel = imgfilter[0][1]
        mask_panel = imgfilter[-1][1]
        # 两个主要panel
        threshold_panel._field_adaptive_threshold_block_size.value = 1300
        threshold_panel._field_adaptive_threshold_c.value = 200
        # 调整两个参数
        video_select_panel = mask_panel._panel.value._videos
        geo_select_panel = mask_panel._panel.value._objects
        item = video_select_panel._form.listWidget.item(row)
        item.setCheckState(QtCore.Qt.Checked)
        # 选中与row相同的一个video
        for i in range(geo_select_panel.count):
            item = geo_select_panel._form.listWidget.item(i)
            if item.text() == 'B':  # 如果是B,才选中
                item.setCheckState(QtCore.Qt.Checked)
        # 选择obj中B,即边界,然后结束.
        # 开始执行
        tracking_window.process()
        unchecked_all(video_select_panel)
    myapp.save_project(project_path)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", '--input_dir', help="which directory you want to process",
                        type=str, )
    args = parser.parse_args()
    indir = args.input_dir

    start_video_tracking(indir)
