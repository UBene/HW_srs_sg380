"""
Created on Jul 20, 2018

@author: Benedikt Ursprung
"""

from qtpy import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
import numpy as np
import pyqtgraph.dockarea as dockarea


class MinMaxQSlider(QtWidgets.QWidget):
    """
    Costume QSlider widget designed to work with logged_quantities.
    Two spin boxes allow to dynamically update the min and max value of the slider.
    """

    # Signals
    updated_value = QtCore.Signal((float,), (int,))

    def __init__(
        self, name="", spinbox_decimals=2, is_logarithmic=False, **QSlider_kwargs
    ):

        self.name = name

        # Setup widget
        QtWidgets.QWidget.__init__(self)

        # slider
        self.slider = QtWidgets.QSlider(
            orientation=QtCore.Qt.Horizontal, **QSlider_kwargs
        )
        self.slider.valueChanged.connect(self.on_slider_value_changed)
        self.slider.setSingleStep(1)
        self.slider.sliderMoved[int].connect(self.set_title)

        # min and max spinbox
        self.min_double_spinbox = QtWidgets.QDoubleSpinBox()
        self.min_double_spinbox.setRange(-1e12, 1e12)
        self.max_double_spinbox = QtWidgets.QDoubleSpinBox()
        self.max_double_spinbox.setRange(-1e12, 1e12)

        self.min_double_spinbox.valueChanged[float].connect(self.update_slider_minimum)
        self.max_double_spinbox.valueChanged[float].connect(self.update_slider_maximum)

        self.setDecimals(spinbox_decimals)

        # title label
        self.title_label = QtWidgets.QLabel()

        # Setup layout
        self.layout_ = QtWidgets.QGridLayout()
        self.layout_.addWidget(
            self.min_double_spinbox, 0, 0, alignment=QtCore.Qt.AlignLeft
        )
        self.layout_.addWidget(self.title_label, 0, 1, alignment=QtCore.Qt.AlignHCenter)
        self.layout_.addWidget(
            self.max_double_spinbox, 0, 2, alignment=QtCore.Qt.AlignRight
        )
        self.layout_.addWidget(self.slider, 1, 0, 1, 3)

        self.setLayout(self.layout_)
        self.is_logarithmic = is_logarithmic

    def set_name(self, name):
        self.name = name
        val = self.transform_from_slider(self.slider.value())
        self.set_title(val)

    @property
    def vmin(self):
        return self.min_double_spinbox.value()

    @property
    def vmax(self):
        return self.max_double_spinbox.value()

    @property
    def vrange(self):
        return self.vmax - self.vmin

    def transform_to_slider(self, x):
        if self.is_logarithmic:
            x = np.log10(x)
        pct = 100 * (x - self.vmin) / self.vrange
        return int(pct)

    def transform_from_slider(self, x):
        if self.is_logarithmic:
            x = 10 ** x
        val = self.vmin + (x * self.vrange / 100)
        return val

    def update_min_double_spinbox(self, vmin):
        try:
            self.min_double_spinbox.blockSignals(True)
            self.min_double_spinbox.setValue(vmin)
        finally:
            self.min_double_spinbox.blockSignals(False)

    def update_max_double_spinbox(self, vmax):
        try:
            self.max_double_spinbox.blockSignals(True)
            self.max_double_spinbox.setValue(vmax)
        finally:
            self.max_double_spinbox.blockSignals(False)

    def update_slider_minimum(self, vmin):
        val = self.slider.sliderPosition()
        self.slider.setMinimum(self.transform_to_slider(vmin))
        self.slider.setSliderPosition(val)

    def update_slider_maximum(self, vmax):
        self.slider.setMaximum(self.transform_to_slider(vmax))

    def update_value(self, x):
        try:
            self.slider.blockSignals(True)
            self.slider.setValue(self.transform_to_slider(x))
        finally:
            self.slider.blockSignals(False)

    def on_slider_value_changed(self):
        val = self.transform_from_slider(self.slider.value())
        self.updated_value.emit(val)

    def setRange(self, vmin, vmax):
        # as it is currently used in LoggedQuantity.change_min_max()
        self.update_min_double_spinbox(vmin)
        self.update_max_double_spinbox(vmax)

    def setDecimals(self, decimals):
        self.min_double_spinbox.setDecimals(decimals)
        self.max_double_spinbox.setDecimals(decimals)

    def setSuffix(self, unit):
        self.min_double_spinbox.setSuffix(" " + unit)
        self.max_double_spinbox.setSuffix(" " + unit)

    def setSingleStep(self, spinbox_step):
        self.min_double_spinbox.setSingleStep(spinbox_step)
        self.max_double_spinbox.setSingleStep(spinbox_step)

    def set_title(self, val):
        val = self.transform_from_slider(val)
        text = self.name + " " + str(val)
        self.title_label.setText(text)


