import time

import numpy as np
import pyqtgraph as pg
from qtpy import QtWidgets
from ScopeFoundry import Measurement, h5_io


class RangedOptimization(Measurement):
    """Sweeps a setting z within a range and measures an optimization quantity f(z)
    Finally sets z = z0 + z_offset where
    - f(z0) > f(z) for all z in that range

    options for f are specified at initialization.
    z can be specified with 3 settings:
        - *z_hw*
        - *z*
        - *z_target* (note that if z has a write func, then *z_target* can be the same as *z*
    """

    name = "ranged_optimization"

    def __init__(
        self,
        app,
        name=None,
        optimization_choices=[
            # specify  with lq_path
            ("hydraharp CountRate0", "hardware/hydraharp/CountRate0"),
            ("hydraharp CountRate1", "hardware/hydraharp/CountRate1"),
            ("picoharp CountRate", "hardware/picoharp/count_rate"),
            ("spotoptimizer 1/FWHM", "measure/toupcam_spot_optimizer/inv_FWHM"),
            ("spotoptimizer max value", "measure/toupcam_spot_optimizer/max_val"),
            ("spotoptimizer focus measure", "measure/toupcam_spot_optimizer/focus_measure"),
            ("andor count rate (cont.)", "measure/andor_ccd_readout/count_rate"),
            ("picam count rate (cont.)", "measure/picam_readout/count_rate"),
            ("apd count rate", "hardware/apd_counter/count_rate"),
        ],
        lq_kwargs={"spinbox_decimals": 6, "unit": ""},
        range_initials=[0, 10, 0.1],
    ):

        self.optimization_quantity_choices = optimization_choices
        self.range_initials = range_initials
        self.lq_kwargs = lq_kwargs
        Measurement.__init__(self, app, name)

    def setup(self):
        self.settings.New("use_current_z_as_center", dtype=bool, initial=True)

        self.settings.New(
            "optimization_quantity",
            dtype=str,
            choices=self.optimization_quantity_choices,
            initial=self.optimization_quantity_choices[0][1],
        )

        self.settings.New_Range(
            "z",
            include_center_span=True,
            initials=self.range_initials,
            **self.lq_kwargs
        )
        self.settings.New("z_offset", initial=0, **self.lq_kwargs)
        self.settings.New("N_samples", int, initial=10)
        self.settings.New(
            "sampling_period",
            float,
            initial=0.050,
            unit="s",
            si=True,
            description="time waited between sampling",
        )

        self.settings.New("use_fine_optimization", bool, initial=True)
        self.settings.New("z_span_travel_time", initial=2.0, unit="sec")

        self.settings.New("z_hw", dtype=str, initial="focus_wheel")
        self.settings.New("z", dtype=str, initial="position")
        self.settings.New("z_target", dtype=str, initial="target_position")
        self.settings.New("coarse_to_fine_span_ratio", initial=4.0)

        self.z0_history = []
        self.f_history = []
        self.z_history = []
        self.time_history = []
        self.t0 = time.time()

        self.z_original, self.z0_coarse, self.z0_fine = 0, 0, 0

        self.settings.New('post_process_option', str, initial='gauss', choices=('gauss',),
                          description='e.g. fit gaussian to data and use the derived mean as optimized value')
        self.add_operation('post process', self.post_process)
        self.add_operation('take processed value', self.go_to_post_process_value)
        
        self.settings.New("save_h5", bool, initial=True)

    def setup_figure(self):
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.ui.setLayout(self.layout)

        # # Add settings
        S = self.settings
        settings_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(settings_layout)

        operations_widget = QtWidgets.QWidget()
        operationsLayout = QtWidgets.QVBoxLayout()
        operations_widget.setLayout(operationsLayout)        
        settings_layout.addWidget(operations_widget)
        # start_pushButton = QtWidgets.QPushButton('Start')
        # start_pushButton.clicked.connect(self.start)
        # operationsLayout.addWidget(start_pushButton)
        # interrupt_pushButton = QtWidgets.QPushButton('Interrupt')
        # interrupt_pushButton.clicked.connect(self.interrupt)
        # operationsLayout.addWidget(interrupt_pushButton)
        operationsLayout.addWidget(S.activation.new_pushButton())    
        take_pushButton = QtWidgets.QPushButton('Interrupt and Take')
        take_pushButton.clicked.connect(self.take_current_optimal)
        operationsLayout.addWidget(take_pushButton)
        
        settings_layout.addWidget(
            S.New_UI(
                ["optimization_quantity", "N_samples", "sampling_period"]
            )
        )
        
        settings_layout.addWidget(
            S.New_UI(["use_current_z_as_center", "z_center", "z_span", "z_num"])
        )
        
        # third settings widget
        w3 = S.New_UI(["z_offset", "use_fine_optimization", "post_process_option"])
        settings_layout.addWidget(w3)
        post_process_pushButton = QtWidgets.QPushButton('post_process')
        post_process_pushButton.clicked.connect(self.post_process)
        w3.layout().addWidget(post_process_pushButton)
        go_to_post_process_value_pushButton = QtWidgets.QPushButton('go_to_post_process_value')
        go_to_post_process_value_pushButton.clicked.connect(self.go_to_post_process_value)
        w3.layout().addWidget(go_to_post_process_value_pushButton)

        # # Add plot and plot items
        self.graph_layout = pg.GraphicsLayoutWidget(border=(0, 0, 0))
        self.layout.addWidget(self.graph_layout)

        self.plot = self.graph_layout.addPlot()
        self.plot_line_coarse = self.plot.plot()
        self.plot_line_fine = self.plot.plot(pen="r")
        self.plot_line_post_process = self.plot.plot(pen="g")

        # indicator lines
        self.line_z_original = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen="b",
            label="original position: {value:0.6f}",
            labelOpts={
                "color": "b",
                "movable": True,
                "position": 0.15,
                "fill": (200, 200, 200, 200),
            },
        )
        self.line_z0_coarse = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen=(200, 200, 200),
            label="coarse optimized: {value:0.6f}",
            labelOpts={
                "color": (200, 200, 200),
                "movable": True,
                "position": 0.30,
                "fill": (200, 200, 200, 60),
            },
        )
        self.line_z0_fine = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen="r",
            label="fine optimized: {value:0.6f}",
            labelOpts={
                "color": "r",
                "movable": True,
                "position": 0.45,
                "fill": (200, 200, 200, 80),
            },
        )
        self.line_z0_post_process = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen="g",
            label="fit value: {value:0.6f}",
            labelOpts={
                "color": "g",
                "movable": True,
                "position": 0.50,
                "fill": (200, 200, 200, 80),
            },
        )
        self.plot.addItem(self.line_z_original, ignoreBounds=True)
        self.plot.addItem(self.line_z0_coarse, ignoreBounds=True)
        self.plot.addItem(self.line_z0_fine, ignoreBounds=True)
        self.plot.addItem(self.line_z0_post_process, ignoreBounds=True)

        self.plot.enableAutoRange()

    def get_optimization_quantity(self):
        x = 0.0
        for q in range(self.settings["N_samples"]):
            if self.optimization_lq.hardware_read_func is not None:
                x += self.optimization_lq.hardware_read_func()
            else:
                x += self.optimization_lq.val
            time.sleep(self.settings["sampling_period"])

        return x / self.settings["N_samples"]

    def run(self):
        S = self.settings        
        
        self.plot_line_post_process.setVisible(False)
        self.line_z0_post_process.setVisible(False)

        self.take_current = False

        z = self.app.hardware[S["z_hw"]].settings.get_lq(S["z"])
        z_target = self.app.hardware[S["z_hw"]].settings.get_lq(S["z_target"])        
        self.optimization_lq = self.app.lq_path(S["optimization_quantity"])

        # if measurement is interrupted, the z will be set to original pos
        self.z_original = z.val

        # create coarse data arrays
        if S["use_current_z_as_center"]:
            S["z_center"] = z.read_from_hardware() - S["z_offset"]
        self.z_coarse = np.linspace(
            S["z_center"] - 0.5 * S["z_span"],
            S["z_center"] + 0.5 * S["z_span"],
            S["z_num"],
            dtype=float,
        )
        self.f_coarse = np.zeros(S["z_num"], dtype=float)
        self.z0_coarse = S["z_center"]
        self.z0_fine = S["z_center"]

        # move to start position and wait
        z_target.update_value(self.z_coarse[0])
        time.sleep(S["z_span_travel_time"])

        # for loop through z-array
        for i, z in enumerate(self.z_coarse):
            self.set_progress(i * 100.0 / S["z_num"] / 3)

            z_target.update_value(z)
            time.sleep(S["z_span_travel_time"] / S["z_num"])
            self.f_coarse[i] = self.get_optimization_quantity()
            self.z0 = z0_coarse = self.z0_coarse = self.z_coarse[np.argmax(self.f_coarse)]
            if self.interrupt_measurement_called:
                break
            
        r = self.settings['coarse_to_fine_span_ratio']   
        # Repeat fine scan
        self.z_fine = np.linspace(
            z0_coarse - 0.5 * S["z_span"] / r,
            z0_coarse + 0.5 * S["z_span"] / r,
            2 * S["z_num"],
            dtype=float,
        )
        self.f_fine = np.ones(2 * S["z_num"], dtype=float) * self.f_coarse.max()

        if S["use_fine_optimization"] and not self.interrupt_measurement_called:
            z_target.update_value(self.z_fine[0])
            time.sleep(S["z_span_travel_time"])

            for i, z in enumerate(self.z_fine):
                self.set_progress((S["z_num"] + i) * 100.0 / S["z_num"] / 3)
                if self.interrupt_measurement_called:
                    break
                z_target.update_value(z)
                time.sleep(S["z_span_travel_time"] / S["z_num"] / 4)
                self.f_fine[i] = self.get_optimization_quantity()
                self.z0 = self.z0_fine = self.z_fine[np.argmax(self.f_fine)]

        if self.interrupt_measurement_called and not self.take_current:
            print(self.name, "interrupted, moving to original position")
            z_target.update_value(self.z_original)
        elif self.interrupt_measurement_called and self.take_current:
            print(self.name, "interrupted, moving to current optimal")
            z_target.update_value(self.z0 + S["z_offset"])
            self.save_h5_file()
            time.sleep(S["z_span_travel_time"] / 4)
        else:
            print(self.name, "finished, moving to range optimal")
            z_target.update_value(self.z0 + S["z_offset"])
            self.save_h5_file()

            # Update history
            self.z0_history.append(self.z0)
            self.f_history.append(S["optimization_quantity"])
            self.z_history.append(S["z"])
            self.time_history.append(int((time.time() - self.t0)))

            # print history
            template = "{0:10}, {1:8.4}, {2:25};"
            print(template.format("time [s]", "z0", "optimized quantity"))
            for rec in zip(self.time_history, self.z0_history, self.f_history):
                print(template.format(*rec))

            time.sleep(S["z_span_travel_time"] / 4)

            # TODO, make a plot of the history
            
    def pre_run(self):
        S = self.settings
        self.hw0 = None
        self.S0 = None
        if S['optimization_quantity'] == 'measure/andor_ccd_readout/count_rate':
            self.hw0 = self.app.measurements.andor_ccd_readout
            self.S0 = self.hw0.settings.as_value_dict()
            self.hw0.settings['explore_mode_exposure_time'] = S['sampling_period']
            self.hw0.settings['explore_mode'] = True
            
        if S['optimization_quantity'] == 'measure/picam_readout/count_rate':
            self.hw0 = self.app.measurements.picam_readout
            self.S0 = self.hw0.settings.as_value_dict()
            self.hw0.settings['continuous'] = True
                    
        elif S['optimization_quantity'] == 'hardware/apd_counter/count_rate':
            self.hw0 = self.app.hardware.apd_counter
            self.S0 = self.hw0.settings.as_value_dict()
            self.hw0.settings['int_time'] = S['sampling_period']
            
        # self.app.hardware.flip_mirror.settings['mirror_position'] = True
            
    def post_run(self):
        if self.S0 and self.hw0:
            for k, v in self.S0.items():
                self.hw0.settings[k] = v

        
        #self.app.hardware.flip_mirror.settings['mirror_position'] = False

            
    def save_h5_file(self):        
        if self.settings['save_h5']:            
            self.t0 = time.time()
            self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
            try:
                self.h5_file.attrs['time_id'] = self.t0
                H = self.h5_meas_group = h5_io.h5_create_measurement_group(self, self.h5_file)    
                H['f_coarse'] = self.f_coarse
                H['z_coarse'] = self.z_coarse
                H['z0_coarse'] = self.z0_coarse
                H['z_original'] = self.z_original
                H['z0'] = self.z0

                if self.settings['use_fine_optimization']:
                    H['f_fine'] = self.f_fine
                    H['z_fine'] = self.z_fine
                    H['z0_fine'] = self.z0_fine
                    
                print(self.name, 'saved h5 file')
            finally:
                self.log.info("data saved " + self.h5_file.filename)
                self.h5_file.close()

    def update_display(self):

        S = self.settings

        # self.plot.enableAutoRange()
        self.plot.setLabels(bottom=S["optimization_quantity"], left="z")

        self.plot_line_coarse.setData(self.f_coarse, self.z_coarse)
        if hasattr(self, "f_fine"):
            self.plot_line_fine.setData(self.f_fine, self.z_fine)

        self.line_z_original.setPos(self.z_original)
        self.line_z0_coarse.setPos(self.z0_coarse)
        self.line_z0_fine.setPos(self.z0_fine)

        self.line_z0_fine.setVisible(S["use_fine_optimization"])
        self.plot_line_fine.setVisible(S["use_fine_optimization"])
        
    def take_current_optimal(self):
        self.take_current = True
        self.interrupt_measurement_called = True

    def post_process(self):
        '''apply an algorithm to find a derived optimized quantity'''
        S = self.settings
        if S['use_fine_optimization']:
            z, f = self.z_fine, self.f_fine
        else:
            z, f = self.z_coarse, self.f_coarse
        
        self.z_post_process = z
        self.f_post_process = f  # typically to be overwritten
        self.z0_post_process = z.mean()  # overwrite this!
                
        if S['post_process_option'] == 'gauss':
            a, mean, sigma = fit_gauss(z, f - f.min())
            self.f_post_process = gauss(z, a, mean, sigma) + f.min()
            self.z0_post_process = mean
            
        print(self.name, f'used {S["post_process_option"]} fit option')
        self.plot_line_post_process.setVisible(True)
        self.plot_line_post_process.setData(self.f_post_process, self.z_post_process)
        self.line_z0_post_process.setVisible(True)
        self.line_z0_post_process.setPos(self.z0_post_process)

    def go_to_post_process_value(self):
        S = self.settings
        z_target = self.app.hardware[S["z_hw"]].settings.get_lq(S["z_target"])        
        z_target.update_value(self.z0_post_process + S["z_offset"])

        
def gauss(x, a, x0, sigma):
    return a * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))

    
def fit_gauss(x, y):
    from scipy.optimize import curve_fit
    p0 = [y.max(), x[y.argmax()], 10]
    popt, pcov = curve_fit(gauss, x, y, p0=p0)
    return popt  # a,mean,sigma 

