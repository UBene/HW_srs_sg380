"""
Created on Mar 21, 2022

@author: Benedikt Ursprung

to be retired! use 
"""

import time
from random import shuffle

import numpy as np
import pyqtgraph as pg
from pyqtgraph.dockarea.DockArea import DockArea
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from odmr_measurements.esr import ESRPulseProgramGenerator
from odmr_measurements.pulse_blaster_functions import (ContrastModes,
                                                       calculateContrast)
from ScopeFoundry import Measurement, h5_io

sequences = ["ESR", "Rabi", "T1", "T2", "XY8", "correlSpecconfig"]


def norm(x):
    return 1.0 * x / x.max()


class ConfigMeasurement(Measurement):

    name = "config_measurement"

    def setup(self):

        S = self.settings

        self.frequency_range = S.New_Range(
            "frequency", initials=[2.7e9, 3e9, 3e6], unit="Hz", si=True
        )
        # S.New(
        #    "microwavePower", float, initial=-5, unit="dBm",
        # )
        # S.New("sequence", str, choices=sequences, initial="ESR")
        # S.New("t_duration", float, initial=80.0e3, si=False, unit="ns")
        # S.New("t_AOM", float, initial=80.0, si=False, unit="ns")
        # S.New("t_readoutDelay", float, initial=80.0, si=False, unit="ns")
        # S.New("t_pi", float, initial=80.0, si=False, unit="ns")
        # S.New("t_uW", float, initial=80.0, si=False, unit="ns")
        # S.New("t_delay", float, initial=80.0, si=False, unit="ns")

        # S.New("IQpadding", float, initial=80.0)
        # S.New("numberOfPiPulses", int, initial=1)
        # S.New("numberOfRepeats", int, initial=1)
        # S.New("t_delay_betweenXY8seqs", float, initial=80.0, si=False, unit="ns")

        S.New("Nsamples", int, initial=1000, description='Number of samples per frequency')
        S.New("Navg", int, initial=1)
        # S.New("DAQtimeout", float, initial=10)
        S.New("randomize", bool, initial=True)
        S.New("shot_by_shot_normalization", bool, initial=False)
        S.New(
            "contrast_mode",
            str,
            initial="ratio_SignalOverReference",
            choices=ContrastModes,
        )

        S.New("save_h5", bool, initial=True)
        
        self.pulse_generator = ESRPulseProgramGenerator(self)

    def setup_figure(self):
        self.ui = DockArea()        
        
        widget = QWidget()
        self.plot_dock = self.ui.addDock(name=self.name, widget=widget, position='right')
        self.layout = QVBoxLayout(widget)
                
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.frequency_range.New_UI())
        settings_layout.addWidget(self.settings.New_UI(include=["contrast_mode", "Nsamples", "Navg", "randomize", "save_h5"], style='form'))
        settings_layout.addWidget(self.settings.activation.new_pushButton())
        self.layout.addLayout(settings_layout)

        self.graph_layout = pg.GraphicsLayoutWidget(border=(100, 100, 100))
        self.layout.addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title=self.name)
        self.data = {
            "signal": np.arange(10),
            "reference": np.arange(10) / 10,
            "contrast": np.arange(10) / 100,
        }
        colors = ["g", "r", "w"]
        self.plot_lines = {}
        for i, name in enumerate(["signal", "reference", "contrast"]):
            self.plot_lines[name] = self.plot.plot(
                self.data[name], pen=colors[i], symbol="o", symbolBrush=colors[i]
            )
        self.data["frequencies"] = np.arange(10) * 1e9
        self.data_ready = False
        self.i_run = 0
        
        self.ui.addDock(dock=self.pulse_generator.make_dock(), position='right')
        
    def update_display(self):
        if self.data_ready:
            for name in ["signal", "reference", "contrast"]:
                y = self.data[name][:, 0:self.i_run + 1].mean(-1)
                self.plot_lines[name].setData(self.data["frequencies"], norm(y))
        self.plot.setTitle('ESR')

    def pre_run(self):
        self.pulse_generator.update_pulse_plot()
        self.data_ready = False

    def run(self):
        self.data_ready = False
        self.data = {}
        S = self.settings

        SRS = self.app.hardware["srs_control"]
        PB = self.app.hardware["pulse_blaster"]
        DAQ = self.app.hardware['triggered_counter']

        frequencies = self.frequency_range.sweep_array
        self.data['frequencies'] = frequencies
        sequence = 'ESR'

        try:
            """Runs the experiment."""
            # expCfg = import_module(expConfigFile)
            # expCfg.N_freqs = len(
            #     expCfg.frequencies
            # )  # protection against non-integer user inputs for N_freqs.
            # validateUserInput(expCfg)
            # # Check if save directory exists, and, if not, creates a "Saved Data" folder in the current directory, where all data will be saved.
            # if not (isdir(expCfg.savePath)):
            #     makedirs(expCfg.savePath)
            #     print(
            #         "Warning: Save directory did not exist, creating folder named Saved_Data in the working directory. Data will be saved to this directory."
            #     )

            # Initialise SRS and program PulseBlaster

            # SRS = SRSctl.initSRS(conCfg.GPIBaddr,conCfg.modelName)
            SRS.connect()
            # SRSctl.setSRS_RFAmplitude(SRS,expCfg.microwavePower)
            # SRS.settings["amplitude"] = S["microwavePower"]
            # SRSctl.setupSRSmodulation(SRS,expCfg.sequence)
            SRS.setupSRSmodulation(sequence)

            # sequenceArgs = expCfg.updateSequenceArgs()
            # expParamList = expCfg.updateExpParamList()

            # TODO: handle this
            if sequence is not "ESR":
                pass
                # SRSctl.setSRS_Freq(SRS, expCfg.microwaveFrequency)
                # SRS.settings["frequency"] = expCfg.microwaveFrequency
                # Program PB
                # seqArgList = [expCfg.frequencies[-1]]
                # seqArgList.extend(sequenceArgs)
                # instructionArray=PBctl.programPB(expCfg.sequence,seqArgList)
                # PB.programPB(expCfg.sequence, seqArgList)

            else:
                # SRSctl.setSRS_Freq(SRS, expCfg.frequencies[0])
                SRS.settings["frequency"] = frequencies[0]
            # Program PB
            self.pulse_generator.program_hw()
            PB._configure()
            # SRSctl.enableSRS_RFOutput(SRS)
            SRS.settings["output"] = True

            # Configure DAQ
            # DAQclosed = False
            # DAQtask = DAQctl.configureDAQ(expCfg.Nsamples)
            DAQ.restart(2 * S['Nsamples'])
            
            # if expCfg.plotPulseSequence:
            #     # Plot sequence
            #     plt.figure(0)
            #     [t_us, channelPulses, yTicks] = seqCtl.plotSequence(
            #         instructionArray, expCfg.PBchannels
            #     )
            #     for channel in channelPulses:
            #         plt.plot(t_us, list(channel))
            #         plt.yticks(yTicks)
            #         plt.xlabel("time (us)")
            #         plt.ylabel("channel")
            #         # If we are plotting a Rabi with pulse length <5*t_min, warn the user in the sequence plot title that the instructions sent to the PulseBlaster microwave channel are for a 5*t_min pulse, but that the short pulse flags are simultaneously pulsed to produce the desired pulse length
            #         if expCfg.sequence == "RabiSeq" and (seqArgList[0] < (5 * t_min)):
            #             plt.title(
            #                 "Pulse Sequence plot (at last scan point). Close to proceed with experiment...\n(note: we plot the instructions sent to the PulseBlaster (PB) for each channel. For microwave pulses<",
            #                 5 * t_min,
            #                 "ns, the microwave\nchannel (PB_MW) is instructed to pulse for",
            #                 5 * t_min,
            #                 "ns, but the short-pulse flags of the PB are pulsed simultaneously (not shown) to\nproduce the desired output pulse length at PB_MW. This can be verified on an oscilloscope.)",
            #                 fontsize=7,
            #             )
            #         else:
            #             plt.title(
            #                 "Pulse Sequence plot (at last scan point)\n close to proceed with experiment..."
            #             )
            #     plt.show()

            # Initialize data arrays
            N_freqs = len(frequencies)
            Navg = S["Navg"]
            
            # meanSignalCurrentRun = np.zeros(N_freqs)
            # meanBackgroundCurrentRun = np.zeros(N_freqs)
            # contrastCurrentRun = np.zeros(N_freqs)
            signal = np.zeros((N_freqs, Navg))
            reference = np.zeros_like(signal)
            contrast = np.zeros_like(signal)

            # Run experiment
            for i_run in range(Navg):
                self.i_run = i_run
                if self.interrupt_measurement_called:
                    break
                print("Run ", i_run + 1, " of ", Navg)
                if S["randomize"]:
                    if i_run > 0:
                        shuffle(frequencies)
                index = np.argsort(frequencies)
                
                for i_scanPoint in range(N_freqs):
                    pct = 100 * (i_run * N_freqs + i_scanPoint) / (Navg * N_freqs)
                    self.set_progress(pct)
                    if self.interrupt_measurement_called:
                        break
                    
                    if sequence == "ESR":
                        # SRSctl.setSRS_Freq(SRS, expCfg.frequencies[i_scanPoint])
                        SRS.settings["frequency"] = frequencies[i_scanPoint]

                    # TODO: handle this
                    # else:
                    #    seqArgList[0] = frequencies[i_scanPoint]
                    #    instructionArray = PB.programPB(sequence, seqArgList)
                    print("Scan point ", i_scanPoint + 1, " of ", N_freqs)
                    time.sleep(0.01)
                    
                    cts = np.array(DAQ.read_counts(2 * S['Nsamples']))
                    # sig = cts[0::2]
                    # ref = cts[1::2]
                    # ref = ref - sig
                    # sig = cts[0::2] - cts[1::2]
                    ref = np.sum(cts[1::2] - cts[0::2])
                    sig = np.sum(cts[2::2] - cts[1:-2:2]) + cts[0]                 
                    
                    # print(cts[0::4].mean(), cts[1::4].mean(), cts[2::4].mean(), cts[3::4].mean(),)
                    # print(cts[:8])
                    
                    # sig = cts[1::4] - cts[0::4]
                    # ref = cts[3::4] - cts[2::4]
                    
                    print(sig.sum(), ref.sum())
                    # Take average of counts
                    ii = index[i_scanPoint]
                    signal[ii][i_run] = sig
                    reference[ii][i_run] = ref
                    if S["shot_by_shot_normalization"]:
                        contrast[ii][i_run] = np.mean(
                            calculateContrast(S["contrastMode"], sig, ref)
                        )
                    else:
                        contrast[ii][i_run] = calculateContrast(
                            S["contrast_mode"], signal[ii][i_run], reference[ii][i_run],
                        )

                    # if i_run == 0:
                    #     if expCfg.livePlotUpdate:
                    #         xValues = expCfg.frequencies[0 : i_scanPoint + 1]
                    #         plt.plot(
                    #             [x / expCfg.plotXaxisUnits for x in xValues],
                    #             contrastCurrentRun[0 : i_scanPoint + 1],
                    #             "b-",
                    #         )
                    #         plt.ylabel("Contrast")
                    #         plt.xlabel(expCfg.xAxisLabel)
                    #         plt.draw()
                    #         plt.pause(0.0001)
                    #
                    #     # Save data at intervals dictated by saveSpacing_inPulseLengthPts and at final delay point
                    #     if (i_scanPoint % expCfg.saveSpacing_inScanPts == 0) or (
                    #         i_scanPoint == expCfg.N_freqs - 1
                    #     ):
                    #         data = np.zeros([i_scanPoint + 1, 3])
                    #         data[:, 0] = expCfg.frequencies[0 : i_scanPoint + 1]
                    #         data[:, 1] = meanSignalCurrentRun[0 : i_scanPoint + 1]
                    #         data[:, 2] = meanBackgroundCurrentRun[0 : i_scanPoint + 1]
                    #         dataFile = open(expCfg.dataFileName, "w")
                    #         for line in data:
                    #             dataFile.write("%.0f\t%.8f\t%.8f\n" % tuple(line))
                    #         paramFile = open(expCfg.paramFileName, "w")
                    #         expParamList[1] = i_scanPoint + 1
                    #         paramFile.write(
                    #             expCfg.formattingSaveString % tuple(expParamList)
                    #         )
                    #         dataFile.close()
                    #         paramFile.close()

                    self.data["signal"] = signal
                    self.data["reference"] = reference
                    self.data["contrast"] = contrast
                    self.data["frequencies"] = frequencies
                    self.data_ready = True
                # Sort current run counts in order of increasing delay

                # dataCurrentRun = np.transpose(
                #     np.array(
                #         [
                #             frequencies,
                #             meanSignalCurrentRun,
                #             meanBackgroundCurrentRun,
                #             contrastCurrentRun,
                #         ]
                #     )
                # )
                # sortingIndices = np.argsort(dataCurrentRun[:, 0])
                # dataCurrentRun = dataCurrentRun[sortingIndices]
                # # Fill in current run data:
                # sortedScanParam = dataCurrentRun[:, 0]
                # signal[:, i_run] = dataCurrentRun[:, 1]
                # background[:, i_run] = dataCurrentRun[:, 2]
                # contrast[:, i_run] = dataCurrentRun[:, 3]
                #
                # # Update quantities for plotting
                # updatedSignal = np.mean(signal[:, 0 : i_run + 1], 1)
                # updatedBackground = np.mean(background[:, 0 : i_run + 1], 1)
                # updatedContrast = np.mean(contrast[:, 0 : i_run + 1], 1)
                #
                # self.data_ready = True

                # Update plot:
                # if expCfg.livePlotUpdate:
                #     plt.clf()
                # plt.plot(
                #     [x / expCfg.plotXaxisUnits for x in sortedScanParam],
                #     updatedContrast,
                #     "b-",
                # )
                # plt.ylabel("Contrast")
                # plt.xlabel(expCfg.xAxisLabel)
                # plt.draw()
                # plt.pause(0.001)

                # Save data at intervals dictated by saveSpacing_inAverages and after final scan
                # if (i_run % expCfg.saveSpacing_inAverages == 0) or (
                #     i_run == expCfg.Navg - 1
                # ):
                #     data = np.zeros([expCfg.N_freqs, 3])
                #     data[:, 0] = sortedScanParam
                #     data[:, 1] = updatedSignal
                #     data[:, 2] = updatedBackground
                #     dataFile = open(expCfg.dataFileName, "w")
                #     for item in data:
                #         dataFile.write("%.0f\t%.8f\t%.8f\n" % tuple(item))
                #     paramFile = open(expCfg.paramFileName, "w")
                #     expParamList[3] = i_run + 1
                #     paramFile.write(expCfg.formattingSaveString % tuple(expParamList))
                #     dataFile.close()
                #     paramFile.close()

        finally:
            # Turn off SRS output
            SRS.settings["output"] = False
            SRS.settings["modulation"] = False
            DAQ.end_task()

    def post_run(self):
        if self.settings['save_h5']:
            self.save_h5_data()
        
    def save_h5_data(self):
        self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_meas_group = h5_io.h5_create_measurement_group(self, self.h5_file)
        ref = self.data['reference'].mean(-1)
        sig = self.data['signal'].mean(-1)
        self.h5_meas_group['reference'] = ref
        self.h5_meas_group['signal'] = sig
        for c in ContrastModes:
            self.h5_meas_group[c] = calculateContrast(c, sig, ref)
        for k, v in self.data.items():
            self.h5_meas_group[k] = v        
        self.pulse_generator.save_to_h5(self.h5_meas_group)
        self.h5_file.close()
