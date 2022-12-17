from __future__ import division
import ctypes

import time
from pipython import GCSDevice, pitools
import os
import platform
import numpy as np


SLOW_STEP_PERIOD = 0.050  #units are seconds        

class PINanopositioner(object):

    def __init__(self, debug=False):
        self.debug = debug
        
        CONTROLLERNAME = 'E-727'
        refmode =None
        deviceaxes = ('1','2','3')
        self.num_axes = 3
        
        self.pidevice = GCSDevice()
        ID = self.pidevice.EnumerateUSB(CONTROLLERNAME)
        
        self.pidevice.ConnectUSB(ID[0])
        

        if self.debug: print( "Device ID: ", ID)

        if not ID:
            print ("PINanopositioner failed to grab device handle ", ID)

        if self.debug: print('connected: {}'.format(self.pidevice.qIDN().strip()))
        
        #######################################################
        if self.pidevice.HasINI():
            self.pidevice.INI()
        if self.pidevice.HasONL():
            self.pidevice.ONL(deviceaxes, [True] * 3)
        pitools.stopall(self.pidevice)
        self.pidevice.SVO(deviceaxes,(True, True, True))
    
        pitools.waitontarget(self.pidevice, axes=deviceaxes)
        referencedaxes = []
        #if refmode:
        #    refmode = refmode if isinstance(refmode, (list, tuple)) else [refmode] * self.pidevice.numaxes
        #    refmode = refmode[:pidevice.numaxes]
        #    reftypes = set(refmode)
        #    for reftype in reftypes:
        #        if reftype is None:
        #            continue
        #        axes = [pidevice.axes[i] for i in range(len(refmode)) if refmode[i] == reftype]
        #        getattr(pidevice, reftype.upper())(axes)
        #        referencedaxes += axes
        #pitools.waitontarget(self.pidevice, axes=referencedaxes)
            
        self.cal = list(self.pidevice.qTMX().values())
        print("self.cal",self.cal)
        self.cal_X = self.cal[0]    
        self.cal_Y = self.cal[1]
        self.cal_Z = self.cal[2]
        print(self.cal_X, self.cal_Y, self.cal_Z)
        #################################################
        
    
    def set_pos_slow(self, x=None, y=None, z=None):
        '''
        x -> axis 1
        y -> axis 2
        z -> axis 3
        '''
        
        #print("xyz",x, y, z)

        
        if x is not None:
            assert 0.0 <= x <= self.cal_X
            self.pidevice.MOV(["1"], [x])      
        if y is not None:
            assert 0.0 <= y <= self.cal_Y
            self.pidevice.MOV(["2"], [y])
        if z is not None:
            assert 0.0 <= z <= self.cal_Z
            self.pidevice.MOV(["3"], [z])

        pitools.waitontarget(self.pidevice, ["1","2","3"])
        #time.sleep(0.05)

        #self.get_pos()
        #self.x_pos = x
        #self.y_pos = y
        #self.z_pos = z
        

    
    def set_pos_fast(self, x=None, y=None, z=None):
        '''
        x -> axis 1
        y -> axis 2
        z -> axis 3
        '''
        #print("xyz",x, y, z)

        
        if x is not None:
            assert 0.0 <= x <= self.cal_X
            self.pidevice.MOV(["1"], [x])      
        if y is not None:
            assert 0.0 <= y <= self.cal_Y
            self.pidevice.MOV(["2"], [y])
        if z is not None:
            assert 0.0 <= z <= self.cal_Z
            self.pidevice.MOV(["3"], [z])

        #pitools.waitontarget(self.pidevice, ["1","2","3"])
        time.sleep(0.05)

        #self.get_pos()
        #self.x_pos = x
        #self.y_pos = y
        #self.z_pos = z
    
    def set_pos_ax_slow(self, pos, axis):
        if self.debug: print ("set_pos_slow_ax ", pos, axis)
        assert 1 <= axis <= self.num_axes
        assert 0 <= pos <= self.cal[axis]
        
        self.pidevice.MOV(str(axis), pos)
        #pitools.waitontarget(self.pidevice, str(axis))
        time.sleep(0.05)         
    

    def get_pos(self):
        pos = self.pidevice.qPOS(('1','2','3'))
        self.x_pos = pos['1']
        self.y_pos = pos['2']
        self.z_pos = pos['3']
        
        return (self.x_pos, self.y_pos, self.z_pos)
    
    def get_pos_ax(self, axis):
        pos_dict = self.pidevice.qPOS(str(axis))
        pos = pos_dict[str(axis)]
        if self.debug: print ("get_pos_ax", axis, pos)
        return pos
    
    def close(self):
        self.pidevice.CloseConnection()
        
if __name__ == '__main__':
    print ("PI nanopositioner test")
    
    nanodrive = PINanopositioner(debug=True)
    time_start = time.time()
    #for x,y in [ (0,0), (10,10), (30,30), (50,50), (50,25), (50,0)]:
    #for x,y,z in [ (30,1,1), (30,10,10), (30,30,30), (30,50,60), (30,25,60), (30,1,1)]:
    for x,y,z in [ (30,1,1), (30.1,1.1,1.1), (30.2,1.2,1.2), (30.3,1.3,1.3), (30.4,1.4,1.4), (30,1,1)]:   
        print ("moving to ", x,y,z)
        nanodrive.set_pos_fast(x,y,z)
        #time.sleep(1)
        x1,y1,z1 = nanodrive.get_pos()
        print ("moved to ", x1, y1,z1)
    time_end = time.time()   
    print("Calculation time: {}".format(time_end - time_start))
    
    #nanodrive.close()
    
