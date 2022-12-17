"""
Created on Mar 22, 2022

@author: Benedikt Ursprung
"""
from ScopeFoundry.hardware import HardwareComponent

import nidaqmx
from nidaqmx.constants import Edge, AcquisitionType, TerminalConfiguration, VoltageUnits


class DAQTriggeredAReadout(HardwareComponent):

    name = "DAQ_triggered_analog_readout"

    def setup(self):
        S = self.settings
        
        print((e.name, e.value, type(e.value)) for e in AcquisitionType)

        S.New(
            "input_channel",
            str,
            initial="Dev1/ai1",
            description="""the analog input channel of the DAQ to which you have connected your photodector's 
                              signal. Here, this is assumed to be a Referenced Single-Ended (RSE) connection. 
                              If the user wishes to use a differential connection, the configuration below and 
                              in the DAQcontrol.py library should be modified accordingly (e.g. if using the NI 
                              USB-6211 DAQ card, refer to chapter 4 the NI USB-621x manual version from April 
                              2009, for analog-input connection options)""",
        )
        S.New(
            "sample_clock",
            str,
            initial="PFI0",
            description="""is the Peripheral Function Interface (PFI) terminal of the DAQ to which you have 
              connected the output of the PB_DAQ PulseBlaster channel (i.e. the PulseBlaster channel which generates 
              the TTL pulses that gate/act as a sample clock to time the data aquisition)""",
        )
        S.New(
            "source",
            str,
            initial="PFI5",
            description="""Specifies the source terminal of the
                Sample Clock. Leave this input unspecified to use the
                default onboard clock of the device.""",
        )
        S.New(
            "terminal_config",
            int,
            choices=[(e.name, e.value) for e in TerminalConfiguration],
            initial=TerminalConfiguration.DEFAULT.value,
        )
        S.New("rate", int, initial=250000, unit="Hz", description="sampling rate")
        S.New(
            "active_edge", choices=[(e.name, e.value) for e in Edge],  # initial=Edge.RISING
        )
        S.New(
            "sample_mode",
            int,
            choices=[(e.name, e.value) for e in AcquisitionType],
            initial=AcquisitionType.FINITE.value,
        )
        S.New("samps_per_chan", int, initial=1000)
        S.New("max_val", initial=10.0, unit="V")
        S.New("min_val", initial=-10.0, unit="V")

    def connect(self):

        S = self.settings
        self.task = task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(
            
            physical_channel=S["input_channel"],
            name_to_assign_to_channel="",
            terminal_config=TerminalConfiguration.DEFAULT,
            min_val=S["min_val"],
            max_val=S["max_val"],
            units=VoltageUnits.VOLTS
        )
        task.timing.cfg_samp_clk_timing(
            rate=S["rate"],
            source=S["source"],
            active_edge=S["active_edge"],
            sample_mode=S["sample_mode"],
            samps_per_chan=S["samps_per_chan"],
        )
        task.timing.ai_conv_src = S["sample_clock"]
        task.timing.ai_conv_active_edge = S["edge"]

        # Configure start trigger
        task.triggers.start_trigger.readStartTrig.cfg_dig_edge_start_trig(
            S["source"], S["edge"]
        )

    def readDAQ(self, N, timeout):
        try:
            counts = self.task.read(N, timeout)
        except Exception as excpt:
            print(
                self.name,
                "Error: could not read DAQ. Please check your DAQ's connections. Exception details:",
                type(excpt).__name__,
                ".",
                excpt,
                counts=0
            )
        return counts

    def disconnect(self):
        self.task.close()



if __name__ == "__main__":
    print(type(Edge))
    print(list(Edge))
