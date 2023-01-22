'''
Created on Jan 22, 2023

@author: MT-User
'''
_ERRORS = {
    # FTDI and Communication errors

    # The following errors are generated from the FTDI communications module
    # or supporting code.
    0: ("FT_OK", "Success"),
    1: ("FT_InvalidHandle", "The FTDI functions have not been initialized."),
    2: ("FT_DeviceNotFound", "The Device could not be found: This can be generated if the function TLI_BuildDeviceList() has not been called."),
    3: ("FT_DeviceNotOpened", "The Device must be opened before it can be accessed. See the appropriate Open function for your device."),
    4: ("FT_IOError", "An I/O Error has occured in the FTDI chip."),
    5: ("FT_InsufficientResources", "There are Insufficient resources to run this application."),
    6: ("FT_InvalidParameter", "An invalid parameter has been supplied to the device."),
    7: ("FT_DeviceNotPresent", """The Device is no longer present. The device may have been disconnected since the last TLI_BuildDeviceList() call."""),
    8: ("FT_IncorrectDevice", "The device detected does not match that expected"),
    # The following errors are generated by the device libraries.
    16: ("FT_NoDLLLoaded", "The library for this device could not be found"),
    #     17 (0x11) FT_NoFunctionsAvailable - No functions available for this device./term>
    #     18 (0x12) FT_FunctionNotAvailable - The function is not available for this device./term>
    #     19 (0x13) FT_BadFunctionPointer - Bad function pointer detected./term>
    #     20 (0x14) FT_GenericFunctionFail - The function failed to complete succesfully./term>
    # 21 (0x15) FT_SpecificFunctionFail - The function failed to complete
    # succesfully./term>

    # General DLL control errors

    # The following errors are general errors generated by all DLLs.

    # 32 (0x20) TL_ALREADY_OPEN - Attempt to open a device that was already open.
    # 33 (0x21) TL_NO_RESPONSE - The device has stopped responding.
    # 34 (0x22) TL_NOT_IMPLEMENTED - This function has not been implemented.
    # 35 (0x23) TL_FAULT_REPORTED - The device has reported a fault.
    # 36 (0x24) TL_INVALID_OPERATION - The function could not be completed at this time.
    # 36 (0x28) TL_DISCONNECTING - The function could not be completed because the device is disconnected.
    # 41 (0x29) TL_FIRMWARE_BUG - The firmware has thrown an error
    # 42 (0x2A) TL_INITIALIZATION_FAILURE - The device has failed to initialize
    # 43 (0x2B) TL_INVALID_CHANNEL - An Invalid channel address was supplied


    # Motor specific errors
    #
    # The following errors are motor specific errors generated by the Motor DLLs.
    #
    # 37 (0x25) TL_UNHOMED - The device cannot perform this function until it has been Homed.
    # 38 (0x26) TL_INVALID_POSITION - The function cannot be performed as it would result in an illegal position.
    # 39 (0x27) TL_INVALID_VELOCITY_PARAMETER - An invalid velocity parameter was supplied
    #  The velocity must be greater than zero.
    # 44 (0x2C) TL_CANNOT_HOME_DEVICE - This device does not support Homing
    #  Check the Limit switch parameters are correct.
    # 45 (0x2D) TL_JOG_CONTINOUS_MODE - An invalid jog mode was supplied for the jog function.
    # 46 (0x2E) TL_NO_MOTOR_INFO - There is no Motor Parameters available to
    # convert Real World Units.

}


def handle_error(retval):
    if retval == 0:
        return retval
    else:
        err_name, description = _ERRORS.get(
            retval, ("UNKNOWN", "Unknown error code."))
        raise IOError("Thorlabs Kinesis Error [{}] {}: {} ".format(
            retval, err_name, description))
