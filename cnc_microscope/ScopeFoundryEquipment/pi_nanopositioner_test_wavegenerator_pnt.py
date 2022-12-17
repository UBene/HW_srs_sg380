from __future__ import division
import ctypes

import time
from pipython import GCSDevice, pitools
import os
import platform
import numpy as np
#from _pytest.skipping import _get_pos
from dis import dis

SLOW_STEP_PERIOD = 0.20  # units are seconds


class PINanopositioner(object):

    def __init__(self, debug=False):
        self.debug = debug
        
        CONTROLLERNAME = 'E-727'
        refmode = None
        deviceaxes = ('1', '2', '3')
        self.num_axes = 3
        self.sleeptime = 0.01               # sleep time: 0.01 sec / (um /sec)
        self.pidevice = GCSDevice()
        ID = self.pidevice.EnumerateUSB(CONTROLLERNAME)

        self.pidevice.ConnectUSB(ID[0])

        if self.debug: print("Device ID: ", ID)

        if not ID:
            print ("PINanopositioner failed to grab device handle ", ID)

        if self.debug: print('connected: {}'.format(self.pidevice.qIDN().strip()))

        #######################################################
        if self.pidevice.HasINI():
            self.pidevice.INI()
        if self.pidevice.HasONL():
            self.pidevice.ONL(deviceaxes, [True] * 3)
        pitools.stopall(self.pidevice)
        self.pidevice.SVO(deviceaxes, (True, True, True))
        self.pidevice.VCO(('1', '2', '3'), (False, False, False))
        pitools.waitontarget(self.pidevice, axes=deviceaxes)
        referencedaxes = []
        # if refmode:
        #    refmode = refmode if isinstance(refmode, (list, tuple)) else [refmode] * self.pidevice.numaxes
        #    refmode = refmode[:pidevice.numaxes]
        #    reftypes = set(refmode)
        #    for reftype in reftypes:
        #        if reftype is None:
        #            continue
        #        axes = [pidevice.axes[i] for i in range(len(refmode)) if refmode[i] == reftype]
        #        getattr(pidevice, reftype.upper())(axes)
        #        referencedaxes += axes
        # pitools.waitontarget(self.pidevice, axes=referencedaxes)

        self.cal = list(self.pidevice.qTMX().values())
        # print("index self.cal", self.cal[0], self.cal[1], self.cal[2])
        print("self.cal", self.cal)
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

        # print("xyz",x, y, z)

        if x is not None:
            assert 0.0 <= x <= self.cal_X
            self.pidevice.MOV(["1"], [x])
        if y is not None:
            assert 0.0 <= y <= self.cal_Y
            self.pidevice.MOV(["2"], [y])
        if z is not None:
            assert 0.0 <= z <= self.cal_Z
            self.pidevice.MOV(["3"], [z])

        pitools.waitontarget(self.pidevice, ["1", "2", "3"])
        # time.sleep(0.05)

        # self.get_pos()
        # self.x_pos = x
        # self.y_pos = y
        # self.z_pos = z

    def set_pos_fast(self, x=None, y=None, z=None):
        '''
        x -> axis 1
        y -> axis 2
        z -> axis 3
        '''
        # print("xyz",x, y, z)

        if x is not None:
            assert 0.0 <= x <= self.cal_X
            self.pidevice.MOV(["1"], [x])
        if y is not None:
            assert 0.0 <= y <= self.cal_Y
            self.pidevice.MOV(["2"], [y])
        if z is not None:
            assert 0.0 <= z <= self.cal_Z
            self.pidevice.MOV(["3"], [z])

        # pitools.waitontarget(self.pidevice, ["1","2","3"])
        time.sleep(0.05)

        # self.get_pos()
        # self.x_pos = x
        # self.y_pos = y
        # self.z_pos = z

    def set_pos_ax_slow(self, pos, axis):
        if self.debug: print ("set_pos_slow_ax ", pos, axis)
        
        assert 1 <= axis <= self.num_axes
        assert 0 <= pos <= self.cal[axis - 1]
        self.pidevice.MOV(str(axis), pos)
        # pitools.waitontarget(self.pidevice, str(axis))
        time.sleep(0.05)

    def get_pos(self):
        pos = self.pidevice.qPOS(('1', '2', '3'))
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

    def set_vel_control(self, xvc = None, yvc = None, zvc = None):
        
        self.pidevice.VCO(('1', '2', '3'), (xvc, yvc, zvc))
    
    def set_VCO_flag(self, flag):
        
        self.vel_control = flag
    
    
    def set_vel(self, xv=None, yv=None, zv=None):
        self.pidevice.VEL(('1', '2', '3'), (xv, yv, zv))
    
    def jog(self, xv, yv, zv):
        self.pidevice.JOG(('1', '2', '3'), (xv, yv, zv))
    
    def qtcv(self):
        vel_info = self.pidevice.qTCV()
        print(vel_info)
    
    def jogging(self, xt = None, yt = None, zt = None,
                xv = None, yv = None, zv = None):

        '''
        let stage move from current pos to (xt, yt, zt) with the velocity component (xv, yv, zv)
        
        xt, yt, zt -> target position(xt, yt, zt)
        xv, yv, zv -> set velocity component(Vx, Vy, Vz)
        '''
        # Get the current position of the stage
        pos = self.pidevice.qPOS(('1', '2', '3'))
        x1 = pos['1']
        y1 = pos['2']
        z1 = pos['3']
        
        # Calculate the distance, average velocity, estimated moving time 
        dis = np.sqrt((xt-x1)**2 + (yt-y1)**2 + (zt-z1)**2)
        avg_vel = np.sqrt(xv**2 + yv**2 + zv**2)
        t = dis / avg_vel
        t = t + self.sleeptime * avg_vel       
        
        # Turn on the velocity control
        self.pidevice.VCO(('1', '2', '3'), (True, True, True))
        # Set constant velocity
        self.pidevice.VEL(('1', '2', '3'), (xv, yv, zv))
        
        assert 0.0 <= xt <= self.cal_X
        self.pidevice.MOV(["1"], [xt])
        assert 0.0 <= yt <= self.cal_Y
        self.pidevice.MOV(["2"], [yt])
        assert 0.0 <= zt <= self.cal_Z
        self.pidevice.MOV(["3"], [zt])
        
        if t == NaN:
            t = 0
        
        
        time.sleep(t)
        #velocity = self.pidevice.qVEL(('1', '2', '3'))
        #print(velocity)
        #time.sleep(0.5*t)        
        # Turn OFF the velocity control
        self.pidevice.VCO(('1', '2', '3'), (False, False, False))
    
    def set_vel_xy(self, vxy, xt, yt):
        
        '''
        calculate the velocity components (vx, vy) with vxy and target position (xt, yt)
        
        vxy     -> ordered horizontal velocity (in x-y plane)  
        xt/yt   -> (x/y target)
        '''
        
        # Get the current position of the stage
        pos = self.pidevice.qPOS(('1', '2'))
        x1 = pos['1']
        y1 = pos['2']
        dis = np.sqrt((xt-x1)**2 + (yt-y1)**2)
        vx = np.abs(vxy * (xt-x1)/dis)
        vy = np.abs(vxy * (yt-y1)/dis)
        
        return (vx, vy)
    
    
    def z_comp(self, x_r, y_r, vx, vy, xt, yt):
        
        '''
        input the x, y axis parameter
        x_r/y_r -> (x/y-axis ratio)
        x/y     -> velocity 
        xt/yt   -> (x/y target)
        
        return the compensation parameter of z axis
        zt -> z target
        vz -> z velocity
        '''
        pos = self.pidevice.qPOS(('1', '2', '3'))
        x1 = pos['1']
        y1 = pos['2']
        z1 = pos['3']
        x_d = (xt - x1) / np.abs(xt - x1)        # moving direction of x, y
        y_d = (yt - y1) / np.abs(yt - y1)
        
        dz = (xt - x1) * x_r + (yt -y1) * y_r    # compensated z target
        zt = z1 + dz
        
        vzx = x_d * x_r * vx                     # compensated z velocity
        vzy = y_d * y_r * vy
        vz = vzx + vzy                           
        return(zt, np.abs(vz))
        
    
    def qVEL(self):
        
        # return the current assigned velocity of all 3 axis
        
        velocity = self.pidevice.qVEL(('1', '2', '3'))
        self.x_vel = velocity['1']
        self.y_vel = velocity['2']
        self.z_vel = velocity['3']
        
        return (self.x_vel, self.y_vel, self.z_vel)
        
    
    def readwavedata(self,DATAFILE):
        """Read DATAFILE, must have a column for each wavetable.
        @return : Datapoints as list of lists of values.
        """
        print('read wave points from file {}'.format(DATAFILE))
        data = None
        with open(DATAFILE) as datafile:
            for line in datafile:
                items = line.strip().split()
                if data is None:
                    print('found {} data columns in file'.format(len(items)))
                    data = [[] for _ in range(len(items))]
                for i in range(len(items)):
                    data[i].append(items[i])
        return data
  
    
