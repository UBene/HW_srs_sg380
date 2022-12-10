from .thorlabs_powermeter import ThorlabsPowerMeterHW
from .thorlabs_pm100d import ThorlabsPM100D
from .powermeter_optimizer import PowerMeterOptimizerMeasure
try:
    from ..nidaq.thorlabs_powermeter_analog_readout import ThorlabsPowerMeterAnalogReadOut 
except ImportError as e:
    print('Could not find', e)