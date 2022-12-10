from __future__ import division, print_function
import pyvisa as visa
import time
import logging


port="USB0::0x1A72::0x101E::0116043634"

visa_resource_manager = visa.ResourceManager()

pm = visa_resource_manager.get_instrument(port)

