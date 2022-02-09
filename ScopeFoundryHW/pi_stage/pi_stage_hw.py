from ScopeFoundry import HardwareComponent
from collections import OrderedDict
from ScopeFoundry.helper_funcs import sibling_path
import time
from pipython import GCSDevice
from pipython.interfaces.gcsdll import GCSDll


import threading

default_axes = OrderedDict(
    [(1,'x'), (2,'y'), (3,'z')])

class PIStage(HardwareComponent):
    
    name = 'pi_stage'
    
    
    def __init__(self, app, debug=False, name=None , axes =default_axes):
        self.axes = axes
        
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    
    def setup(self):
        
        self.settings.New('port', dtype=str, initial='USB:114053980')
        
        
        for ax_num, ax_name in self.axes.items():
            
            self.settings.New(ax_name + "_position", dtype=float, 
                              unit='um', si=False, spinbox_decimals=3,
                              ro=True)

            self.settings.New(ax_name + "_target", dtype=float, 
                              unit='um', si=False, spinbox_decimals=3,
                              ro=False)
            
            self.settings.New(ax_name + '_servo', dtype=bool, ro=False)
            
            self.settings.New(ax_name + "_velocity", dtype=float, ro=False,
                              si=False, spinbox_decimals=3, unit='um/s')
    
            self.settings.New(ax_name + "_on_target", dtype=bool, ro=True)
    
    
    
    
    def connect(self):
        S = self.settings
        import os

        #dll_path = os.path.normpath(sibling_path(__file__, "PI_GCS2_DLL_x64.dll"))
        #print(dll_path)
        self.gcs = GCSDevice()#gcsdll=dll_path)
        time.sleep(0.1)
        if S['port'].startswith('USB:'):
            ser_num = S['port'].split(':')[-1]
            #print(ser_num)
            self.gcs.ConnectUSB(ser_num)
            print(self.gcs.qIDN())
        else:
            raise ValueError("Port of undefined type {}".format(S['port']))
        
        for ax_num, ax_name in self.axes.items():
            
            lq = S.get_lq(ax_name + "_position")
            lq.connect_to_hardware(
                read_func = lambda n=ax_num: self.gcs.qPOS()[str(n)]
                )
            lq.read_from_hardware()
            
            lq = S.get_lq(ax_name + "_target")
            lq.connect_to_hardware(
                read_func  = lambda n=ax_num: self.gcs.qMOV()[str(n)],
                write_func = lambda new_target, n=ax_num: self.gcs.MOV(n, new_target)
                )
            lq.read_from_hardware()
            
            lq = S.get_lq(ax_name + "_servo")
            lq.connect_to_hardware(
                read_func  = lambda n=ax_num: self.gcs.qSVO()[str(n)],
                write_func = lambda enable, n=ax_num: self.gcs.SVO(n, enable )
                )
            lq.read_from_hardware()
            
            lq = S.get_lq(ax_name + "_on_target")
            lq.connect_to_hardware(
                read_func  = lambda n=ax_num: self.gcs.qONT()[str(n)],
                )
            lq.read_from_hardware()
            
            lq = S.get_lq(ax_name + "_velocity")
            lq.connect_to_hardware(
                read_func  = lambda n=ax_num: self.gcs.qVEL()[str(n)],
                write_func = lambda new_vel, n=ax_num: self.gcs.VEL(n, new_vel )
                )
            lq.read_from_hardware()
        
        
        self.update_thread_interrupted = False
        #self.update_thread = threading.Thread(target=self.update_thread_run)
        #self.update_thread.start()
        
        #self.update_timer = QtCore.QTimer()
        #self.update_timer.timeout.connect(self.on_update_timer)
        #self.update_timer.start(100)

    

    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        #if hasattr(self, 'update_timer'):
        #    self.update_timer.stop()
        if hasattr(self, 'update_thread'):
            self.update_thread_interrupted = True
            self.update_thread.join(timeout=1.0)
            del self.update_thread
            
        if hasattr(self, 'gcs'):
            self.gcs.close()
            del self.gcs
        
    def update_thread_run(self):
        while not self.update_thread_interrupted:
            for ax_num, ax_name in self.axes.items():
                self.settings.get_lq(ax_name + "_position").read_from_hardware()
                self.settings.get_lq(ax_name + "_on_target").read_from_hardware()
            time.sleep(0.1)
    