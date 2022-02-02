# Tests if a python client can be connected to the corresponding proxy server
# Proxy server is initialized in the aist software by running the 
# macros\qnami\remote_crtl.lua macro
#
# Requires pip install zeroc-ice
# Adapted from Demo.printer example from Ice manual
# Copyright (c) ZeroC, Inc. All rights reserved
#



import sys
import Ice

Ice.loadSlice('RemoteSpm.ice')

import RemoteSpmRPC
import time


#
# Ice.initialize returns an initialized Ice communicator,
# the communicator is destroyed once it goes out of scope.
#
with Ice.initialize(sys.argv) as communicator:
    #base = communicator.stringToProxy("SimplePrinter:default -h localhost -p 10000")
    base = communicator.stringToProxy("myTestAdapter:default -p 54321") #see remote_crtl.lua
    #prop = communicator.propertyToProxy('Ice.Default.EncodingVersion')
    
    props = Ice.createProperties(sys.argv)
    props.setProperty('Ice.Default.EncodingVersion', '1.0')
    idata = Ice.InitializationData()
    idata.properties = props

    ice = Ice.initialize(idata)
    prx = ice.stringToProxy(prxstr)
    
    
    remote_spm = RemoteSpmRPC.RemoteSpmPrx.checkedCast(base)
    #remote_spm.setProperty('Ice.Default.EncodingVersion', '1.0')
    if not remote_spm:
        raise RuntimeError("Invalid proxy")

    remote_spm.setProperty("Ice.ACM.Client", "0")
    remote_spm.start()
    
    for i in range(10):
        if remote_spm.isConnecting():
            print('is_connecting')
        time.sleep(0.1)
        
    if remote_spm.isConnected():
        print("myTestAdapter:default -p 54321 is connected")
                
        
    
    