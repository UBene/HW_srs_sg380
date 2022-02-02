'''
Created on Nov 16, 2021

@author: bened
'''


import ctypes
from ctypes import windll



from qtpy import QtCore

import sys
from Cython.Shadow import typedef


MAX_SIG_NAME_LEN = 40
MAX_AXIS_ID_LEN = 8
INTERFACE_VERSION = 11

lib = r"C:\Users\RAMAN\workspace\NearField\ScopeFoundryHW\aist-nt_remote_spm\dll\remote_spm.dll"
lib = r"C:\aist\aist_3.5.153\aist\remote_spm\remote_spm.dll"

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
    
    print('hello')
    
    
    spm_remote_interface = SPMRemoteInterface()
    spm_remote_interface.initialization()
    