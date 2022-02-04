from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import logging

logging.basicConfig(level='DEBUG')  # , filename='m3_log.txt')
# logging.getLogger('').setLevel(logging.WARNING)
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)
logging.getLogger('pyvisa').setLevel(logging.WARNING)


class Microscope(BaseMicroscopeApp):

    name = 'generic_microscope'

    def setup(self):

        print("Adding Hardware Components")

        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW
        self.add_hardware_component(ThorlabsPowerMeterHW(self))
        
        print("Adding Measurement Components")

        from ScopeFoundryHW.thorlabs_powermeter import PowerMeterOptimizerMeasure
        self.add_measurement(PowerMeterOptimizerMeasure(self))
        
    def setup_ui(self):
        '''sets up a quickbar'''
        Q = self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'quickbar.ui')))
        
        # Power wheel
        n = power_wheel_hardware_name = 'power_wheel'
        if n in self.hardware:
            PW = self.hardware[n]
            PWS = PW.settings

            def go_to(pos, PWS=PWS):
                PWS['target_position'] = pos

            Q.power_wheel_0_pushButton.clicked.connect(lambda x:go_to(0))
            Q.power_wheel_90_pushButton.clicked.connect(lambda x:go_to(90))
            Q.power_wheel_180_pushButton.clicked.connect(lambda x:go_to(180))
            Q.power_wheel_270_pushButton.clicked.connect(lambda x:go_to(270))
            Q.power_wheel_jog_forward_pushButton.clicked.connect(lambda x:PW.jog_forward)
            #PWS._jog_step.connect_to_widget(Q.power_wheel_jog_doubleSpinBox)
            #Q.power_wheel_jog_backward_pushButton.clicked.connect(lambda x:PW.jog_backward)
            PWS.position.connect_to_widget(Q.power_wheel_position_label)
            #PWS.target_position.connect_to_widget(Q.power_wheel_target_position_doubleSpinBox)
        else:
            Q.power_wheel_groupBox.setVisible(False)
        
        # Power meter
        n = 'thorlabs_powermeter'
        if n in self.hardware:
            PM = self.hardware[n]
            PMS = self.hardware.thorlabs_powermeter.settings
            PMS.connected.connect_to_widget(Q.power_meter_connected_checkBox)
            PMS.wavelength.connect_to_widget(Q.power_meter_wavelength_doubleSpinBox)        
            # PMS.power.connect_to_widget(Q.power_meter_power_label)
            from ScopeFoundry.helper_funcs import replace_widget_in_layout
            import pyqtgraph as pg
            W = replace_widget_in_layout(Q.power_meter_power_label, pg.widgets.SpinBox.SpinBox())
            PMS.power.connect_to_widget(W)
            if 'powermeter_optimizer' in self.measurements:
                M = self.measurements['powermeter_optimizer']
                M.settings.activation.connect_to_pushButton(Q.power_meter_activation_pushButton)
                Q.power_meter_show_ui_pushButton.clicked.connect(M.show_ui)
        else:
            Q.power_meter_groupBox.setVisible(False)

    def link_2D_scan_params(self, parent_scan_name='apd_asi',
                            children_scan_names=['hyperspec_asi', 'asi_trpl_2d_scan']):
        '''call this function to link equivalent settings of children scans to a parent scan'''
        lq_names = ['h0', 'h1', 'v0', 'v1', 'Nh', 'Nv']

        parent_scan = self.measurements[parent_scan_name]
        for scan in children_scan_names:
            child_scan = self.measurements[scan]
            for lq_name in lq_names:
                master_scan_lq = parent_scan.settings.get_lq(lq_name)
                child_scan.settings.get_lq(lq_name).connect_to_lq(master_scan_lq)
                
                
if __name__ == '__main__':
    import sys
    app = Microscope(sys.argv)
    app.settings_load_ini('defaults.ini')
    #app.load_window_positions_json(r'window_positions.json')
    sys.exit(app.exec_())
