'''
Created on Oct 27, 2016

@author: Edward Barnard
'''
from __future__ import absolute_import, division, print_function
from ScopeFoundry import Measurement
import numpy as np
import pyqtgraph as pg
import time
from ScopeFoundry.helper_funcs import sibling_path, replace_widget_in_layout
from ScopeFoundry import h5_io
from collections import deque


class LakeshoreMeasure(Measurement):

    name = "lakeshore_measure"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "lakeshore_measure.ui")
        Measurement.__init__(self, app)
        
    def setup(self):        
        self.display_update_period = 1  # seconds

        # logged quantities
        S = self.settings
        self.save_data = S.New(name='save_data', dtype=bool, initial=False, ro=False,
                                           description='saves current history')
        S.New(name='update_period', dtype=float, si=True, initial=1, unit='s')

        # std stability
        S.New('std', float, initial=1000, ro=True, unit='K', spinbox_decimals=4,
              description='''standard deviation of the last 15 data points from <b>control_input</b>''')
        S.New('std_stable', float, initial=0.005, unit='K', spinbox_decimals=4,
              description='criterion for <b>is_std_stable</b>')
        S.New('is_std_stable', bool, colors=['rgba(255,0,0,100)', 'rgba(0,120,0,100)'],
              initial=False, ro=True,
              description='''True iff the standard deviation <b>std</b> of 
                             the last 15 data points is lower than <b>std_stable</b>. 
                             Is agnostic to difference in set-point and actual temperature.''')
        S.is_std_stable.add_listener(self.on_stable)
        S.New('is_awake', bool, initial=True,
              description='''toggle True to skip waiting periods, e.g. when queued measurements are waiting to stabilize.''')
        
        S.New('auto_range_plot', bool, initial=False)

        # create data array
        self.OPTIMIZE_HISTORY_LEN = 1800

        self.optimize_history_A = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)
        self.optimize_history_B = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)            
        self.optimize_ii = 0

        # hardware
        self.ctrl = self.app.hardware['lakeshore335']
        self.optimize_ii = 0
        
        self.plot_ready = False

    def setup_figure(self):

        S = self.settings
        # connect events
        self.ctrl.settings.connected.connect_to_widget(self.ui.connected_checkBox)        
        S.activation.connect_to_pushButton(self.ui.start_pushButton)
        self.ui.T_A_PGSpinBox = replace_widget_in_layout(self.ui.T_A_doubleSpinBox,
                                                         pg.widgets.SpinBox.SpinBox())
        self.ui.T_B_PGSpinBox = replace_widget_in_layout(self.ui.T_B_doubleSpinBox,
                                                         pg.widgets.SpinBox.SpinBox())
        self.ctrl.settings.T_A.connect_to_widget(self.ui.T_A_PGSpinBox)
        self.ctrl.settings.T_B.connect_to_widget(self.ui.T_B_PGSpinBox)
        
        self.ctrl.settings.manual_heater_output.connect_to_widget(self.ui.manual_heater_output_doubleSpinBox)
        self.ctrl.settings.analog_output.connect_to_widget(self.ui.heater_output_progressBar)
        self.ctrl.settings.setpoint_T.connect_to_widget(self.ui.setpoint_T_doubleSpinBox)
        self.ctrl.settings.input_sensor.connect_to_widget(self.ui.control_input_comboBox)
        self.ctrl.settings.heater_output_mode.connect_to_widget(self.ui.control_mode_comboBox)
        self.ctrl.settings.heater_range.connect_to_widget(self.ui.heater_range_comboBox)
        self.ctrl.settings.ramp_enable.connect_to_widget(self.ui.ramp_on_checkBox)
        self.ctrl.settings.rate_value.connect_to_widget(self.ui.ramp_rate_doubleSpinBox)
        self.save_data.connect_to_widget(self.ui.save_data_checkBox)

        S.is_std_stable.connect_to_widget(self.ui.is_std_stable_checkBox)
        S.std_stable.connect_to_widget(self.ui.std_stable_doubleSpinBox)
        S.std.connect_to_widget(self.ui.std_doubleSpinBox)
        S.is_awake.connect_to_pushButton(self.ui.is_awake_pushButton,
                                          ['rgba(200,0,0,50)', 'rgba(0,200,0,50)'],
                                          ['sleeping - wake up',
                                           'awake - put to sleep'],)
                
        self.ui.add_event_pushButton.clicked.connect(self.on_add_event_pushButton)
        self.ui.clear_events_pushButton.clicked.connect(self.clear_history_events)
        self.ui.set_history_start_pushButton.clicked.connect(self.set_history_start)
        self.ui.save_history_pushButton.clicked.connect(lambda:self.save_history(None, None))
        
        self.add_operation('set history start', self.set_history_start)
        self.add_operation('save history', lambda:self.save_history(None, None))
        self.add_operation('wake up', self.wake_up)
        S.activation.add_listener(self.wake_up)

        self.graph_layout = pg.GraphicsLayoutWidget(border=(100, 100, 100))
        self.ui.plot_widget.layout().addWidget(self.graph_layout)        
        self.plot = self.graph_layout.addPlot(title="Lakeshore 331 Readout")
        #xaxis = pg.DateAxisItem(orientation="bottom")
        #self.plot.setAxisItems({"bottom":xaxis})        
        self.plot.setLabel('left', text='T', units='K')
        
        self.reset_plot()

    def reset_plot(self):
        self.plot_ready = False
        
        # Call this function when the plot gets slow        
        self.clear_history_events()
        if hasattr(self, 'plot'):
            self.plot.clear()
            self.plot.deleteLater()
            del self.plot
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater()  # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout

        self.graph_layout = pg.GraphicsLayoutWidget(border=(100, 100, 100))
        self.ui.plot_widget.layout().addWidget(self.graph_layout)
        
        # history plot
        self.plot = self.graph_layout.addPlot(title="Lakeshore 331 Readout")
        
        self.optimize_plot_line_A = self.plot.plot(np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float), name='T_A', pen={'color': "r", 'width': 2}) 
        self.optimize_plot_line_B = self.plot.plot(np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float), name='T_B', pen={'color': "b", 'width': 2})
        
        self.line_t = pg.InfiniteLine(
            movable=False,
            pen=(0, 255, 255),
            label="t: {value:0.0f} sec",
            labelOpts={
                "color": (0, 255, 255),
                "movable": True,
                "position": 0.85,
                "fill": (200, 200, 200, 60),
            },
            )
        self.line_history_start = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=(0, 255, 255),
            label="history start: {value:0.0f} sec",
            labelOpts={
                
                "color": (0, 255, 255),
                "movable": True,
                "position": 0.80,
                "fill": (200, 200, 200, 60),
            },
            )
        self.plot.addItem(self.line_t)
        self.plot.addItem(self.line_history_start)
        
        self.plot_ready = True
        
    def pre_run(self):
        self.reset_plot()
                    
    def run(self):
        self.reset()

        S = self.settings
        S['is_std_stable'] = False
        CS = self.ctrl.settings        

        if self.save_data.val:
            self.full_optimize_history = []
            self.full_optimize_history_time = []
            self.t0 = time.time()

        while not self.interrupt_measurement_called:
            
            # check for std_stability
            try:
                self.std_stability_data.pop()
                control_temp = CS[f'T_{CS["control_input"]}']
                self.std_stability_data.appendleft(control_temp)
                S['std'] = np.std(list(self.std_stability_data))
                S['is_std_stable'] = S['std'] < S['std_stable']
    
                # Update history data
                self.optimize_ii += 1
                self.optimize_ii %= self.OPTIMIZE_HISTORY_LEN
                if self.optimize_ii == 0:
                    self.reset_time_array()
                self.optimize_history_A[self.optimize_ii] = self.ctrl.settings['T_A']
                self.optimize_history_B[self.optimize_ii] = self.ctrl.settings['T_B']
                
                # print(self.optimize_history_A[self.optimize_ii] - self.optimize_history_A[self.optimize_ii-2])
                
            except:
                pass
            
            time.sleep(self.settings['update_period'])
            
        if self.settings['save_data']:
            self.save_history(0, self.OPTIMIZE_HISTORY_LEN - 1)
            
        S['is_std_stable'] = False
            
    def set_history_start(self):
        ''' use in conjunction with set_history_stop to set the time interval of a temperature series'''
        self.optimize_ii_start = self.optimize_ii
        self.t_start = self.time_array[self.optimize_ii_start]
        print(self.name, 'history start', self.t_start, self.optimize_ii_start)
        self.clear_history_events()
        
    def set_history_end(self):
        ''' use in conjunction with set_history_start to set the time interval of a temperature series'''
        self.optimize_ii_end = self.optimize_ii
        self.t_end = self.time_array[self.optimize_ii_end]
        # self.save_history(ii_end=self.optimize_ii_end)
        return self.optimize_ii_end
            
    def save_history(self, ii_start=None, ii_end=None):
        '''stores data between history start and end in a h5_file'''
        if ii_start == None:
            ii_start = self.optimize_ii_start
        if ii_end == None:
            ii_end = self.set_history_end()
            
        try:
            self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
            self.h5_file.attrs['time_id'] = time.time()
            H = self.h5_meas_group = h5_io.h5_create_measurement_group(self, self.h5_file)
        
            # create h5 data arrays
            if ii_start < ii_end:
                s = np.s_[ii_start:ii_end + 1]
                H['T_A'] = self.optimize_history_A[s]
                H['T_B'] = self.optimize_history_B[s]
                t_start = self.time_array[ii_start]
                t_end = self.time_array[ii_end]
            else:

                def re_arrange(a, i0, i1):
                    return np.roll(a, len(a) - i1)[:i0 + len(a) - i1 + 1]

                H['T_A'] = re_arrange(self.optimize_history_A, ii_start, ii_end)
                H['T_B'] = re_arrange(self.optimize_history_B, ii_start, ii_end)
                t_start = self.time_array[ii_start]
                t_end = self.time_array[ii_end] + max(self.time_array)
                
            p = self.settings['update_period']
            H['time_array'] = np.arange(t_start, t_end + p, p)
            H['time_start'] = t_start
            H['time_end'] = t_end
            
            try:
                time_events_group = H.create_group('time_events')
                colors_events_group = H.create_group('ii_events')
                
                if hasattr(self, 'events'):
                    for line, text, t, ii, c in self.events:
                        time_events_group.attrs[text] = t
                        colors_events_group[text] = c
                print('saved events')

            except:
                print('failed to save events')
            
            print(self.name, f'save history {ii_start} {ii_end} success')

        finally:
            self.h5_file.close()
            
    def reset_time_array(self):
        self.time_array = np.arange(self.OPTIMIZE_HISTORY_LEN) * self.settings['update_period'] + int(time.time())
    
    def reset(self):
        self.reset_time_array()
        self.optimize_history_A = np.ones(self.OPTIMIZE_HISTORY_LEN, dtype=np.float) * self.ctrl.settings['T_A']
        self.optimize_history_B = np.ones(self.OPTIMIZE_HISTORY_LEN, dtype=np.float) * self.ctrl.settings['T_B']            
        self.optimize_ii = 0
        self.std_stability_data = deque(np.arange(15) * 100)
        self.set_history_start()
            
    def clear_history_events(self):
        if hasattr(self, 'events'):
            for event in self.events:
                line = event[0]
                self.plot.removeItem(line)
        self.events = []
            
    def add_history_event(self, text, color=(200, 200, 200)):
        ''' to track events between calling set_history_start and set_history_end'''

        print('added history event', text)
        ii = self.optimize_ii
        time = self.time_array[ii]

        line = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=color,
            label=f"{text}: {time} sec",
            labelOpts={
                "color": color,
                "movable": True,
                "position": 0.4,
                "fill": (200, 200, 200, 60),
                'rotateAxis': [1, 0],
                },
            )
        line.setPos(time)
        self.plot.addItem(line)
        self.events.append([line, text, time, ii, color])
        
    def on_add_event_pushButton(self):
        text = self.ui.event_text_lineEdit.text()
        self.add_history_event(text)
        self.ui.event_text_lineEdit.setText("")
            
    def update_display(self):
        if self.plot_ready:
            self.display_update_period = self.settings['update_period']
            self.line_t.setPos(self.time_array[self.optimize_ii])
            self.line_history_start.setPos(self.t_start)
            self.optimize_plot_line_A.setData(self.time_array, self.optimize_history_A)
            self.optimize_plot_line_B.setData(self.time_array, self.optimize_history_B)
            if self.settings['auto_range_plot']:
                self.plot.setXRange(self.t_start, self.time_array[self.optimize_ii])
    
    def on_stable(self):
        return  # causes cluttering the plot
        q = self.settings["std_stable"]
        s = self.settings['is_std_stable']
        text = { True: f'stable, (std < {q})',
                 False: f'unstable,(std > {q})'}[s]
        color = { True: (0, 255, 0, 180),
                 False: (255, 0, 0, 180)}[s]
        self.add_history_event(text, color=color)
        
    def wake_up(self):
        self.settings['is_awake'] = True
        
    def wait_until_stable(self,
                          setpoint_T=None,
                          timeout=20 * 60,
                          delay=60,
                          ):
        '''
        MAYBE UNSTABLE
        Sets *setpoint_T* and starts *measurements* after a stabilization period. 
        The stabilization period is over when one of the following criterion is met:
            1. *timeout* duration passed.
            2. is_std_stable setting toggles True the first time after *delay* passed. 
            3. The 'is_awake' is set to True 
                (can be set True by calling self.wake_up or self.interrupt)
        A *delay* >= 5 sec is recommended as Temperature might be stable for 
        some time after changing the setpoint temperature.
        '''
        
        S = self.settings
                
        if not S['activation']:
            S['activation'] = True
        
        S['is_awake'] = False

        t0 = time.time()
        
        # set temperature settings
        TS = self.app.hardware['lakeshore331'].settings
        if setpoint_T:
            TS['setpoint_T'] = setpoint_T
            time.sleep(delay)
        
        # wait 
        while time.time() - t0 < timeout:
            pct = 100 * ((timeout - (time.time() - t0)) / timeout)
            self.set_progress(pct)
            print(self.name, 'setpoint_T', setpoint_T,
                  'stabilization, press wake_up or wait',
                  timeout - (int(time.time() - t0)), 'sec')
            if S['is_awake']:
                break
            if S['is_std_stable']:
                break
            time.sleep(S['update_period'])
        S['is_awake'] = True
        
    def queue_measurements(self,
                          setpoint_T=None,
                          measurements=None,
                          timeout=20 * 60,
                          delay=60,
                          ):
        '''
        MAYBE UNSTABLE
        Sets *setpoint_T* and starts *measurements* after a stabilization period. 
        The stabilization period is over when one of the following criterion is met:
            1. *timeout* duration passed.
            2. is_std_stable setting toggles True the first time after *delay* passed. 
            3. The 'is_awake' is set to True 
                (can be set True by calling self.wake_up or self.interrupt)
        A *delay* >= 5 sec is recommended as Temperature might be stable for 
        some time after changing the setpoint temperature.
        '''
        
        S = self.settings
                
        if not S['activation']:
            S['activation'] = True
        
        S['is_awake'] = False

        t0 = time.time()
        
        # set temperature settings
        TS = self.app.hardware['lakeshore331'].settings
        if setpoint_T:
            TS['setpoint_T'] = setpoint_T
        ramp_on_state_0 = TS['ramp_on']
        TS['ramp_on'] = False
        
        heater_range0 = TS['heater_range']
        TS['heater_range'] = 'high (50W)'
         
        # self.add_history_event(f'updated setpoint_T={setpoint_T}')
        time.sleep(delay)
        
        # wait 
        while time.time() - t0 < timeout:
            pct = 100 * ((timeout - (time.time() - t0)) / timeout)
            self.set_progress(pct)
            print(self.name, 'setpoint_T', setpoint_T,
                  'stabilization, press wake_up or wait',
                  timeout - (int(time.time() - t0)), 'sec')
            if S['is_awake']:
                break
            if S['is_std_stable']:
                break
            time.sleep(S['update_period'])
        S['is_awake'] = True
            
        self.reset()
        time.sleep(0.2)

        # run measurements
        if measurements:
            if not hasattr(measurements, '__getitem__'):
                measurements = [measurements]
            for measure in measurements:
                time.sleep(0.2)
                if self.interrupt_measurement_called:
                    break
                print(self.name, f'started {measure.name}')
                # self.add_history_event(f'started {measure.name}')
                print(self.name, f'added event {measure.name}')
                self.start_nested_measure_and_wait(measure, nested_interrupt=False)
            
        # save lakeshore data
        self.set_history_end()    
        TS['ramp_on'] = ramp_on_state_0
        TS['heater_range'] = heater_range0
        
    def do_while(self, Tstart=None, Tstop=350, ToDos=[],
                        ramp_rate=None, timeout=30 * 60):
        """
        MAYBE UNSTABLE
        when stable at setpoint_T=*Tstart*, runs *ToDos* repeatedly until one of the following criterion is met:
            - lakeshore measurement interrupted
            - timeout passed
            - Tstop is reached
            
            
        *ToDos* is a list containing:
            - type Measurement object
            - ("lq_path", value)
        """
        TS = self.app.hardware['lakeshore331'].settings
        
        if Tstart:
            self.queue_measurements(Tstart, [])
        else:
            Tstart = TS[f'T_{TS["control_input"]}']
        
        if ramp_rate != None:
            
            TS['setpoint_T'] = Tstop
            TS["ramp_rate"] = ramp_rate
            TS["ramp_on"] = True
        else:
            TS['heater_range'] = 'off' 

        t0 = time.time()
        
        self.settings['is_awake'] = False

        BREAK = False        
        
        while not BREAK:
            for item in ToDos:
                
                self.reset()
                print(self.name, item)
                
                if time.time() - t0 > timeout:
                    self.add_history_event('exit due to timeout')
                    BREAK = True
                    break
                
                elif self.interrupt_measurement_called or self.settings['is_awake']:
                    self.add_history_event('exit: measure interrupted')
                    BREAK = True
                    break
                
                # elif not TS["is_ramping"]:
                #    self.add_history_event('exit ramping False')
                #    BREAK = True
                #    break
                
                if hasattr(item, 'run'):
                        self.add_history_event(f'started {item.name}')
                        self.start_nested_measure_and_wait(item, False)

                elif hasattr(item, '__getitem__'):
                    if len(item) == 2:
                        path, value = item
                        self.app.lq_path(path).update_value(value)
                        self.add_history_event(f'set {path}={value}')
                        
                T = TS[f'T_{TS["control_input"]}']
                pct = (1 - (T - Tstart) / (Tstop - Tstart)) * 100
                self.set_progress(pct)
                if pct >= 100:
                    self.add_history_event(f'exit T_{TS["control_input"]} reached Tstop={Tstop}')
                    BREAK = True
                    break

                time.sleep(0.1)
                
        self.settings['is_awake'] = True

        self.set_history_end()    
