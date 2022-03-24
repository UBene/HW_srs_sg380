"""
Created on Mar 17, 2022

@author: bened
"""
from ScopeFoundry.logged_quantity import LQCollection
import numpy as np
from qtpy import QtWidgets
from ScopeFoundry.widgets import DataSelector
from qtpy import QtCore
import pyqtgraph as pg

import pyqtgraph.dockarea as dockarea


class HyperSpecDataManager:
    def __init__(
        self,
        signal_selector: DataSelector = None,
        bg_selector: DataSelector = None,
        spec_axis=-1,
    ):

        self.bg_selector = bg_selector
        self.signal_selector = signal_selector
        self.spec_axis = spec_axis
        self.ready = False

        self.settings = LQCollection()
        self.settings.New("x_axis", str, choices=("pixels",), initial="pixels")

        dummy_data = 0.5 * np.random.random(512 * 21 * 21).reshape((21, 21, 512))
        self.set_data(dummy_data)

    def add_x_axis_array(self, name: str, x: np.ndarray):
        self.xs[name] = x
        self.settings.x_axis.add_choices([name])

    def set_data(self, data: np.ndarray):
        self._data = data
        if not hasattr(self, "xs") or self._data.shape[-1] != self.xs["pixels"]:
            self.xs = {"pixels": self._data.shape[-1]}
            self.settings.x_axis.change_choice_list(["pixels"])

    def get_bg(self):
        if not self.bg_selector:
            return 0
        if self.bg_selector.activated.val:
            return self.bg_selector.select(self._data, self.spec_axis).mean()
        else:
            return 0

    def get_signal_data(self):
        if self.signal_selector:
            return self.signal_selector.select(self._data, self.spec_axis)
        else:
            return self._data

    def get_data(self, select=True):
        if not select:
            return self._data
        return self.get_signal_data() - self.get_bg()

    def get_x(self, select=True):
        if not select:
            return self.xs[self.settings["x_axis"]]
        return self.signal_selector.select(self.xs[self.settings["x_axis"]], 0)

    def new_widget(self):
        return self.settings.New_UI()


class ImageManager(QtCore.QObject):

    images_updated = QtCore.Signal()

    def __init__(self, data_manager: HyperSpecDataManager):
        super().__init__()
        self.data_manager = data_manager
        S = self.settings = LQCollection()
        S.New("image", str, choices=("sum",))
        self.reset()

    def reset(self):
        self.images = {}

    def fit_map(self):
        x = self.data_manager.get_x()
        hyperspec = self.data_manager.get_data()
        keys, images = self.plot_n_fit.fit_hyperspec(x, hyperspec)
        if len(keys) == 1:
            self.add_display_image(keys[0], images)
        else:
            for key, image in zip(keys, images):
                self.add_display_image(key, image)

    def calc_media_map(self):
        hyperspec_data = self.data_manager.get_data()
        x = self.data_manager.get_x()
        median_map = spectral_median_map(hyperspec_data, x)
        self.add_display_image("median_map", median_map)

    def calc_sum_image(self):
        image = self.data_manager.get_data().sum(axis=-1)
        self.add_display_image("sum", image)

    def add_display_image(self, key, image):
        key = self.add_descriptor_suffixes(key)
        self.images[key] = image
        self.settings.image.add_choices(key, allow_duplicates=False)
        self.images_updated.emit()

    def add_descriptor_suffixes(self, key):
        ss = self.data_manager.signal_selector
        bg = self.data_manager.bg_selector
        if ss.activated.val:
            key += f"_x{ss.start.val}-{ss.stop.val}"
        if bg.activated.val:
            key += f"_bg{bg.start.val}-{bg.stop.val}"
        return key

    def delete_current_display_image(self):
        key = self.settings.image.val
        del self.display_images[key]
        self.settings.image.remove_choices(key)
        self.images_updated.emit()

    def get_current_image(self):
        if self.settings["image"] in self.images:
            return self.images[self.settings["image"]]
        else:
            return np.random.rand(3, 3)

    def new_layout(self):
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.settings.New_UI())

        self.calc_median_pushButton = QtWidgets.QPushButton(text="recalc median map")
        self.calc_median_pushButton.clicked.connect(self.calc_media_map)
        self.calc_sum_pushButton = QtWidgets.QPushButton(text="recalc sum map")
        self.calc_sum_pushButton.clicked.connect(self.calc_sum_image)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.calc_median_pushButton)
        button_layout.addWidget(self.calc_sum_pushButton)
        layout.addLayout(button_layout)

        return layout


class Correlator:
    def __init__(self, image_manager: ImageManager):
        S = self.settings = LQCollection()
        S.New("X", str, choices=("sum",), initial="sum")
        S.New("Y", str, choices=("sum",), initial="sum")

        self.image_manager = image_manager
        self.image_manager.images_updated.connect(self.on_images_updated)

    def add_listener(self, func, argtype=(), **kwargs):
        self.settings.X.add_listener(func, argtype=(), **kwargs)
        self.settings.Y.add_listener(func, argtype=(), **kwargs)

    def reset(self):
        choices = list(self.image_manager.images.keys())
        self.settings.X.change_choice_list(choices)
        self.settings.Y.change_choice_list(choices)

    def on_images_updated(self):
        choices = list(self.image_manager.images.keys())
        self.settings.X.change_choice_list(choices)
        self.settings.Y.change_choice_list(choices)
        self.settings.Y.update_value(choices[-1])

    @property
    def x_image(self):
        S = self.settings
        if S["X"] in self.image_manager.images:
            return self.image_manager.images[S["X"]]

    @property
    def y_image(self):
        S = self.settings
        if S["Y"] in self.image_manager.images:
            return self.image_manager.images[S["Y"]]

    @property
    def x(self):
        return np.flat(self.x_image)

    @property
    def y(self):
        return np.flat(self.y_image)

    # guis
    def new_dock(self):
        return dockarea.Dock(name="correlator", widget=self.new_widget())

    def new_widget(self):
        self.graph_widget = pg.GraphicsLayoutWidget()
        self.plot = self.graph_widget.addPlot()
        self.data_line = pg.PlotDataItem(
            x=[0, 1, 2, 3, 4],
            y=[0, 2, 1, 3, 2],
            size=17,
            pen=pg.mkPen(None),
            symbol="o",
            symbolBrush=pg.mkBrush(255, 255, 255, 30),
            symbolPen=pg.mkPen(None),
        )
        self.target = pg.TargetItem(movable=False)
        self.highlight_data_line = pg.PlotDataItem(
            x=[0, 1, 2, 3, 4],
            y=[0, 2, 1, 3, 2],
            size=17,
            pen=pg.mkPen(None),
            symbol="o",
            symbolBrush=pg.mkBrush(255, 255, 255, 60),
            symbolPen=pg.mkPen(255, 255, 255),
        )
        self.plot.addItem(self.data_line)
        self.plot.addItem(self.target, pen="r", size=40)
        self.plot.addItem(self.highlight_data_line)

        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.addWidget(self.graph_widget)
        layout.addWidget(self.settings.New_UI())
        return widget


def spectral_median(spec, wls):
    int_spec = np.cumsum(spec)
    total_sum = int_spec[-1]
    return wls[int_spec.searchsorted(0.5 * total_sum)]


def spectral_median_map(hyperspectral_data, wls):
    return np.apply_along_axis(spectral_median, -1, hyperspectral_data, wls=wls)


def norm(x):
    x_max = x.max()
    if x_max == 0:
        return x * 0.0
    else:
        return x * 1.0 / x_max


def norm_map(map_):
    return np.apply_along_axis(norm, -1, map_)
