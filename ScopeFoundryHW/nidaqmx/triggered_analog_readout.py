"""
Created on Mar 22, 2022

@author: bened
"""
from ScopeFoundry.hardware import HardwareComponent


import nidaqmx
from nidaqmx.constants import Edge, AcquisitionType, TerminalConfiguration, VoltageUnits


class DAQTriggeredAReadout(HardwareComponent):

    name = "DAQ_triggered_analog_readout"

    def setup(self):
        S = self.settings

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
            choices=[(e.name, e.val) for e in TerminalConfiguration],
            initial=TerminalConfiguration.DEFAULT,
        )
        S.New("rate", int, initial=250000, unit="Hz", description="sampling rate")
        S.New(
            "active_edge", choices=[(e.name, e.val) for e in Edge], initial=Edge.RISING
        )
        S.New(
            "sample_mode",
            choices=[(e.name, e.val) for e in AcquisitionType],
            initial=AcquisitionType.FINITE,
        )
        S.New("samps_per_chan", int, initial=1000)
        S.New("max_val", initial=10.0, unit="V")
        S.New("min_val", initial=-10.0, unit="V")

    def connect(self):

        S = self.settings
        self.task = task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(
            S["input_channel"],
            "",
            S[""],
            S["min_val"],
            S["max_val"],
            VoltageUnits.VOLTS,
        )
        task.timing.cfg_samp_clk_timing(
            S["rate"],
            S["source"],
            S["active_edge"],
            S["sample_mode"],
            S["samps_per_chan"],
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
            )
        return counts

    def disconnect(self):
        self.task.close()


class DAQTriggeredDReadout(HardwareComponent):

    name = "DAQ_triggered_digital_readout"

    def setup(self):
        S = self.settings

        S.New(
            "counter",
            str,
            initial="Dev1/ai1",
            description="""Specifies the name of the counter to use to
                create the virtual channel. The DAQmx physical channel
                constant lists all physical channels, including
                counters, for devices installed in the system.""",
        )
        S.New(
            "trigger_source",
            initial="Dev1/di0",
            str,
            description="""Specifies the name of the counter to use to
                create the virtual channel. The DAQmx physical channel
                constant lists all physical channels, including
                counters, for devices installed in the system.""",
        )
        S.New(
            "trigger_edge",
            choices=[(e.name, e.val) for e in Edge],
            initial=Edge.RISING,
            description="""specifies
                on which edge of the digital signal to start acquiring
                or generating samples.""",
        )
        
        S.New('duration', float=0.1, unit='s', )

    def connect(self):

        S = self.settings
        self.task = task = nidaqmx.Task()
        task.ci_channels.add_ci_count_edges_chan(S["counter"], edge=S["edge"])
        task.triggers.start_trigger.cfg_dig_edge_start_trig(
            S["trigger_source"], S["trigger_edge"]
        )
        task.timing.cfg_samp_clk_timing(
            100_000,
            active_edge=Edge.RISING,
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=1000,
        )

    def read_counts(self, N, timeout=10):
        try:
            counts = self.task.read(N, timeout)
        except Exception as excpt:
            print(
                self.name,
                "Error: could not read DAQ. Please check your DAQ's connections. Exception details:",
                type(excpt).__name__,
                ".",
                excpt,
            )
        return counts

    def disconnect(self):
        self.task.close()


if __name__ == "__main__":
    print(type(Edge))
    print(list(Edge))