class RegionSlicer(QtWidgets.QWidget):
    """
    **Bases:** :class: `QWidget <pyqt.QtWidgets.QWidget>`
    
    Adds a movable <pyqtgraph.LinearRegionItem> to a plot.
    Provides a numpy slice and mask that would slices the x_array according to the region.
    
    ===============================  =============================================================================
    **Signals:**
    region_changed_signal()          Emitted when region is changed or activated by user
    ===============================  =============================================================================
    
    
    ===============================  =============================================================================
    **Properties:**
    slice:                           numpy.slice[start:stop]
    s_:                              :property:slice if activated  else *s_return_on_deactivated*
    mask:                            numpy boolean array of size 'x_array': True for where x is within region
                                     false otherwise (ignores step). Useful if x_array is not ordered. 
    m_:                              mask if activated, else a mask equivalent to 
                                        *s_return_on_deactivated*
    ===============================  =============================================================================    
    """

    region_changed_signal = QtCore.Signal()

    def __init__(
        self,
        plot_item,
        x_array=None,
        name="array_slicer_name",
        slicer_updated_func=lambda: None,
        initial=[0, 100],
        s_return_on_deactivated=np.s_[:],
        brush=QtGui.QColor(0, 255, 0, 70),
        ZValue=10,
        font=QtGui.QFont("Times", 12),
        label_line=1,
        activated=False,
    ):
        """Create a new LinearRegionItem on plot_item.
        
        ====================== ==============================================================
        **Arguments:**
        plot_item              <pyqtgraph.PlotDataItem> (recommended) 
                                or <pyqtgraph.PlotItem>  (does not grab x_array data from plot
                                item: initialize x_array manually
                                or use :func:`set_x_array <self.set_x_array>`)
        x_array                use to initialize x_array if plot_item == <pyqtgraph.PlotItem>.
        name                   <str> 
        slicer_updated_func    gets called when region is updated, alternatively use 
                               :sig:region_changed_signal().
        initial                initial index values [start,stop,step] or [start,stop]
        s_return_on_deactivated  Object returned if RegionSlicer is not activated.
                                 Slicing with np.s_[:] (default) and np.s_[0] gives the full and 
                                 an empty array respectively. Note, <RegionSlicer.slice> always 
                                 returns the last determined slice even if slice is deactivated.
        brush,ZValue,          are passed to the LinearRegionItem
        font,                  passed to the label
        label_line             '0' or '1' for placement of label onto 'left' or 'right'
                               bounding line. 
        activated              <bool> state at initialization
        ====================== ===============================================================
        """
        QtWidgets.QWidget.__init__(self)

        self.name = name

        self.slicer_updated = slicer_updated_func

        from ScopeFoundry.logged_quantity import LQCollection

        self.settings = LQCollection()
        if len(initial) == 2:
            initial.append(1)
        start, stop, step = initial
        self.start = self.settings.New("start", int, initial=start, vmin=0)
        self.stop = self.settings.New("stop", int, initial=stop, vmin=0)
        self.step = self.settings.New("step", int, initial=step)
        self.activated = self.settings.New("activated", bool, initial=activated)

        self.s_return_on_deactivated = s_return_on_deactivated

        if type(plot_item) == pg.PlotDataItem:
            self.plot_data_item = plot_item
            self.plot_data_item.sigPlotChanged.connect(self.set_x_array_from_data_item)
            self.parent_plot_item = plot_item.parentItem()
        elif type(plot_item) == pg.PlotItem:
            self.plot_data_item = None
            self.parent_plot_item = plot_item

        self.linear_region_item = pg.LinearRegionItem(brush=brush)
        self.linear_region_item.setZValue(ZValue)
        self.parent_plot_item.addItem(self.linear_region_item)

        self.inf_line_label = pg.InfLineLabel(
            self.linear_region_item.lines[label_line],
            self.name,
            position=0.78,
            anchor=(0.5, 0.5),
        )
        # self.inf_line_label = pg.TextItem(self.name, anchor=(0.5, 0.5))
        self.inf_line_label.setFont(font)
        self.set_label("")

        if x_array == None:  # give it something to work with.
            x_array = np.arange(512)
        self.set_x_array(x_array)

        self.start.add_listener(self.on_change_start_stop)
        self.stop.add_listener(self.on_change_start_stop)
        self.activated.add_listener(self.on_change_activated)
        self.linear_region_item.sigRegionChangeFinished.connect(self.on_change_region)

    @QtCore.Slot(object)
    def set_x_array_from_data_item(self):
        x_array, _ = self.plot_data_item.getData()
        if not np.array_equal(x_array, self.x_array):
            self.apply_new_x_array(x_array)
            # print('set_x_array_from_data_item: new x_array()')
        else:
            pass

    def set_x_array(self, x_array):
        """
        use this function to update the x_array
        not required to use if type(plot_item) == pg.PlotDataItem
        """
        self.apply_new_x_array(x_array)

    def apply_new_x_array(self, x_array):
        mn, mx = self.linear_region_item.getRegion()
        self.x_array = x_array
        self.linear_region_item.setBounds([self.x_array.min(), self.x_array.max()])
        self.settings["start"] = np.argmin((x_array - mn) ** 2)
        self.settings["stop"] = np.argmin((x_array - mx) ** 2)

    @property
    def slice(self):
        S = self.settings
        return np.s_[S["start"] : S["stop"] : S["step"]]

    @property
    def s_(self):
        """returns slice based on region if activated else `s_return_on_deactivated`"""
        if self.activated.val:
            return self.slice
        else:
            return self.s_return_on_deactivated

    @property
    def mask(self):
        Xmin = self.x_array[self.settings["start"]]
        Xmax = self.x_array[self.settings["stop"]]
        return (self.x_array >= Xmin) * (self.x_array <= Xmax)

    @property
    def m_(self):
        if self.activated.val:
            return self.mask
        else:
            s = self.s_return_on_deactivated
            Xmin = self.x_array[s.start]
            Xmax = self.x_array[s.stop]
            return (self.x_array >= Xmin) * (self.x_array <= Xmax)

    @QtCore.Slot(object)
    def on_change_region(self):
        """
        updates settings based on region 
        """
        print(self.name, "on_change_region")
        self.region_min, self.region_max = mn, mx = self.linear_region_item.getRegion()
        self.settings["start"] = np.argmin((self.x_array - mn) ** 2)
        self.settings["stop"] = np.argmin((self.x_array - mx) ** 2)
        self.region_changed_signal.emit()
        self.slicer_updated()

    def on_change_start_stop(self):
        """
        updates linear_region_item based on settings 
        """
        rgn = [0, 0]
        rgn[0] = self.x_array[self.settings["start"]]
        try:
            rgn[1] = self.x_array[self.settings["stop"]]
        except IndexError:
            rgn[1] = self.x_array[self.settings["start"]]
        self.linear_region_item.setRegion(rgn)

    def on_change_activated(self):
        activated = self.activated.val
        self.linear_region_item.setEnabled(activated)
        self.linear_region_item.setAcceptHoverEvents(activated)
        self.linear_region_item.setAcceptTouchEvents(activated)
        self.linear_region_item.setVisible(activated)
        self.region_changed_signal.emit()
        self.slicer_updated()

    def New_UI(self, include=None, exclude=[]):
        ui_widget = self.settings.New_UI(include, exclude)
        ui_widget.layout().insertRow(0, QtWidgets.QLabel("<b>{}</b>".format(self.name)))
        return ui_widget

    def set_label(self, text="", title=None, color=(200, 200, 200)):
        if title == None:
            title = self.name
        label = "<h3>{}</h3>{}".format(title, text)
        self.inf_line_label.setHtml(label)
        self.inf_line_label.setColor(color)

    def get_sliced_xar(self, ar=None):
        if ar == None:
            if hasattr(self, "plot_data_item"):
                _, y = self.plot_data_item.getData()
                return (self.x_array[self.s_], y[self.s_])
            else:
                return None
        else:
            return (self.x_array[self.s_], ar[self.s_])


