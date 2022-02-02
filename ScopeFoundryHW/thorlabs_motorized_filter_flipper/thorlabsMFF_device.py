'''
Created on Nov 3, 2017

@author: Benedikt Ursprung
'''
import time
import logging
import ctypes

logger = logging.getLogger(__name__)




class ThorlabsMFFDev(object):

    " Use Thorlabs kinesis software to control Motorized Flip mirror system MFF101 MFF102"
    
    
    def __init__(self, sernum, poll_time=0.1, debug=False):

        # force serial number to be an integer
        self.sernum = int(sernum) 
        
        self.poll_time = poll_time # polling period in seconds
        
        self.debug = debug
        if self.debug:
            logger.debug("ThorlabsMFFDev.__init__, port={}".format(self.sernum))
        
        # Load DLL libraries, note DeviceManager.dll must be loaded first    
        self.devman_dll = ctypes.windll.LoadLibrary("C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.DeviceManager.dll")
        self.ff_dll = ctypes.windll.LoadLibrary("C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.FilterFlipper.dll")

        # byte string representing serial number, like b'37874816'
        self._sernum = str(self.sernum).encode('ascii') 
        
        self.ff_dll.FF_Open(self._sernum)
        
        # polling required to operate device
        self.ff_dll.FF_StartPolling(self._sernum, int(self.poll_time*1000) )
        
        time.sleep(0.2)
        
    
    def move_pos(self, pos):
        assert pos in (1,2)
        self.ff_dll.FF_MoveToPosition(self._sernum,pos)
    
    def move_pos_wait(self, pos):
        self.move_pos(pos)
        while(self.get_pos() != pos):
            if self.debug: print("waiting")
            time.sleep(self.poll_time/2)
    
    def get_pos(self):
        return self.ff_dll.FF_GetPosition(self._sernum)
        
    
    def close(self):
        self.ff_dll.FF_StopPolling(self._sernum)
        self.ff_dll.FF_Close(self._sernum)    
    
    
if __name__ == '__main__':
    '''
    dev = ThorlabsMFFDev(sernum=37874816, debug=True)
    

    print('get_pos', dev.get_pos())
    
    dev.move_pos(1)
    
    for i in range(10):
        print('get_pos', dev.get_pos())
        time.sleep(0.05)

    dev.move_pos(2)
    
    for i in range(10):
        print('get_pos', dev.get_pos())
        time.sleep(0.05)
        
    dev.move_pos_wait(1)
    
    dev.close()
    '''
    
    position_map = {'spectrometer':1, 'apd':2}
    print(position_map[1])