if __name__ == '__main__':
    print ("PI nanopositioner test")
    
    NUMCYLES = [1,1]  # number of cycles for wave generator output
    TABLERATE = 10  # duration of a wave table point = servo cycle time * tablerate
    DATAFILE = r'wavegenerator_pnt.txt'
    
    nanodrive = PINanopositioner(debug=True)
    print(len(nanodrive.pidevice.axes[:2]))
    
    wavedata = nanodrive.readwavedata(DATAFILE)
    #print(len(wavedata))
    
    axes = nanodrive.pidevice.axes[:len(wavedata)]
    assert len(wavedata) == len(axes), 'this sample requires {} connected axes'.format(len(wavedata))
    wavetables = (1,2)
    #print(wavetables)
    wavegens = (1,2)
    if nanodrive.pidevice.HasWCL():  # you can remove this code block if your controller does not support WCL()
        print('clear wave tables {}'.format(wavetables))
        nanodrive.pidevice.WCL(wavetables)
    for i, wavetable in enumerate(wavetables):
        print('write wave points of wave table {} and axis {}'.format(wavetable, axes[i]))
        pitools.writewavepoints(nanodrive.pidevice, wavetable, wavedata[i], bunchsize=10)
    if nanodrive.pidevice.HasWSL():  # you can remove this code block if your controller does not support WSL()
        print ('connect wave tables {} to wave generators {}'.format(wavetables, wavegens))
        nanodrive.pidevice.WSL(wavegens, wavetables)
    if nanodrive.pidevice.HasWGC():  # you can remove this code block if your controller does not support WGC()
        print('set wave generators {} to run for {} cycles'.format(wavegens, NUMCYLES))
        nanodrive.pidevice.WGC(wavegens, NUMCYLES)
    if nanodrive.pidevice.HasWTR():  # you can remove this code block if your controller does not support WTR()
        print('set wave table rate to {} for wave generators {}'.format(TABLERATE, wavegens))
        nanodrive.pidevice.WTR(0, [TABLERATE], 0)
    startpos = [wavedata[i][0] for i in range(len(wavedata))]
    print('move axes {} to start positions {}'.format(axes, startpos))
    nanodrive.pidevice.MOV(axes, startpos)
    pitools.waitontarget(nanodrive.pidevice, axes)
    print('start wave generators {}'.format(wavegens))
    nanodrive.pidevice.WGO(wavegens, mode=[1] * len(wavegens))
    while any(list(nanodrive.pidevice.IsGeneratorRunning(wavegens).values())):
        print ('.'),
        time.sleep(1.0)
    print('\nreset wave generators {}'.format(wavegens))
    nanodrive.pidevice.WGO(wavegens, mode=[0] * len(wavegens))
    print('done')

    print('done')
       
        