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
        t = 0
        dis = np.sqrt((xt-x1)**2 + (yt-y1)**2 + (zt-z1)**2)
        avg_vel = np.sqrt(xv**2 + yv**2 + zv**2)
        t = dis / avg_vel
        t = t + self.sleeptime
        
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
        
        if np.isnan(t):
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
        if xt == x1:                            # moving direction of x, y
            x_d = 0
        else:
            x_d = (xt - x1) / np.abs(xt - x1)

        if yt == y1:
            y_d = 0
        else:
            y_d = (yt - y1) / np.abs(yt - y1)

        #x_d = (xt - x1) / np.abs(xt - x1)       # moving direction of x, y
        #y_d = (yt - y1) / np.abs(yt - y1)
        
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
        


if __name__ == '__main__':
    print ("PI nanopositioner test")

    nanodrive = PINanopositioner(debug=True)
    nanodrive.set_vel_control(False, False, False)
    nanodrive.set_pos_fast(100, 100, 100)
    nanodrive.set_vel_control(True, True, True)
    #nanodrive.set_vel(5, 5, 0)
    #xv = 10
    #yv = 10
    zv = 0
    vxy = 2
    
    #nanodrive.jog(0.01, 0, 0)
    i = 1
    ex = 0
    ey = 0
    time_start = time.time()
    # for x,y in [ (0,0), (10,10), (30,30), (50,50), (50,25), (50,0)]:
    # for x,y,z in [ (30,1,1), (30,10,10), (30,30,30), (30,50,60), (30,25,60), (30,1,1)]:
    #for x, y, z in [(50, 50, 19), (20, 90, 27), (90, 20, 22), (10, 10, 22) ]:
    #for x, y, z in [(100, 50, 25), (50, 100, 25) ]:
    for x, y in [(100, 110), (110, 110),(110, 120),(120, 120),(120, 130) ]:
        #print ("moving to ", x, y, z)
        print ("moving to ", x, y)
        xv, yv = nanodrive.set_vel_xy(vxy, x, y)
        
        z, zv = nanodrive.z_comp(-0.01, -0.03, xv, yv, x, y)
        print(z, zv)
        #print(xv,yv)
        nanodrive.jogging(x, y, z, xv, yv, zv)
        #nanodrive.qtcv()
        #time.sleep(10)
        x1, y1, z1 = nanodrive.get_pos()
        ex = (np.abs(x1-x) + i * ex) / (i+1)
        ey = (np.abs(y1-y) + i * ey) / (i+1)
        i = i + 1 
        print ("moved to ", x1, y1, z1)
    time_end = time.time()
    print("Calculation time: {}".format(time_end - time_start))
    print("Sleep Time: ", nanodrive.sleeptime, " sec")
    print("Error in X: ", ex * 1000 , "nm" )
    print("Error in Y: ", ey * 1000 , "nm" )
    #nanodrive.set_vel_control(False, False, False)
    # nanodrive.close()

