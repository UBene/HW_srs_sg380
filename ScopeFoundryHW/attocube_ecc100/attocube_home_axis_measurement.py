from ScopeFoundry import Measurement
import time

class AttoCubeHomeAxisMeasurement(Measurement):


    name = 'attocube_home_axis'
    
    
    def setup(self):
        
        self.settings.New('hw_name', dtype=str, initial='attocube_xyz_stage')
        self.settings.New('axis_name', dtype=str, initial='x')
        self.settings.New('safe_travel_dir', dtype=int, initial=1, choices=[('+', +1), ('-', -1)])
        
        
    def run(self):
        
        assert self.settings['safe_travel_dir'] in (+1,0,-1)
        
        hw = self.app.hardware[self.settings['hw_name']]
        S = hw.settings
        
        ax = self.settings['axis_name']
        
        print(hw.name, 'homing axis', ax, self.settings['safe_travel_dir'])
        
        ## Clear reference
        hw.reset_axis_by_name(ax)
        ## read position and status
        hw.read_from_hardware()
        
        ## Turn off closed loop mode        
        S[ax + "_enable_closedloop"] = False
        ## set target to reference position (0)
        S[ax + "_target_position"] = 0

        ## enable auto_reference_update and reset
        S[ax + "_auto_reference_update"] = True
        S[ax + "_auto_reference_reset"] = True
        ## enable EOT stop
        S[ax + "_eot_stop"] = True

        ## read position and status
        hw.read_from_hardware()
        

        try:        
            ## move in safe direction
            print(hw.name, 'homing axis move in safe dir', ax, self.settings['safe_travel_dir'])
            S[ax + "_continuous_motion"] = self.settings['safe_travel_dir']
    
            while 1:
                time.sleep(0.05)
                ## read position and status
                hw.read_from_hardware()
                
                ## User interrupts homing procedure
                if self.interrupt_measurement_called:
                    print(hw.name, 'homing axis interrupted', ax)
                    # stop motion
                    S[ax + "_continuous_motion"] = 0
                    S[ax + "_enable_closedloop"] = False 
                    hw.read_from_hardware()
                    break
                ## check if reference found, if so done
                if S[ax + "_reference_found"]:
                    print(hw.name, 'homing axis ref found', ax)
                    # stop motion
                    S[ax + "_continuous_motion"] = 0          
                    ## set target to reference position (0)
                    S[ax + "_target_position"] = 0
                    ## enable closed loop                
                    S[ax + "_enable_closedloop"] = True
                    break
                ## check if eot and reverse if so reverse direction
                if S[ax + '_eot_forward'] or S[ax + '_eot_back']:
                    print(hw.name, 'homing axis eot found, reversing', ax)
                    # stop motion
                    S[ax + "_continuous_motion"] = 0   
                    time.sleep(0.1)
                    # reverse travel direction
                    S[ax + "_continuous_motion"] = -1*self.settings['safe_travel_dir']
                    time.sleep(0.01)
                    
        except Exception as err:
            S[ax + "_continuous_motion"] = 0
            S[ax + "_enable_closedloop"] = False
            raise err