class DataSelector:
    def __init__(
        self,
        plot_data_item: pg.PlotDataItem,
        name: str = "slicer",
        initials: [int] = [0, 10, 1],
        color="g",
    ):
        self.name = name

        from ScopeFoundry.logged_quantity import LQCollection

        self.settings = LQCollection()
        start, stop, step = initials
        self.start = self.settings.New("start", int, initial=start, vmin=0)
        self.stop = self.settings.New("stop", int, initial=stop, vmin=0)
        self.step = self.settings.New("step", int, initial=step)
        self.activated = self.settings.New("activated", bool, initial=False)
        self.mode = self.settings.New(
            "mode", str, initial="mask", choices=("slice", "mask")
        )

        self.plot_data_item = plot_data_item
        self.plot = plot_data_item.parentItem()

        self.linear_region_item = pg.LinearRegionItem(pen=pg.mkPen(pg.mkColor(color)))
        self.linear_region_item.sigRegionChangeFinished.connect(self.on_region_changed)
        self.label = pg.InfLineLabel(
            self.linear_region_item.lines[0],
            self.name,
            position=0.78,
            anchor=(0.5, 0.5),
        )
        self.plot.addItem(self.linear_region_item)

        self.activated.add_listener(self.set_visible)

    def set_plot_data_item(self, plot_data_item):
        self.plot_data_item = plot_data_item

    def on_region_changed(self):
        mn, mx = self.linear_region_item.getRegion()
        x, _ = self.plot_data_item.getData()
        self.settings["start"] = np.argmin((x - mn) ** 2)
        self.settings["stop"] = np.argmin((x - mx) ** 2) + 1

    def on_change_start_stop(self):
        x, _ = self.plot_data_item.getData()
        mn = x[self.settings["start"]]
        mx = x[self.settings["stop"]]
        self.linear_region_item.setRegion((mn, mx))

    def get_masked_data(self):
        x, y = self.plot_data_item.getData()
        mask = self.mask
        return x[mask], y[mask]

    def get_sliced_data(self):
        x, y = self.plot_data_item.getData()
        s = self.slice
        return x[s], y[s]

    def get_data(self):
        if self.activated.val:
            if self.mode.val == "mask":
                return self.get_masked_data()
            else:
                return self.get_sliced_data()
        else:
            return self.plot_data_item.getData()

    @property
    def x(self):
        return self.get_data()[0]

    @property
    def y(self):
        return self.get_data()[1]

    @property
    def mask(self):
        x, _ = self.plot_data_item.getData()
        mn, mx = self.linear_region_item.getRegion()
        return (x >= mn) * (x <= mx)

    @property
    def slice(self):
        S = self.settings
        return np.s_[S["start"] : S["stop"] : S["step"]]

    def New_UI(self, include=None, exclude=[]):
        ui_widget = self.settings.New_UI(include, exclude)
        ui_widget.layout().insertRow(0, QtWidgets.QLabel(f"<b>{self.name}</b>"))
        return ui_widget

    def New_Dock(self):
        return dockarea.Dock(name=self.name, widget=self.New_UI())

    def set_label(self, text="", title=None, color=(200, 200, 200)):
        if title == None:
            title = self.name
        label = "<h3>{}</h3>{}".format(title, text)
        self.label.setHtml(label)
        self.label.setColor(color)

    def set_visible(self, v=None):
        if not v:
            v = self.activated.val
        self.label.setVisible(v)
        self.linear_region_item.setVisible(v)

    def add_listener(
        self, func, include=["start", "stop", "step", "activated"], argtype=(), **kwargs
    ):
        for key in include:
            self.settings.get_lq(key).add_listener(func, argtype, **kwargs)
