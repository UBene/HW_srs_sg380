import time
from pipython import GCSDevice, pitools
import numpy as np

SLOW_STEP_PERIOD = 0.050  # units are seconds        


class PINanopositioner(object):

    def __init__(self, debug=False):
        self.debug = debug
        
        CONTROLLERNAME = 'E-727'
        refmode = None
        deviceaxes = ('1', '2', '3')
        self.num_axes = 3
        
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
        
        self.cal_X = self.cal[0]    
        self.cal_Y = self.cal[1]
        self.cal_Z = self.cal[2]
        
        #################################################

    def set_max_speed(self, max_speed):
        '''
        Units are in microns/second
        '''
        self.max_speed = float(max_speed)
    
    def get_max_speed(self):
        return self.max_speed
    
    def set_pos_slow(self, x=None, y=None, z=None):
        self.max_speed = 0.1
        '''
        x -> axis 1
        y -> axis 2
        z -> axis 3
        '''
        
        self.set_pos(x, y, z)
        
        x_start, y_start, z_start = self.get_pos()
        
        if x is not None:
            dx = x - x_start
        else:
            dx = 0
        if y is not None: 
            dy = y - y_start
        else:
            dy = 0
        if z is not None:
            dz = z - z_start
        else:
            dz = 0
        
        # Compute the amount of time that will be needed to make the movement.
        dt = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2) / self.max_speed
            
        # Assume dt is in ms; divide the movement into SLOW_STEP_PERIOD chunks
        steps = int(np.ceil(dt / SLOW_STEP_PERIOD))
        x_step = dx / steps
        y_step = dy / steps
        z_step = dz / steps
        
        for i in range(1, steps + 1):
            t1 = time.time()         
            self.set_pos(x_start + i * x_step, y_start + i * y_step, z_start + i * z_step)
            t2 = time.time()
            
            if (t2 - t1) < SLOW_STEP_PERIOD:
                time.sleep(SLOW_STEP_PERIOD - (t2 - t1))
        
        # Update internal variables with current position
        self.get_pos()
        
    # def __del__(self):
    #    self.close()
        
    def close(self):
        # madlib.MCL_ReleaseHandle(self._handle)
        self.pidevice.CloseConnection()

    def move_rel(self, dx, dy, dz=0):
        pass
        # TODO

    def set_pos(self, x, y, z=None):
        assert 0 <= x <= self.cal_X
        assert 0 <= y <= self.cal_Y
        # TODO z-axis is ignored        
        if z is not None:
            assert 0 <= z <= self.cal_Z
        
        self.set_pos_ax(x, 1)
        # madlib.MCL_DeviceAttached(200, self._handle)
        self.set_pos_ax(y, 2)
        if z is not None:
            self.set_pos_ax(z, 3)
        # MCL_DeviceAttached can be used as a simple wait function. In this case
        # it is being used to allow the nanopositioner to finish its motion before 
        # reading its position. (standard 200)
        # madlib.MCL_DeviceAttached(100, self._handle)
        
    def set_pos_ax(self, pos, axis):
        # if self.debug: print ("set_pos_ax ", pos, axis)
        assert 1 <= axis <= self.num_axes
        assert 0 <= pos <= self.cal[axis]
        self.pidevice.MOV(str(axis), pos)
    
    def get_pos_ax(self, axis):
        pos_dict = self.pidevice.qPOS(str(axis))
        pos = pos_dict[str(axis)]
        if self.debug: print ("get_pos_ax", axis, pos)
        return pos
    
    def get_pos(self):
        pos = self.pidevice.qPOS(('1', '2', '3'))
        self.x_pos = pos['1']
        self.y_pos = pos['2']
        self.z_pos = pos['3']
        
        return (self.x_pos, self.y_pos, self.z_pos)
    
    def set_pos_ax_slow(self, pos, axis):
        if self.debug: print ("set_pos_slow_ax ", pos, axis)
        assert 1 <= axis <= self.num_axes
        assert 0 <= pos <= self.cal[axis]
        
        start = self.get_pos_ax(axis)
        
        self.set_pos_ax(pos, axis)
        
        dl = pos - start
        dt = abs(dl) / self.max_speed
        
        # Assume dt is in ms; divide the movement into SLOW_STEP_PERIOD chunks
        steps = int(np.ceil(dt / SLOW_STEP_PERIOD))
        l_step = dl / steps
        
        print ("\t", steps, l_step, dl, dt, start)    
        
        for i in range(1, steps + 1):
            t1 = time.time()         
            self.set_pos_ax(start + i * l_step, axis)
            t2 = time.time()
            
            if (t2 - t1) < SLOW_STEP_PERIOD:
                time.sleep(SLOW_STEP_PERIOD - (t2 - t1))
        # Update internal variables with current position
        self.get_pos()
        
    # def handle_err(self, retcode):
    #    if retcode < 0:
    #        raise IOError(self.MCL_ERROR_CODES[retcode])
    #    return retcode

        
if __name__ == '__main__':
    print ("PI nanopositioner test")
    
    nanodrive = PINanopositioner(debug=True)
    time_start = time.time()
    # for x,y in [ (0,0), (10,10), (30,30), (50,50), (50,25), (50,0)]:
    for x, y, z in [ (30, 1, 1), (30, 10, 10), (30, 30, 30), (30, 50, 60), (30, 25, 60), (30, 1, 1)]:
        
        print ("moving to ", x, y, z)
        nanodrive.set_pos_slow(x, y, z)
        # time.sleep(1)
        x1, y1, z1 = nanodrive.get_pos()
        print ("moved to ", x1, y1, z1)

        # time.sleep(1)
    time_end = time.time()
    print("Calculation time: {}".format(time_end - time_start))
    # nanodrive.close()
    
