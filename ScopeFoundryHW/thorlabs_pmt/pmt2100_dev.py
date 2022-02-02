"""
Command Description

INSTrument
    :NSELect <numeric> Selects source channel by number
    :NSELect? Gets the selected/last channel
    number
    [:SELect] <identifier> SELect - selects source channel by
    name <GAIN; BIAS; OFFSET;
    TRIP>
    [:SELect]? Gets the selected/last channel name
SENSe
    :DETector[:FUNCtion] <function> Sets the type of PMT connected to
    the system < H10721-20>
    :FILTer[:LPASs]:FREQuency <numeric> | Sets the low pass frequency after
        the second amp stage <80MHz;
        2.5MHz; 250kHz>
    :FUNCtion[:ON] <sensor> ON - turns the PMT power on
    :FUNCtion[:OFF] <sensor> OFF - turns the PMT power off
    :FUNCtion:STATe? <sensor> STATe - returns boolean of current
    state of the PMT
    :VOLTage[:DC]:PROTection:CLEar CLEar - clears voltage trip condition
    :VOLTage[:DC]:PROTection[:LEVel]
    <numeric>
    LEVel - sets the voltage trip level in
    uV
    :VOLTage[:DC]:PROTection:STATe
    <boolean>
    STATe 1 - enables the amp trip
    circuit
    STATe 0 - disables the amp trip
    circuit
    :VOLTage[:DC]:PROTection:TRIPped?
    TRIPped - returns boolean of
    tripped state
    :CURRent[:DC]:PROTection:CLEar CLEar - clears current trip condition
    :CURRent[:DC]:PROTection:TRIPped?
    TRIPped - checks if the PMT has
    tripped
    :CURRent[:DC]:PROTection:TRIPped:
    COUNTs?
    COUNTs - counts the number of
    times the PMT has tripped
SOURce
    :VOLTage[:LEVel][:IMMediate][:AMPLitude] <numeric>
        Sets the output on the selected channel, units of V or V/W
    :VOLTage:LIMit:HIGH <numeric> HIGH - sets the upper limit for the
        selected channel, V or V/W
    :VOLTage:LIMit:LOW <numeric> LOW - sets the lower limit for the
        selected channel, V or V/W
    :VOLTage:LIMit:STATe <boolean> STATe - controls whether the limit is enabled
"""
import visa
import time
import logging

from threading import Lock

logger = logging.getLogger(__name__)


class ThorlabsPMT(object):
    
    def __init__(self, port="USB0::0x1313::0x2F00::D3240011::0::INSTR", debug=False):
    
        self.port = port
        self.debug = debug
        self.lock = Lock()
        #self.lock = LogLock('Thorlabs_PM100D')
        #self.lock = DummyLock()
        
        self.visa_resource_manager = visa.ResourceManager()
    
        if debug: 
            print("resources")
            print(self.visa_resource_manager.list_resources())
    
        self.pm = self.visa_resource_manager.get_instrument(port)
        self.pm.timeout = 1000
    
        self.idn = self.ask("*IDN?")
    
    def close(self):
        return self.pm.close()

    def ask(self, cmd):
        if self.debug: logger.debug( "Thorlabs PMT ask " + repr(cmd) )
        with self.lock:
            resp = self.pm.query(cmd)
        if self.debug: logger.debug( "Thorlabs PMT resp ---> " + repr(resp) )
        return resp
    
    def write(self, cmd):
        if self.debug: logger.debug( "PM100D write" + repr(cmd) )
        with self.lock:
            resp = self.pm.write(cmd)
        if self.debug: logger.debug( "PM100D written --->" + repr(resp))

            
    def get_detector_type(self):
        """
        SENSe
            :DETector[:FUNCtion] <function> Sets the type of PMT connected to
            the system < H10721-20>
        """
        return self.ask("SENS:DET:FUNC?")
    
    def get_low_pass_filter_freq(self):
        """SENS:FILTer[:LPASs]:FREQuency <numeric> | Sets the low pass frequency after
        the second amp stage <80MHz;
        2.5MHz; 250kHz>
        
        returns example 2500000Hz
        setting example SENS:FILT:FREQ 2500000Hz
        """
        resp = self.ask("SENS:FILT:FREQ?")
        return resp # need to convert
    
    
    def enable(self, enable=True):
        """SENSe
            :FUNCtion[:ON] <sensor> ON - turns the PMT power on
            :FUNCtion[:OFF] <sensor> OFF - turns the PMT power off
        """
        state = ["OFF", "ON"][int(bool(enable))]
        return self.ask("SENS:FUNC:" + state )

    def get_state(self):
        """SENSe
            :FUNCtion:STATe? <sensor> STATe - returns boolean of current
                state of the PMT
        """
        return self.ask("SEMS:FUNC:STAT?")
    
    def clear_voltage_protection_condition(self):
        """SENSe:VOLTage[:DC]:PROTection:CLEar CLEar - clears voltage trip condition"""
    
    def get_voltage_protection_level(self):
        "SENS:VOLTage[:DC]:PROTection[:LEVel] <numeric>"
        
    def set_voltage_protection_level(self):
        """SENS:VOLTage[:DC]:PROTection[:LEVel] <numeric>
            LEVel - sets the voltage trip level in uV"""

    def enable_voltage_protection(self, enable=True):
        """
        SENS:VOLTage[:DC]:PROTection:STATe        <boolean>
            STATe 1 - enables the amp trip
            circuit
            STATe 0 - disables the amp trip
            circuit
            """
    
    def get_voltage_protection_tripped(self):
        """SENS:VOLTage[:DC]:PROTection:TRIPped?
                TRIPped - returns boolean of tripped state
        """
    
    def clear_current_protection_condition(self):    
        "SENS:CURRent[:DC]:PROTection:CLEar CLEar - clears current trip condition"
    
    def get_current_protection_tripped(self):
        """    :CURRent[:DC]:PROTection:TRIPped?
                TRIPped - checks if the PMT has tripped
        """    
    def get_current_protection_trip_count(self):
        """:CURRent[:DC]:PROTection:TRIPped:
        COUNTs?
        COUNTs - counts the number of times the PMT has tripped
        """
        
    def get_gain_voltage(self):
        resp = self.ask("""INST GAIN;:SOUR:VOLT?""")
        # resp in form "0.6506V"
        return resp

    def set_gain_voltage(self, V):
        assert 0 <= V <= 1.0
        """INST GAIN;:SOUR:VOLT {:1.6f}V""".format(V)

if __name__ == '__main__':
    pmt = ThorlabsPMT(debug=True)
    print("IDN:", pmt.idn)
    pmt.close()