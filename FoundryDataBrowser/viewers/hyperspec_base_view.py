"""
reworked on March, 2022

@author: Benedikt Ursprung
"""
import os
import time
from datetime import datetime
import h5py
from scipy.stats import spearmanr
import numpy as np
from qtpy import QtCore, QtWidgets
import pyqtgraph as pg
import pyqtgraph.dockarea as dockarea
import traceback


from ScopeFoundry.data_browser import DataBrowserView
from FoundryDataBrowser.viewers.plot_n_fit import PlotNFit
from FoundryDataBrowser.viewers.scalebars import ConfocalScaleBar
from ScopeFoundry.widgets import DataSelector
from ScopeFoundry.helper_funcs import sibling_path
from FoundryDataBrowser.viewers.map_exporter import MapExporter
from FoundryDataBrowser.viewers.image_processor import (
    HyperSpecDataManager,
    ImageManager,
    Correlator,
)


class HyperSpectralBaseView(DataBrowserView):

    name = "HyperSpectralBaseView"

    def setup(self):

        self.data_loaded = False

        self.plot_n_fit = PlotNFit(Ndata_lines=2)
        self.bg_selector = DataSelector(name="background", initials=[0, 10, 1])
        self.signal_selector = self.plot_n_fit.data_selector

        self.data_manager = HyperSpecDataManager(self.signal_selector, self.bg_selector)

        self.image_manager = ImageManager(self.data_manager)

        self.correlator = Correlator(self.image_manager)
        self.exporter = MapExporter(self.image_manager)

        # Docks
        self.ui = self.dockarea = dockarea.DockArea()
        self.image_dock = self.dockarea.addDock(name="Image")
        self.spec_dock = self.dockarea.addDock(self.plot_n_fit.ui.graph_dock)
        self.settings_dock = self.dockarea.addDock(
            name="settings", position="left", relativeTo=self.image_dock
        )
        self.export_dock = self.dockarea.addDock(
            self.exporter.new_dock(), position="below", relativeTo=self.settings_dock,
        )
        self.dockarea.addDock(
            self.plot_n_fit.ui.settings_dock,
            name="plot_and_fit settings",
            relativeTo=self.settings_dock,
            position="below",
        )
        self.correlator_dock = self.correlator.new_dock()
        self.corr_dock = self.dockarea.addDock(
            self.correlator_dock, position="right", relativeTo=self.spec_dock
        )

        # Image View
        self.imview = pg.ImageView()
        self.imview.getView().invertY(False)  # lower left origin
        self.image_dock.addWidget(self.imview)

        # Rectangle ROI
        self.rect_roi = pg.RectROI([20, 20], [20, 20], pen="w")
        self.rect_roi.addTranslateHandle((0.5, 0.5))
        self.imview.getView().addItem(self.rect_roi)
        self.rect_roi.sigRegionChanged[object].connect(self.on_change_rect_roi)

        # Point ROI
        self.circ_roi = pg.CircleROI((0, 0), (2, 2), movable=True, pen="r")
        # self.circ_roi.removeHandle(self.circ_roi.getHandles()[0])
        h = self.circ_roi.addTranslateHandle((0.5, 0.5))
        h.pen = pg.mkPen(pen="r")
        h.update()
        self.imview.getView().addItem(self.circ_roi)
        self.circ_roi.removeHandle(0)
        self.circ_roi_plotline = pg.PlotCurveItem([0], pen="r")
        self.imview.getView().addItem(self.circ_roi_plotline)
        self.circ_roi.sigRegionChanged[object].connect(self.on_update_circ_roi)

        # Spec plot
        self.spec_plot = self.plot_n_fit.ui.plot
        self.spec_plot.setLabel("left", "Intensity", units="counts")
        self.rect_plotdata = self.plot_n_fit.ui.data_lines[0]
        self.point_plotdata = self.plot_n_fit.ui.data_lines[1]
        self.point_plotdata.setZValue(-1)

        self.image_manager.settings.image.add_listener(self.update_display)

        S = self.settings

        self.norm_data = S.New("norm_data", bool, initial=False)
        self.norm_data.add_listener(self.update_display)

        self.binning = S.New("binning", int, initial=1, vmin=1)
        self.binning.add_listener(self.update_binning)

        self.spatial_binning = S.New("spatial_binning", int, initial=1, vmin=1)
        self.spatial_binning.add_listener(self.update_binning)

        self._load_dummy_data()  # load some dummy data

        S.New("show_circ_line", bool, initial=True)
        S.New("show_rect_line", bool, initial=True)
        self.settings.show_circ_line.updated_value[bool].connect(
            self.point_plotdata.setVisible
        )
        self.settings.show_rect_line.updated_value[bool].connect(
            self.rect_plotdata.setVisible
        )

        # state
        self.save_state_pushButton = QtWidgets.QPushButton(text="save state")
        self.export_dock.addWidget(self.save_state_pushButton)
        self.save_state_pushButton.clicked.connect(self.save_state)

        # finalize settings widgets
        self.scan_specific_setup()  # there could more settings_widgets generated here (part 2/2)

        hide_settings = [
            "norm_data",
            "show_circ_line",
            "show_rect_line",
            "spatial_binning",
        ]
        self.settings_ui = self.settings.New_UI(exclude=hide_settings)
        self.settings_dock.addWidget(self.settings_ui)
        self.settings_dock.addWidget(self.bg_selector.New_UI())
        self.settings_dock.addWidget(self.signal_selector.New_UI())

        self.bg_selector.set_plot_data_item(self.rect_plotdata)

        self.hidden_settings_ui = self.settings.New_UI(include=hide_settings)
        self.export_dock.addWidget(self.hidden_settings_ui)

        self.settings_dock.addWidget(self.new_settings_widget())

        self.plot_n_fit.ui.add_button("fit_map", self.image_manager.fit_map)
        self.plot_n_fit.ui.graph_dock.addWidget(
            self.data_manager.settings.x_axis.new_default_widget()
        )

        self.settings_dock.raiseDock()

        self.settings_dock.setStretch(1, 1)
        self.export_dock.setStretch(1, 1)
        self.settings_dock.setStretch(1, 1)

        for layout in [
            self.settings_ui.layout(),
            self.export_dock.layout,
        ]:
            VSpacerItem = QtWidgets.QSpacerItem(
                0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
            )
            layout.addItem(VSpacerItem)

        self.correlator.add_listener(self.on_change_corr_settings)


        self.circ_roi_ji = (0, 0)

    def _new_data_loaded(self):
        self.image_manager.reset()
        self.correlator.reset()
        self.image_manager.calc_media_map()
        self.image_manager.calc_sum_image()

    # gui
    def new_settings_widget(self):
        self.update_display_pushButton = QtWidgets.QPushButton(text="update display")
        self.update_display_pushButton.clicked.connect(self.update_display)
        self.default_view_pushButton = QtWidgets.QPushButton(text="default img view")
        self.default_view_pushButton.clicked.connect(self.default_image_view)

        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.addLayout(self.image_manager.new_layout())
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.update_display_pushButton)
        hlayout.addWidget(self.default_view_pushButton)
        layout.addLayout(hlayout)
        return widget

    def get_spec_average(self, ji_slice: (slice, slice), select_spec: bool = True):
        """
        returns processed hyperspec_data averaged over a given spatial slice.
        
        *ji_slice:      spatial slice
        *full_spec:     True: do not apply data selectors 
                
        """
        x = self.data_manager.get_x(select_spec)
        y = self.data_manager.get_data(select_spec)[ji_slice].mean(axis=(0, 1))
        if self.settings["norm_data"]:
            y = norm(y)
        return (x, y)

    def scan_specific_setup(self):
        # add settings and export_settings. Append widgets to self.settings_widgets and self.export_widgets
        pass

    def is_file_supported(self, fname):
        # override this!
        return False

    def post_load(self):
        # override this!
        pass

    def on_change_data_filename(self, fname):
        self.data_loaded = False
        if fname == "0":
            return
        try:
            self.scalebar_type = None
            self.load_data(fname)
            self.update_binning()  # also sets data
        except Exception as err:
            HyperSpectralBaseView.load_data(self, fname)
            self.databrowser.ui.statusbar.showMessage(
                "failed to load {}: {}".format(fname, err)
            )
            raise (err)
        finally:
            self._new_data_loaded()
            self.databrowser.ui.statusbar.clearMessage()
            self.post_load()
            #self.add_scalebar()
            #self.on_change_display_image()
            #self.on_change_corr_settings()
            self.update_display()
        #self.on_change_x_axis()

        #if self.settings["default_view_on_load"]:
        self.default_image_view()

    def add_scalebar(self):
        """ not intended to use: Call set_scalebar_params() during load_data()"""

        if hasattr(self, "scalebar"):
            try:
                self.imview.getView().removeItem(self.scalebar)
                del self.scalebar
            except AttributeError:
                pass

        num_px = self.image_manager.get_current_image().shape[1]  # horizontal dimension!
        
        
        if self.scalebar_type == None:
            # matplotlib export
            self.unit_per_px = 1
            self.exporter.settings["scale_bar_width"] = int(num_px / 4)
            self.exporter.settings["scale_bar_text"] = "{} pixels".format(
                int(num_px / 4)
            )

        if self.scalebar_type != None:
            kwargs = self.scalebar_kwargs

            span = self.scalebar_kwargs[
                "span"
            ]  # this is in meter! convert to according to its magnitude
            w_meter = span / 4
            mag = int(np.log10(w_meter))
            conv_fac, unit = {
                0: (1, "m"),
                -1: (1e2, "cm"),
                -2: (1e3, "mm"),
                -3: (1e3, "mm"),
                -4: (1e6, "\u03bcm"),
                -5: (1e6, "\u03bcm"),
                -6: (1e6, "\u03bcm"),  # \mu
                -7: (1e9, "nm"),
                -8: (1e9, "nm"),
                -9: (1e9, "nm"),
                -10: (1e10, "\u212b"),
                -11: (1e12, "pm"),
                -12: (1e12, "pm"),
            }[mag]

            # matplotlib export
            self.unit_per_px = span * conv_fac / num_px
            self.exporter.settings["scale_bar_width"] = int(w_meter * conv_fac)
            self.exporter.settings[
                "scale_bar_text"
            ] = f"{int(w_meter * conv_fac)} {(unit)}"

        if self.scalebar_type == "ConfocalScaleBar":
            self.scalebar = ConfocalScaleBar(num_px=num_px, **kwargs)
            self.scalebar.setParentItem(self.imview.getView())
            self.scalebar.anchor((1, 1), (1, 1), offset=kwargs["offset"])

        elif self.scalebar_type == None:
            self.scalebar = None

    def set_scalebar_params(
        self,
        h_span,
        units="m",
        scalebar_type="ConfocalScaleBar",
        stroke_width=10,
        brush="w",
        pen="k",
        offset=(-20, -20),
    ):
        """
        call this function during load_data() to add a scalebar!
        *h_span*  horizontal length of image in units of *units* if positive.
                  Else, scalebar is in units of pixels (*units* ignored).
        *units*   SI length unit of *h_span*.
        *scalebar_type* is either `None` (no scalebar will be added)
          or `"ConfocalScaleBar"` (default).
        *stroke_width*, *brush*, *pen* and *offset* affect appearance and 
         positioning of the scalebar.
        """
        assert scalebar_type in [None, "ConfocalScaleBar"]
        self.scalebar_type = scalebar_type
        span_meter = {
            "m": 1,
            "cm": 1e-2,
            "mm": 1e-3,
            "um": 1e-6,
            "nm": 1e-9,
            "pm": 1e-12,
            "fm": 1e-15,
        }[units] * h_span
        self.scalebar_kwargs = {
            "span": span_meter,
            "brush": brush,
            "pen": pen,
            "width": stroke_width,
            "offset": offset,
        }

    @QtCore.Slot()
    def update_display(self):
        self.update_display_image()
        self.on_change_rect_roi()
        self.on_update_circ_roi()

    def update_display_image(self):
        image = self.image_manager.get_current_image()
        self.imview.setImage(image)

    def load_data(self, fname):
        """
        override to set hyperspec_data and x_arrays such as wavelengths
        
        self.hyperspec_data = data 
            where data is of shape Ny, Nx, Nspec
        self.x_arrays = dict('wls'=np.ndarray(Nspec))     
        """

    def _load_dummy_data(self):
        data = np.arange(10 * 10 * 34).reshape((10, 10, 34))
        self.hyperspec_data = data
        self.x_arrays = dict(wls=np.arange(34) / 2.3)
        self.update_binning()

    def set_data_manager(self, data, x_arrays=None):
        self.data_manager.set_data(data)
        for name, x in x_arrays.items():
            self.data_manager.add_x_axis_array(name, x)
        self._new_data_loaded()
        self.data_loaded = True
        self.update_display()
        self.default_image_view()

    @QtCore.Slot(object)
    def on_change_rect_roi(self, roi=None):
        # pyqtgraph axes are (x,y), but hyperspec is in (y,x,spec) hence axes=(1,0)
        roi_slice, roi_tr = self.rect_roi.getArraySlice(
            self.data_manager._data, self.imview.getImageItem(), axes=(1, 0)
        )
        self.rect_roi_slice = roi_slice
        x, y = self.get_spec_average(self.rect_roi_slice, True)
        self.plot_n_fit.set_data(x, y, 0, True)
        self.on_change_corr_settings()

    @QtCore.Slot(object)
    def on_update_circ_roi(self, roi=None):
        if roi is None:
            roi = self.circ_roi

        roi_state = roi.saveState()
        x0, y0 = roi_state["pos"]
        xc = x0 + 1
        yc = y0 + 1

        Ny, Nx, _ = self.data_manager._data.shape

        i = max(0, min(int(xc), Nx - 1))
        j = max(0, min(int(yc), Ny - 1))

        self.circ_roi_plotline.setData([xc, i + 0.5], [yc, j + 0.5])

        self.circ_roi_ji = (j, i)
        self.circ_roi_slice = np.s_[j : j + 1, i : i + 1]

        x, y = self.get_spec_average(self.circ_roi_slice, True)
        self.plot_n_fit.set_data(x, y, 1, False)
        self.plot_n_fit.update()
        self.on_change_corr_settings()

    def default_image_view(self):
        "sets rect_roi congruent to imageItem and optimizes size of imageItem to fit the ViewBox"
        iI = self.imview.imageItem
        h, w = iI.height(), iI.width()
        self.rect_roi.setSize((w, h))
        self.rect_roi.setPos((0, 0))
        self.imview.getView().enableAutoRange()
        self.spec_plot.enableAutoRange()

    def on_change_corr_settings(self):
        try:
            X = self.correlator.x_image
            Y = self.correlator.y_image

            if not type(X) == np.ndarray:
                return

            self.correlator.data_line.setData(x=X.flat, y=Y.flat)

            # mark points within rect_roi
            mask = np.zeros_like(X, dtype=bool)
            mask[self.rect_roi_slice[0:2]] = True
            cor_x = X[mask].flatten()
            cor_y = Y[mask].flatten()
            self.correlator.highlight_data_line.setData(
                cor_x, cor_y, brush=pg.mkBrush(255, 255, 255, 100), pen=None,
            )
            # mark circ_roi point
            j, i = self.circ_roi_ji
            x_circ, y_circ = np.atleast_1d(X[j, i]), np.atleast_1d(Y[j, i])
            self.correlator.target.setPos(x_circ, y_circ)
            self.correlator.target.setPen("r")

            xname = self.correlator.settings["X"]
            yname = self.correlator.settings["Y"]
            self.correlator.plot.setLabels(**{"bottom": xname, "left": yname})
            sm = spearmanr(cor_x, cor_y)
            text = "Pearson's corr: {:.3f}<br>Spearman's: corr={:.3f}, pvalue={:.3f}".format(
                np.corrcoef(cor_x, cor_y)[0, 1], sm.correlation, sm.pvalue
            )
            self.correlator.plot.setTitle(text)

        except Exception as err:
            print(
                "Error in on_change_corr_settings: {}".format(err),
                traceback.format_exc(),
            )
            self.databrowser.ui.statusbar.showMessage(
                "Error in on_change_corr_settings: {}".format(err)
            )

    def save_state(self):
        from ScopeFoundry import h5_io

        fname = self.databrowser.settings["data_filename"]
        view_state_fname = "{fname}_state_view_{timestamp:%y%m%d_%H%M%S}.{ext}".format(
            fname=fname.strip(".h5"),
            timestamp=datetime.fromtimestamp(time.time()),
            ext="h5",
        )
        h5_file = h5py.File(name=view_state_fname)

        with h5_file as h5_file:
            h5_group_display_images = h5_file.create_group("display_images")
            for k, v in self.display_images.items():
                h5_group_display_images.create_dataset(k, data=v)
            h5_group_spec_x_array = h5_file.create_group("spec_x_arrays")
            for k, v in self.spec_x_arrays.items():
                h5_group_spec_x_array.create_dataset(k, data=v)
            h5_group_settings_group = h5_file.create_group("settings")
            h5_io.h5_save_lqcoll_to_attrs(self.settings, h5_group_settings_group)
            h5_group_settings_group = h5_file.create_group("x_slicer_settings")
            h5_io.h5_save_lqcoll_to_attrs(
                self.signal_selector.settings, h5_group_settings_group
            )
            h5_group_settings_group = h5_file.create_group("bg_slicer_settings")
            h5_io.h5_save_lqcoll_to_attrs(
                self.bg_selector.settings, h5_group_settings_group
            )
            h5_group_settings_group = h5_file.create_group("export_settings")
            h5_io.h5_save_lqcoll_to_attrs(self.export_settings, h5_group_settings_group)
            self.view_specific_save_state_func(h5_file)
            h5_file.close()

    def load_state(self, fname_idx=-1):

        # does not work properly, maybe because the order the settings are set matters?
        path = sibling_path(self.databrowser.settings["data_filename"], "")
        pre_state_fname = (
            self.databrowser.settings["data_filename"].strip(path).strip(".h5")
        )

        state_files = []
        for x in os.listdir(path):
            if pre_state_fname in x:
                if "state_view" in x:
                    state_files.append(x)

        print("state_files", state_files)

        if len(state_files) != 0:
            h5_file = h5py.File(path + state_files[fname_idx])
            for k, v in h5_file["bg_slicer_settings"].attrs.items():
                try:
                    self.bg_selector.settings[k] = v
                except:
                    pass
            for k, v in h5_file["x_slicer_settings"].attrs.items():
                try:
                    self.signal_selector.settings[k] = v
                except:
                    pass

            for k, v in h5_file["settings"].attrs.items():
                try:
                    self.settings[k] = v
                except:
                    pass

            for k, v in h5_file["biexponential_settings"].attrs.items():
                self.biexponential_settings[k] = v
            for k, v in h5_file["export_settings"].attrs.items():
                self.export_settings[k] = v

            h5_file.close()
            print("loaded", state_files[fname_idx])

    def view_specific_save_state_func(self, h5_file):
        """
        you can override me, use 'h5_file' - it's already open 
        e.g:  h5_file.create_group('scan_specific_settings')
         ...
        """
        pass

    def update_binning(self):
        binned_x = bin_x(self.hyperspec_data, self.settings["spatial_binning"])
        binned_xy = bin_y(binned_x, self.settings["spatial_binning"])
        binned = bin_spec(binned_xy, self.settings["binning"])
        arrays = {}
        for name, x in self.x_arrays.items():
            arrays[name] = bin_array(x, self.settings["binning"])
        self.set_data_manager(binned, arrays)


