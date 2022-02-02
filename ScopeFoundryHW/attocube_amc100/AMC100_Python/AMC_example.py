"""
by attocube systems AG 2020

@author: Schindler
"""

import AMC
import time

### This script requires the PRO version of the AMC100.


def main(ipadress='192.168.1.1'):
    '''
    This is an example for the AMC100/NUM/PRO.

    Parameters
    ----------
    ipadresse : str
        Optional parameter. Default 192.168.1.1. The IP-adresse of the AMC100 the example is used with.
        The IP-adresse of an new device is 192.168.1.1

    Returns
    -------
    None.

    '''

    dev = AMC.Device(ipadress)
    dev.connect()

    axis = 0 # axes 1-3 are counted as zero based int 0-2

    #### print the firmware version ####
    print("Firmware Version: " + str(dev.system.getFirmwareVersion()))

    #### Check if axis is connected. If yes start script ####
    if dev.status.getStatusConnected(axis)[1] == True:
        dev.control.setControlOutput(axis, True)
        print("Position: " + str(dev.move.getPosition(axis)[1]))
        dev.control.setReset(axis) # Set Position to Zero
        #print("PositionersList: " + str(dev.getPositionersList())) # get possible positioner Types
        dev.control.setActorParametersByName(axis, 'ECSx5050') # Set positioner Type
        dev.control.setControlAmplitude(axis, 45000) # set amplitude
        dev.control.setControlFrequency(axis, 1000000) # set Frequency
        ### Open loop movements ###
        dev.move.setNSteps(axis, True, 1000) # (axis, Forward Direction, Number of steps) # Pro Version needed
        dev.move.setControlEotOutputDeactive(axis, True) # activates the end of travel detection. The positioner stops automatically 
        dev.move.setControlContinousFwd(axis, True)
        while (0, False) == dev.status.getStatusEotFwd(axis): # wait till the positioner reaches the end of the travel range.
            time.sleep(0.5)
        dev.move.setControlContinousBkwd(axis, True)
        while (0, False) == dev.status.getStatusEotBkwd(axis):
            time.sleep(0.5)
        ### Closed loop movements ###
        if dev.status.getStatusReference(axis)[1] == True:
            print("Reference Position: " + str(dev.control.getReferencePosition(axis)[1]))
        else:
            print('Reference not found yet')
        dev.control.setControlTargetRange(axis, 100) # Activates TargetRange Status to true if position is within 100nm to the target position
        dev.move.setControlTargetPosition(axis, 0) # set Target Position to 1µm
        ### Deactivate outputs and close connection
        dev.control.setControlMove(axis, True) # actives Closed loop
        time.sleep(3)
        for i in range(0, 10):
            dev.move.setControlTargetPosition(axis, 1000*i)
            time.sleep(1)
            while dev.status.getStatusTargetRange(axis)[1]!= True:
                time.sleep(0.5) # wait for another 500ms
        dev.move.setControlTargetPosition(axis, 0) # go to zero position
        dev.control.setControlMove(axis, False)
        dev.control.setControlOutput(axis, False)
    dev.close()


if __name__ == '__main__':
    main()