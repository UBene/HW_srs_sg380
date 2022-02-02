from ScopeFoundry.hardware import HardwareComponent
import sys
import Ice

import RemoteSpmRPC
import time


class RemoteSPMHW(HardwareComponent):

    name = "remote_spm_hw"

    def setup(self):
        print(self.name, 'setup')

    def __connect(self):

        prxstr = "myTestAdapter:default -p 54321"  # see remote_crtl.lua
        props = Ice.createProperties(sys.argv)
        # props.setProperty("Ice.ImplicitContext", "Shared")
        props.setProperty('Ice.Default.EncodingVersion', '1.0')
        idata = Ice.InitializationData()
        idata.properties = props
        ice = Ice.initialize(idata)
        prx = ice.stringToProxy(prxstr)        
        
        Ice.loadSlice('RemoteSpm.ice')
        
        remote_spm = RemoteSpmRPC.RemoteSpmPrx.checkedCast(prx)
        print(self.name, remote_spm)
        if not remote_spm:
            raise RuntimeError(f"{self.name} Invalid proxy - Make sure macros is running")
            return
        
        print('successfull connections')
    
    def connect(self):
        print(self.name, 'connect')
        
        with Ice.initialize(sys.argv, 'config.client') as communicator: 
            
            Ice.loadSlice('RemoteSpm.ice')
            
            base = communicator.propertyToProxy('RemoteSpm.Proxy')
            remote_spm = RemoteSpmRPC.RemoteSpmPrx.uncheckedCast(
                base, 'config.client')
            print('remote connected', remote_spm, hasattr(remote_spm, 'isConnected'))
            print(remote_spm.isConnected())

            if not remote_spm:
                print(self.name)
                raise RuntimeError(f"{self.name} Invalid proxy") 

        
            print(remote_spm.isConnected())
            # remote_spm.setProperty("Ice.ACM.Client", "0")
            remote_spm.start()
            
            for i in range(10):
                if remote_spm.isConnecting():
                    print('is_connecting')
                time.sleep(0.1)
                
            if remote_spm.isConnected():
                print("myTestAdapter:default -p 54321 is connected")
                self.dev = remote_spm

    def _connect(self):
        print(self.name, 'connect')
        
        Ice.loadSlice('RemoteSpm.ice')
        
        self.communicator = open(Ice.initialize(sys.argv))
        base = self.communicator.stringToProxy("myTestAdapter:default -p 54321")  # see remote_crtl.lua

        remote_spm = RemoteSpmRPC.RemoteSpmPrx.checkedCast(base)
        if not remote_spm:
            raise RuntimeError(f"{self.name} Invalid proxy")
    
        remote_spm.setProperty("Ice.ACM.Client", "0")
        remote_spm.start()
        
        for i in range(10):
            if remote_spm.isConnecting():
                print('is_connecting')
            time.sleep(0.1)
            
        if remote_spm.isConnected():
            print("myTestAdapter:default -p 54321 is connected")
            self.dev = remote_spm

    def disconnect(self):
        print('disconnect')
        # self.dev.disconnect()
        # self.communicator.close()
        
