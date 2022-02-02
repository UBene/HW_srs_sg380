from ScopeFoundry.scanning import BaseRaster2DSlowScan
import numpy as np
import time

class ThorlabsStepper2DScan(BaseRaster2DSlowScan):
    
    name = 'thorlabs_stepper_2dscan'
    
    def __init__(self, app):
        BaseRaster2DSlowScan.__init__(self, app, h_limits=(-5,5), v_limits=(-5,5),
                                      h_spinbox_step = 0.010, v_spinbox_step=0.010,
                                      h_unit="mm", v_unit="mm")
        
    def setup(self):
        BaseRaster2DSlowScan.setup(self)
        
        self.settings.New("h_axis", initial="x", dtype=str, choices=("x", "y", "z"))
        self.settings.New("v_axis", initial="z", dtype=str, choices=("x", "y", "z"))

        self.stage = self.app.hardware['thorlabs_stepper_controller']


    def setup_figure(self):
        BaseRaster2DSlowScan.setup_figure(self)
        self.set_details_widget(widget=self.settings.New_UI(include=['h_axis', 'v_axis']))

    def distance_from_target(self):
        S = self.stage.settings
        h = self.settings['h_axis']
        v = self.settings['v_axis']
        
        print(h, v, S[h + '_position'], S[h + '_target_position'], S[v + '_position'], S[v + '_target_position'], )
        
        return np.sqrt(    (S[h + '_position'] - S[h + '_target_position'])**2 
                         + (S[v + '_position'] - S[v + '_target_position'])**2)

    def move_position_start(self, h,v):
        
        #self.interrupt_measurement_called = False
        print('moving!')
        
        if not self.stage.settings['connected']:
            raise IOError("Not connected to thorlabs stepper stage")
        
        h_axis = self.settings['h_axis']
        v_axis = self.settings['v_axis']
        
        print('calculating distance')
        #h_target = self.stage.settings.get_lq(h_axis + "_target_position")
        #h_target.update_value(h)
        #h_target.write_to_hardware()

        #v_target = self.stage.settings.get_lq(v_axis + "_target_position")
        #v_target.update_value(v)
        #v_target.write_to_hardware()
        self.stage.settings[h_axis + "_target_position"] = h
        self.stage.settings[v_axis + "_target_position"] = v
        
        
        
        print(self.name, "move_position", h,v)
        
        # Wait until stage has moved to target
        while True:
            
            #print('waiting')
            time.sleep(0.10)
                
            for ax in [h_axis, v_axis]:
                self.stage.settings.get_lq(ax + "_position").read_from_hardware()
                
            print("distance_from_target", self.distance_from_target())
            #print(self.stage.settings['z_acceleration'])

            
            
            h_done = False
            v_done = False
            
            messages = self.stage.read_message_queue(h_axis)
            for m_type, m_id, m_data in messages:
                if m_type == 'GenericMotor' and m_id == 1: 
                    h_done = True
                    # moving done message
            if len(messages) == 0:
                h_done = True

            messages = self.stage.read_message_queue(v_axis)
            for m_type, m_id, m_data in messages:
                if m_type == 'GenericMotor' and m_id == 1: 
                    v_done = True
            if len(messages) == 0:
                v_done = True
                
#            if self.interrupt_measurement_called:
#                self.stage.stop_all_axes()
#                break

            if self.interrupt_measurement_called:
                h_done = True
                v_done = True
                break


            if self.distance_from_target() < 0.01 and h_done and v_done:
                print('close enough to target')
                time.sleep(0.10)
                break
            
            
#             if (time.time() - t0) > timeout:
#                 raise IOError("AttoCube ECC100 took too long to reach position")
#             time.sleep(0.005)

        print(self.name, "move_position arrived", h,v)

    def post_scan_cleanup(self):
        self.stage.stop_all_axes()
        
    def move_position_slow(self, h,v, dh,dv):
        self.move_position_start(h, v)

    def move_position_fast(self,  h,v, dh,dv):
        self.move_position_slow(h,v,dh,dv)
        
    def update_display(self):
        BaseRaster2DSlowScan.update_display(self)
        
class ThorlabsStepperDelay2DScan(ThorlabsStepper2DScan):
    
    name = 'thorlabs_stepper_delay2d'

    def setup_figure(self):
        ThorlabsStepper2DScan.setup_figure(self)
        self.set_details_widget(
            widget=self.settings.New_UI(include=['h_axis', 'v_axis', 'pixel_time', 'frame_time']))
    
    def scan_specific_setup(self):
        self.settings.pixel_time.change_readonly(False)

    
    def collect_pixel(self, pixel_num, k, j, i):
        time.sleep(self.settings['pixel_time'])

    def update_display(self):
        pass