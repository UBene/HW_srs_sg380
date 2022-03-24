"""
Created on Mar 21, 2022

@author: Benedikt Ursprung
"""
from ScopeFoundry.hardware import HardwareComponent
import visa


def bool2str(v):
    return str(int(v))


def str2bool(v):
    return {"0": False, "1": True}[v]


MODULATIONTYPES = (
    #(0,'OFF'),
    ("OFF", 0,),
    ("unknown", 1,),
    ("unknown", 2,),
    ("unknown", 3,),
    ("unknown", 4,),
    ("unknown", 5,),
    ("IO", 6),
    ("unknown", 7,),
    ("unknown", 8,),
    ("unknown", 9,),)  #'unknown' to author check manual

QFNC = (
    ("unknown", 0,),
    ("unknown", 1,),
    ("unknown", 2,),
    ("unknown", 3,),
    ("unknown", 4,),
    ("external", 5,),
    ("unknown", 6),
    ("unknown", 7,),
    ("unknown", 8,),
    ("unknown", 9,),
)  #'unknown' to author check manual


class SRS(HardwareComponent):

    name = "srs_control"

    def setup(self):
        S = self.settings
        S.New("port", str, initial="GPIB0::GPIBaddr::INSTR")
        S.New("output", bool, initial=False)
        S.New("frequency", unit="Hz", si=True)
        S.New("amplitude", float, unit="dBm")
        S.New("modulation", bool, initial=False)
        S.New("TYPE", int, #initial=MODULATIONTYPES[0][1], 
              choices=MODULATIONTYPES)
        S.New(
            "QFNC", str, initial=5, choices=QFNC,
        )

    def connect(self):

        S = self.settings

        rm = visa.ResourceManager()
        self.dev = SRS = rm.open_resource(S["port"])

        try:
            deviceID = SRS.query("*IDN?")
        except Exception as excpt:
            print(
                "Error: could not query SRS. Please check GPIB address is correct and SRS GPIB communication is enabled. Exception details:",
                type(excpt).__name__,
                ".",
                excpt,
            )
            return False

        print("connected to ", deviceID)
        SRS.write("*CLS")

        S.output.connect_to_hardware(
            self.read_enable_output, self.write_enable_RFOutput
        )
        S.frequency.connect_to_hardware(write_func=self.write_frequency)
        S.amplitude.connect_to_hardware(write_func=self.write_amplitude)
        S.modulation.connect_to_hardware(
            self.read_enable_modulation, self.write_enable_modulation
        )
        S.TYPE.connect_to_hardware(write_func=self.write_type)
        S.QFNC.connect_to_hardware(write_func=self.write_qfnc)

    def SRSerrCheck(self,):
        err = self.dev.query("LERR?")
        if int(err) is not 0:
            print(
                "SRS error: error code",
                int(err),
                ". Please refer to SRS manual for a description of error codes.",
            )
            return False

    def write_enable_output(self, enable):
        a = bool2str(enable)
        self.write(f"ENBR {a}")

    def read_enable_output(self):
        return str2bool(self.ask("ENBR?"))

    def read_frequency(self):
        resp = self.ask("FREQ?")
        if self.settings["debug_mode"]:
            print(resp)
        return resp

    def write_frequency(self, freq, units="Hz"):
        # setSRSFreq: Sets frequency of the SRS output. You can call this function with one argument only (the first argument, freq),
        #             in which case the argument freq must be in Hertz. This function can also be called with both arguments, the first
        #             specifying the frequency and the second one specifying the units, as detailed below.
        #             arguments: - freq: float setting frequency of SRS. This must either be in Hz if the units argument is not passed.
        #                        - units: string describing units (e.g. 'MHz'). For SRS384, minimum unit is 'Hz', max 'GHz'
        self.write("FREQ " + str(freq) + " " + units)

    def write_amplitude(self, RFamplitude, units="dBm"):
        self.write("AMPR " + str(RFamplitude) + " " + units)

    def ask(self, cmd):
        resp = self.dev.query(cmd)[:-4]
        return resp

    def write(self, cmd):
        self.dev.query(cmd)

    def write_enable_modulation(self, enable: bool):
        self.write(f"MODL {bool2str(enable)}")

    def read_enable_modulation(self):
        return str2bool(self.ask("MODL?"))

    def write_type(self, _type: int):
        self.write(f"TYPE {_type}")

    def write_qfnc(self, val):
        self.write(f"QFNC {val}")

    def setupSRSmodulation(self, sequence):
        # Enables IQ modulation with an external source for T2, XY8 and correlation spectroscopy sequences
        # and disables modulation for ESR, Rabi and T1 sequences.
        if sequence in ["ESRseq", "RabiSeq", "T1seq"]:
            self.settings["modulation"] = False
        elif sequence in ["T2seq", "XY8seq", "correlSpecSeq"]:
            self.settings["modulation"] = True
            self.settings["TYPE"] = 6
            self.settings["QFNC"] = 5
        else:
            print(
                "Error in SRScontrol.py: unrecognised sequence name passed to setupSRSmodulation."
            )
            return False

    def enableIQmodulation(self):
        self.SRSerrCheck(self)
        # Enable modulation
        self.write("MODL 1")
        self.SRSerrCheck()
        # Set modulation type to IQ
        self.write("TYPE 6")
        self.SRSerrCheck()
        # Set IQ modulation function to external
        self.write("QFNC 5")
        return self.SRSerrCheck()
