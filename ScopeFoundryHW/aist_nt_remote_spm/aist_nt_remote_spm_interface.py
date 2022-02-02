'''
Created on Nov 16, 2021

@author: bened
'''

import ctypes

from remote_spm_client import MyClient


MAX_SIG_NAME_LEN = 40
MAX_AXIS_ID_LEN = 8
INTERFACE_VERSION = 11


class SPMRemoteInterface:
    
    
    
    def __init__(self):
        print('init class')        
        
        d = typedef( int)

        windll.LoadLibrary(lib)
        self.lib = ctypes.cdll.LoadLibrary(lib)
        qlib = self.qlib = QtCore.QLibrary(lib)
        
        
        #d = typedef(int)
        
        #void = typedef(MyPrototype)() 
        #resp = self.qlib.resolve('Initialization')
        #resp = self.qlib.resolve("IsConnected")
        
        
        #void = typedef(int)()
        #myFunction = (int) qlib.resolve("IsConnected")
        #if myFunction:
        #    myFunction()
        
        
        print('load()', qlib.load())
        print('isLoaded', qlib.isLoaded())

    def disconnect(self):
        self.lib.Finalization()
    
    
    def isConnected(self):
        self.lib.IsConnected()
    
    
    
    def initialization(self):
        print('init2')




        #ans = ctypes.c_float()
        #axis = ctypes.c_char('x')
        #self.lib.getPosition(axis, ans)
    

        #init = ctypes.create_string_buffer(MAX_SIG_NAME_LEN)
        #with self.lock: self.lib.GetHeadModel(init)
        #self.headModel = headModel.raw.decode().strip('\x00')




if __name__ == '__main__':

    c = MyClient()
    print(c.add(1, 2))
    #print(c.version())
    