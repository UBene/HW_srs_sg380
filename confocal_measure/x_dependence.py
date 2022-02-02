'''
Created on Jul 8, 2021

@author: lab
'''
from ScopeFoundry.measurement import Measurement


class XDependence(Measurement):
    
    name = 'x_dependence'
    
    def setup(self):
        self.x = self.settings.New_Range('x')
        
        self.settings.New("x_hw", dtype=str, initial="polarizer")
        self.settings.New("x", dtype=str, initial="position")
        self.settings.New("x_target", dtype=str, initial="position")
        
        
        print('measurements', self.app.measurements.items())
        #self.measurements = list(self.app.measurement_components)
        self.run_lqs = []
        #self.measurements_names = []
        for name in self.app.measurements.keys():
            self.run_lqs.append(self.setting.New('run_'+name, dtype=bool, initial=False))
            
        
        
    def run(self):
        S = self.settings
        x_values = self.x.sweep_array
        x_target_lq = self.app.hardware[S['x_hw']].settings.get_lq(S['x_target'])
        
        
        
        x = x_values
        for j, x in enumerate(x_values):
            if self.interrupt_measurement_called:
                break
            
            
            self.set_progress(100 * (j + 1) / (len(x_values)))            
            x_target_lq.update_value(x)
            
            
            for run_lq,measure in zip(self.run_lqs,self.app.measurements.values()):
                
                if run_lq.val:
                    print('run', measure.val)
            

        

        
        
        