def bin_array(arr, binning):
    data = arr
    if binning > 1:
        Ns = data.shape[0]
        data = (
            data[: (Ns // binning) * binning]
            .reshape(Ns // binning, binning)
            .mean(axis=-1)
        )
    return data


def bin_x(hyperspec_data, binning):
    data = hyperspec_data
    if binning > 1:
        Nx, Ny, Ns = data.shape
        data = (
            data[: (Nx // binning) * binning, :, :]
            .reshape(Nx // binning, binning, Ny, Ns)
            .mean(axis=1)
        )
    return data


def bin_y(hyperspec_data, binning):
    data = hyperspec_data
    if binning > 1:
        Nx, Ny, Ns = data.shape
        data = (
            data[:, : (Ny // binning) * binning, :]
            .reshape(Nx, Ny // binning, binning, Ns)
            .mean(axis=-2)
        )
    return data


def bin_spec(hyperspec_data, binning):
    data = hyperspec_data
    if binning > 1:
        Nx, Ny, Ns = data.shape
        data = (
            data[:, :, : (Ns // binning) * binning]
            .reshape(Nx, Ny, Ns // binning, binning)
            .mean(axis=-1)
        )
    return data


def norm(x):
    x_max = x.max()
    if x_max == 0:
        return x * 0.0
    else:
        return x * 1.0 / x_max
