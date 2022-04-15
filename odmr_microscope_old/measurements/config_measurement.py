"""
Created on Mar 21, 2022

@author: Benedikt Ursprung
"""


from ScopeFoundry import Measurement
import pyqtgraph as pg
from ScopeFoundry import h5_io
import time
import os
import numpy as np
from qtpy.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QCompleter,
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QGroupBox,
    QLabel,
)
from qtpy import QtCore




from random import shuffle
from ScopeFoundry.logged_quantity import FileLQ
from odmr_microscope.measurements.helper_funcs_constants import ContrastModes, calculateContrast

sequences = ["ESR", "Rabi", "T1", "T2", "XY8", "correlSpecconfig"]

# from .mainControl import validateUserInput, calculateContrast


# TODO: incorporate DAQcontrol to ScopeFoundry
# from .DAQcontrol import configureDAQ, readDAQ, closeDAQTask


class ConfigMeasurement(Measurement):

    name = "config_measurement"

    def setup(self):

        S = self.settings

        self.frequency_range = S.New_Range(
            "frequency", initials=[2.7e9, 3e9, 3e6], unit="Hz", si=True
        )
        S.New(
            "microwavePower", float, initial=-5, unit="dBm",
        )
        S.New("sequence", str, choices=sequences, initial="ESR")
        S.New("t_duration", float, initial=80.0e-9, si=True, unit="sec")
        S.New("Nsamples", int, initial=1000)
        S.New("Navg", int, initial=1)
        S.New("DAQtimeout", int, initial=10)
        S.New("randomize", bool, initial=True)
        S.New("shotByShotNormalization", bool, initial=False)
        S.New(
            "contrast_mode",
            str,
            initial="ratio_SignalOverReference",
            choices=ContrastModes,
        )

        self.file = FileLQ("config_file")

        S.New("save_h5", bool, initial=True)

    def setup_figure(self):
        self.ui = QWidget()
        self.layout = QVBoxLayout(self.ui)

        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.file.new_default_widget())
        settings_layout.addWidget(self.settings.sequence.new_default_widget())
        settings_layout.addWidget(self.settings.activation.new_pushButton())
        self.layout.addLayout(settings_layout)

        if hasattr(self, "graph_layout"):
            self.graph_layout.deleteLater()  # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout = pg.GraphicsLayoutWidget(border=(100, 100, 100))
        self.ui.layout().addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title=self.name)
        self.data = {
            "signal": np.arange(10),
            "background": np.arange(10) / 10,
            "contrast": np.arange(10) / 100,
        }
        colors = ["g", "r", "w"]
        self.plot_lines = {}
        for i, name in enumerate(self.data):
            self.plot_lines[name] = self.plot.plot(
                self.data[name], pen=colors[i], symbol="o", symbolBrush=colors[i]
            )
        self.data["scannedParam"] = np.arange(10) * 1e9

    def update_display(self):
        for name in ["signal", "background", "contrast"]:
            self.plot_lines[name].setData(
                self.data["scannedParam"], self.data[name].mean(-1)
            )
        self.plot.setTitle(self.settings["sequence"])

    def pre_run(self):
        self.data_ready = False

    def run(self):
        self.data = {}
        S = self.settings

        SRS = self.app.hardware["srs_control"]
        PB = self.app.hardware["pulse_blaster"]

        scannedParam = self.frequency_range.sweep_array
        sequence = S["sequence"]
        PBchannels = PB.address_lookup
        sequenceArgs = [S["t_duration"]]

        try:
            """Runs the experiment."""
            # expCfg = import_module(expConfigFile)
            # expCfg.N_scanPts = len(
            #     expCfg.scannedParam
            # )  # protection against non-integer user inputs for N_scanPts.
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
            SRS.settings["amplitude"] = S["microwavePower"]
            # SRSctl.setupSRSmodulation(SRS,expCfg.sequence)
            SRS.setupSRSmodulation(SRS, sequence)

            # sequenceArgs = expCfg.updateSequenceArgs()
            # expParamList = expCfg.updateExpParamList()

            # TODO: handle this
            if sequence is not "ESR":
                pass
                # SRSctl.setSRS_Freq(SRS, expCfg.microwaveFrequency)
                # SRS.settings["frequency"] = expCfg.microwaveFrequency
                # Program PB
                # seqArgList = [expCfg.scannedParam[-1]]
                # seqArgList.extend(sequenceArgs)
                # instructionArray=PBctl.programPB(expCfg.sequence,seqArgList)
                # PB.programPB(expCfg.sequence, seqArgList)

            else:
                # SRSctl.setSRS_Freq(SRS, expCfg.scannedParam[0])
                SRS.settings["frequency"] = scannedParam[0]
                # Program PB
                instructionArray = PB.programPB(sequence, sequenceArgs)
            # SRSctl.enableSRS_RFOutput(SRS)
            SRS.settings["modulation"] = True

            # Configure DAQ
            #DAQclosed = False
            #DAQtask = DAQctl.configureDAQ(expCfg.Nsamples)
            #
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
            N_scanPts = len(scannedParam)
            Navg = S["Navg"]
            
            meanSignalCurrentRun = np.zeros(N_scanPts)
            meanBackgroundCurrentRun = np.zeros(N_scanPts)
            contrastCurrentRun = np.zeros(N_scanPts)
            signal = np.zeros((N_scanPts, Navg))
            background = np.zeros_like(signal)
            contrast = np.zeros_like(signal)

            # Run experiment
            for i_run in range(Navg):
                print("Run ", i_run + 1, " of ", Navg)
                if S["randomize"]:
                    if i_run > 0:
                        shuffle(scannedParam)

                index = np.argsort(scannedParam)
                for i_scanPoint in range(N_scanPts):
                    if sequence == "ESR":
                        # SRSctl.setSRS_Freq(SRS, expCfg.scannedParam[i_scanPoint])
                        SRS.settings["frequency"] = scannedParam[i_scanPoint]

                    # TODO: handle this
                    # else:
                    #    seqArgList[0] = scannedParam[i_scanPoint]
                    #    instructionArray = PB.programPB(sequence, seqArgList)
                    print("Scan point ", i_scanPoint + 1, " of ", N_scanPts)

                    # read DAQ
                    # TODO: handle this line
                    # cts = DAQctl.readDAQ(DAQtask, 2 * S['Nsamples'], DAQtimeout)

                    # Extract signal and background counts
                    cts = [3,6]
                    
                    
                    sig = cts[0]
                    bkgnd = cts[1]-cts[0]                   
                    #sig = cts[0::2]
                    #bkgnd = cts[1::2]

                    # Take average of counts
                    ii = index[i_scanPoint]
                    signal[ii][i_run] = np.mean(sig)
                    background[ii][i_run] = np.mean(bkgnd)
                    if S["shotByShotNormalization"]:
                        contrast[ii][i_run] = np.mean(
                            calculateContrast(S["contrastMode"], sig, bkgnd)
                        )
                    else:
                        contrast[ii][i_run] = calculateContrast(
                            S["contrastMode"], signal[ii][i_run], background[ii][i_run],
                        )

                    # if i_run == 0:
                    #     if expCfg.livePlotUpdate:
                    #         xValues = expCfg.scannedParam[0 : i_scanPoint + 1]
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
                    #         i_scanPoint == expCfg.N_scanPts - 1
                    #     ):
                    #         data = np.zeros([i_scanPoint + 1, 3])
                    #         data[:, 0] = expCfg.scannedParam[0 : i_scanPoint + 1]
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

                    self.data["signal":signal]
                    self.data["background":background]
                    self.data["contrast":contrast]
                    self.data["scannedParam":scannedParam]
                    self.data_ready = True
                # Sort current run counts in order of increasing delay

                # dataCurrentRun = np.transpose(
                #     np.array(
                #         [
                #             scannedParam,
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
                #     data = np.zeros([expCfg.N_scanPts, 3])
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

            # Turn off SRS output
            # SRSctl.disableSRS_RFOutput(SRS)
            SRS.disconnect()

            # TODO: closed DAQ
            # Close DAQ task:
            # DAQctl.closeDAQTask(DAQtask)
            # DAQclosed = True
        except KeyboardInterrupt:
            print("User keyboard interrupt. Quitting...")
            return
        finally:
            if "SRS" in vars():
                # Turn off SRS output
                # SRSctl.disableSRS_RFOutput(SRS)
                SRS.settings["output"] = False

            #if ("DAQtask" in vars()) and (not DAQclosed):
                # Close DAQ task:
                #DAQctl.closeDAQTask(DAQtask)
            #    DAQclosed = True
