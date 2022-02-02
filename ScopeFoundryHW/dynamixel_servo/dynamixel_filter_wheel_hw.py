'''
Created on Apr 26, 2021

@author: Benedikt Ursprung
'''
from ScopeFoundry.hardware import HardwareComponent
import time


class DynamixelFilterWheelHW(HardwareComponent):
    
    name = 'filter_wheel'
    
    def __init__(self, app, debug=False, name=None,
                 named_positions={'Other':[0, 'red']},  # {'name':pos} or {'name',[pos,'color']} are valid.
                 # color can be https://www.w3.org/TR/SVG11/types.html#ColorKeywords or more 
                 positions_in_degrees=False,
                 release_at_target=False
                 ):
        
        self.colors = []
        self.named_positions = {}
        
        for pos, _val in named_positions.items():
            if hasattr(_val, '__len__'):
                val = _val[0]
                self.colors.append(_val[1])
            else:
                val = _val
                
            if positions_in_degrees:
                self.named_positions.update({pos:int(val * 4096 / 360)})   
            else:
                self.named_positions.update({pos:int(val)})                 

        self.release_at_target = release_at_target
                           
        HardwareComponent.__init__(self, app, debug=debug, name=name)
        
    def setup(self):
        
        S = self.settings
        S.New('dynamixel_hw', initial='dynamixel_servos', dtype=str)
        S.New('servo_name', initial=self.name, dtype=str)
        S.New('offset', initial=0, unit='steps', dtype=int)
        S.New('position', unit='steps', dtype=int)

        S.New('target_position', unit='steps', dtype=int)
        S.New('release_at_target', dtype=bool, initial=self.release_at_target, colors=['coral','lime'])
        S.New('profile_velocity', int, initial=180)  # 0 is fastest, 255 2nd fastest ... 1 is slowest 
        
        if type(self.named_positions) == dict:
            self.settings.New('named_position', dtype=str,
                              initial=list(self.named_positions.keys())[0],
                              choices=tuple(self.named_positions.keys()),
                              colors=self.colors)
            
            for name, pos in self.named_positions.items():
                self.add_operation('Goto ' + name, lambda name=name: self.settings.named_position.update_value(name))
                
        self.add_operation('set offset', self.set_offset)
        
    def connect(self):
        
        S = self.settings
        servos = self.servos = self.app.hardware[S['dynamixel_hw']]
        servos.settings['connected'] = True

        # set mode to extended_position
        servos.settings[S['servo_name'] + '_torque'] = False
        servos.settings[S['servo_name'] + '_profile_velocity'] = S['profile_velocity']
        servos.settings[S['servo_name'] + '_mode'] = 4
        servos.settings[S['servo_name'] + '_torque'] = True  # unexpected behavior if not enabled
                
        S.target_position.connect_lq_scale(
            servos.settings.get_lq(S['servo_name'] + '_target_position'), scale=1)  # NOTE, not disconnected on disconnect       

        S.position.connect_lq_scale(
            servos.settings.get_lq(S['servo_name'] + '_position'), scale=1)  # NOTE, not disconnected on disconnect       

        S.profile_velocity.connect_lq_scale(
            servos.settings.get_lq(S['servo_name'] + '_profile_velocity'), scale=1)  # NOTE, not disconnected on disconnect
          
        if 'named_position' in self.settings:
            self.settings.named_position.connect_to_hardware(
                read_func=self.read_named_position,
                write_func=self.goto_named_position
                )
            
        self.read_from_hardware()
            
    def read_named_position(self):
        pos = self.settings['position']

        def closest(lst, K):
            return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]

        closest_value = closest(list(self.named_positions.values()), pos)
        return {v: k for k, v in self.named_positions.items()}[closest_value]
        
    def disconnect(self):
        pass
        
    def goto_named_position(self, name):
        S = self.settings
        if name != 'Other':
            self.servos.settings[S['servo_name'] + '_torque'] = True
            self.settings['target_position'] = self.named_positions[name] + S['offset']

            if S['release_at_target']:
                time.sleep(0.1)
                moving_lq = self.servos.settings.get_lq(S['servo_name'] + '_moving')
                while moving_lq.read_from_hardware():
                    time.sleep(0.05)
                time.sleep(0.1)
                self.servos.settings[S['servo_name'] + '_torque'] = False
            
    def set_offset(self):
        current_position = self.servos.settings[self.settings['servo_name'] + '_position']
        self.settings['offset'] = current_position
        
