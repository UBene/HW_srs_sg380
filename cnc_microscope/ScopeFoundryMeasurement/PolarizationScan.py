'''
Created on Feb 22, 2019

@author: Xinyi Xu
'''
from ScopeFoundry import Measurement
import numpy as np
import time
from ScopeFoundry import h5_io
from ScopeFoundry.helper_funcs import sibling_path
import pyqtgraph as pg

#################################################



class PolarizationScanMeasure(Measurement):

    name = "polarization_scan"

    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "PolarizationScan.ui")
        Measurement.__init__(self, app)

    def setup(self):          #SF build in fct, create logged quantity

        self.Excitation_min = self.add_logged_quantity("Excitation_min",
                                                       dtype=float, spinbox_decimals=2, initial=0, vmin=-360, vmax=+2880, ro=False)
        self.Excitation_max = self.add_logged_quantity("Excitation_max",
                                                       dtype=float, spinbox_decimals=2, initial=0, vmin=-360, vmax=+2880, ro=False)
        self.Collection_min = self.add_logged_quantity("Collection_min",
                                                       dtype=float, spinbox_decimals=2, initial=0, vmin=-360, vmax=+2880, ro=False)
        self.Collection_max = self.add_logged_quantity("Collection_max",
                                                       dtype=float, spinbox_decimals=2, initial=0, vmin=-360, vmax=+2880, ro=False)
        self.Step_ndatapoints = self.add_logged_quantity("Step_ndatapoints",
                                                         dtype=int, unit='', initial=1, vmin=1, vmax=2880, ro=False)
        self.IntegrationRange_min = self.add_logged_quantity("IntegrationRange_min",
                                                             dtype=int, unit='', initial=1, vmin=1, vmax=4000, ro=False)
        self.IntegrationRange_max = self.add_logged_quantity("IntegrationRange_max",
                                                             dtype=int, unit='', initial=1, vmin=1, vmax=4000, ro=False)
        self.Polarization_Compensation_Ratio = self.add_logged_quantity("Polar_Compen_ratio",
                                                        dtype=float, spinbox_decimals=3, initial=0, vmin=-1000, vmax=+1000, ro=False)


        self.Fix_Collection_Stage    = self.add_logged_quantity("Fix_Collection_Stage",dtype=bool, initial=False)
        self.Fix_Excitation_Stage    = self.add_logged_quantity("Fix_Excitation_Stage",dtype=bool, initial=False)
        self.use_shutter    = self.add_logged_quantity("use_shutter",dtype=bool, initial=True)

        self.collect_apd      = self.add_logged_quantity("collect_apd",      dtype=bool, initial=False)
        self.collect_spectrum = self.add_logged_quantity("collect_spectrum", dtype=bool, initial=False)
        self.collect_lifetime = self.add_logged_quantity("collect_lifetime", dtype=bool, initial=False)
        self.collect_Si_powermeter = self.add_logged_quantity("collect_Si_powermeter", dtype=bool, initial=False)
        self.collect_Ge_powermeter = self.add_logged_quantity("collect_Ge_powermeter", dtype=bool, initial=False)
        #self.collect_ascom_img = self.add_logged_quantity('collect_ascom_img', dtype=bool, initial=False)
        self.x_axis_flag = 0

        #self.settings.New("x_axis", dtype=str, initial='Excitation_Stage_Pos', choices=('Excitation_Stage_Pos', 'Collection_Stage_Pos'))



    def setup_figure(self):        #SF build in fct, connect lq to the UI

        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

        self.Excitation_min.connect_to_widget(self.ui.Excitation_min_doubleSpinBox)
        self.Excitation_max.connect_to_widget(self.ui.Excitation_max_doubleSpinBox)
        self.Collection_min.connect_to_widget(self.ui.Collection_min_doubleSpinBox)
        self.Collection_max.connect_to_widget(self.ui.Collection_max_doubleSpinBox)
        self.Step_ndatapoints.connect_to_widget(self.ui.num_datapoints_doubleSpinBox)
        self.IntegrationRange_min.connect_to_widget(self.ui.IntegrationRange_min_doubleSpinBox)
        self.IntegrationRange_max.connect_to_widget(self.ui.IntegrationRange_max_doubleSpinBox)
        self.Polarization_Compensation_Ratio.connect_to_widget(self.ui.PolarizationCompensationRatio_doubleSpinBox)

        self.use_shutter.connect_bidir_to_widget(self.ui.use_shutter_checkBox)
        self.Fix_Collection_Stage.connect_bidir_to_widget(self.ui.Fix_Collection_Stage_checkBox)
        self.Fix_Excitation_Stage.connect_bidir_to_widget(self.ui.Fix_Excitation_Stage_checkBox)

        self.collect_apd.connect_to_widget(self.ui.collect_apd_checkBox)
        self.collect_spectrum.connect_to_widget(self.ui.collect_spectrum_checkBox)
        self.collect_lifetime.connect_to_widget(self.ui.collect_hydraharp_checkBox)
        self.collect_Si_powermeter.connect_to_widget(self.ui.collect_Si_powermeter_checkBox)
        self.collect_Ge_powermeter.connect_to_widget(self.ui.collect_Ge_powermeter_checkBox)




        # Hardware connections
        if 'apd_counter' in self.app.hardware.keys():
            self.app.hardware.apd_counter.settings.int_time.connect_bidir_to_widget(
                self.ui.apd_int_time_doubleSpinBox)
        else:
            self.collect_apd.update_value(False)
            self.collect_apd.change_readonly(True)

        if 'lightfield' in self.app.hardware.keys():
            self.app.hardware['lightfield'].settings.exposure_time.connect_bidir_to_widget(
                self.ui.spectrum_int_time_doubleSpinBox)
        else:
            self.collect_spectrum.update_value(False)
            self.collect_spectrum.change_readonly(True)



        if 'hydraharp' in self.app.hardware.keys():
            self.app.hardware['hydraharp'].settings.Tacq.connect_to_widget(
                self.ui.hydraharp_tacq_doubleSpinBox)
        else:
            self.collect_lifetime.update_value(False)
            self.collect_lifetime.change_readonly(True)



        # Plot
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater()              # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
        
        self.plot1 = self.graph_layout.addPlot(title="Polarization Scan(Collection path angle)")
        self.plot2 = self.graph_layout.addPlot(title="Polarization Scan(Excitation path angle)")
        
        self.plot_line1 = self.plot1.plot([0])
        self.plot_line2 = self.plot2.plot([0])       # Different lines in a specific plot
        
        
    def update_display(self):
        if hasattr(self, "ii"):
            ii = self.ii
        else:
            ii = 0


        if hasattr(self, 'Excitation_Stage_position'):
            X2 = self.Excitation_Stage_position[:ii]
            #print('Excitation Loaded')
                
        if hasattr(self, 'Collection_Stage_position'):
            X1 = self.Collection_Stage_position[:ii]
            #print('Changed to Collection')
        
        
        if self.settings['collect_apd']:
            self.plot_line1.setData(X1, self.apd_count_rates[:ii])
            self.plot_line2.setData(X2, self.apd_count_rates[:ii])
        elif self.settings['collect_lifetime']:
            self.plot_line1.setData(X1, self.hydraharp_histograms[:ii, :].sum(axis=1)/self.hydraharp_elapsed_time[:ii])
            self.plot_line2.setData(X2, self.hydraharp_histograms[:ii, :].sum(axis=1)/self.hydraharp_elapsed_time[:ii])
        elif self.settings['collect_spectrum']:
            if hasattr(self, 'integrated_spectra'):
                self.plot_line1.setData(X1, self.integrated_spectra[:ii])
                self.plot_line2.setData(X2, self.integrated_spectra[:ii])
            self.lightfield_readout.update_display()
        elif self.settings['collect_Si_powermeter']:
            if hasattr(self, 'Si_pm_reading'):
                self.plot_line1.setData(X1, self.Si_pm_reading[:ii])
                self.plot_line2.setData(X2, self.Si_pm_reading[:ii])
        elif self.settings['collect_Ge_powermeter']:
            if hasattr(self, 'Ge_pm_reading'):
                self.plot_line1.setData(X1, self.Ge_pm_reading[:ii])
                self.plot_line2.setData(X2, self.Ge_pm_reading[:ii])




    def run(self):

        self.err = False
        ####Temporary
        #self.settings['x_axis'] = 'Excitation_Stage_position'
        self.x_axis_flag = 1

        # Create Data Arrays

        self.Excitation_Stage_position = []
        self.Collection_Stage_position = []
        self.Int_min = 0
        self.Int_max = 0


        ##############################
        if self.use_shutter.val == True:
            print ('Now closing shutter...')
            self.app.hardware.dual_position_slider.move_fwd()


        # hardware and delegate measurements
        self.Excitation_Stage_hw = self.app.hardware.MotorizedStageExcitation
        self.Excitation_Stage_dev = self.Excitation_Stage_hw.Motorized_Stage_Excitation
        self.Collection_Stage_hw = self.app.hardware.MotorizedStageCollection
        self.Collection_Stage_dev = self.Collection_Stage_hw.Motorized_Stage_Collection

        # avoid fixing two stages together
        if (self.Fix_Excitation_Stage.value == True & self.Fix_Collection_Stage.value == True):
            self.err = True



        ######## Connect hardware components here
        if self.settings['collect_apd']:
            self.apd_counter_hw = self.app.hardware.apd_counter
            self.apd_count_rate_lq = self.apd_counter_hw.settings.apd_count_rate

        if self.settings['collect_lifetime']:
            self.ph_hw = self.app.hardware['hydraharp']

        if self.settings['collect_spectrum']:
            self.lightfield_readout = self.app.measurements['lightfield_readout']

        if self.settings['collect_Si_powermeter']:
            self.Si_pm_hw = self.app.hardware['thorlabs_powermeter_Si']

        if self.settings['collect_Ge_powermeter']:
            self.Ge_pm_hw = self.app.hardware['thorlabs_powermeter_Ge']



            # Regulate the step size
        self.Np = Np = self.Step_ndatapoints.val

        self.step_size_Excitaion =  (self.Excitation_max.val-self.Excitation_min.val)/(Np-1)

        self.step_size_Collection =  (self.Collection_max.val-self.Collection_min.val)/(Np-1)

        
        

        ##### Fix the stage by setting the step to be 0
        if self.Fix_Excitation_Stage.value == True:
            self.step_size_Excitaion = 0
            self.x_axis_flag = 1


        if self.Fix_Collection_Stage.value == True:
            self.step_size_Collection = 0
            self.x_axis_flag = 0

        print ('********Excitation Step Size = %.2f'%self.step_size_Excitaion)
        print ('********Collection Step Size = %.2f'%self.step_size_Collection)



        if self.settings['collect_apd']:

            self.apd_count_rates = []

        if self.settings['collect_lifetime']:
            Nt = self.num_hist_chans = self.ph_hw.calc_num_hist_chans()
            self.hydraharp_time_array = np.zeros(Nt, dtype=float)
            self.hydraharp_elapsed_time = np.zeros(Np, dtype=float)
            self.hydraharp_histograms = np.zeros((Np,Nt ), dtype=int)

        if self.settings['collect_spectrum']:
            self.spectra = [] # don't know size of ccd until after measurement
            self.integrated_spectra = []

        if self.settings['collect_Si_powermeter']:
            self.Si_pm_reading = []

        if self.settings['collect_Ge_powermeter']:
            self.Ge_pm_reading = []



            ### Acquire data


        self.ii = 0

        # loop through power wheel positions
        for ii in range(self.Np):
            self.ii = ii

            Excitaion_ins_target_pos = self.Excitation_min.value + ii*self.step_size_Excitaion
            Collection_ins_target_pos = self.Collection_min.value + ii*self.step_size_Collection

            print ('*****Current Ext Pol: %.2f'%Excitaion_ins_target_pos)
            print ('*****Current Col Pol: %.2f'%Collection_ins_target_pos)

            if self.interrupt_measurement_called:
                break
            if self.err:
                break
            # go to the instant pos
            self.Excitation_Stage_dev.go_to_pos(Excitaion_ins_target_pos)
            self.Collection_Stage_dev.go_to_pos(Collection_ins_target_pos)

            # record stages position
            self.Excitation_Stage_position.append(self.Excitation_Stage_dev.current_pos())
            self.Collection_Stage_position.append(self.Collection_Stage_dev.current_pos())



            #########Open shutter
            if self.use_shutter.val == True:
                print ('Now opening shutter...')
                self.app.hardware.dual_position_slider.move_bkwd()

            # read detectors
            if self.settings['collect_apd']:

                self.apd_count_rates.append(self.apd_counter_hw.settings.apd_count_rate.read_from_hardware())
            if self.settings['collect_lifetime']:
                hh = self.hh_hw.hydraharp
                hh.start_histogram()
                while not hh.check_done_scanning():
                    if self.interrupt_measurement_called:
                        break
                    hh.read_histogram_data()
                    self.hh_hw.settings.count_rate0.read_from_hardware()
                    self.hh_hw.settings.count_rate1.read_from_hardware()
                    time.sleep(0.1)
                hh.stop_histogram()
                hh.read_histogram_data()
                self.hydraharp_histograms[ii,:] = hh.histogram_data[0:Nt]
                self.hydraharp_time_array =  hh.time_array[0:Nt]
                self.hydraharp_elapsed_time[ii] = hh.read_elapsed_meas_time()

            if self.settings['collect_spectrum']:
                self.lightfield_readout.ro_acquire_data()
                spec = np.array(self.lightfield_readout.img)
                self.spectra.append( spec )
                wls = np.array(self.lightfield_readout.wls)

                if self.Int_max == 0 & self.Int_min == 0 :
                    self.Int_min = min(range(len(wls)), key=lambda i: abs(wls[i]-self.IntegrationRange_min.val))   #Finde the index of desired min/max in wls
                    self.Int_max = min(range(len(wls)), key=lambda i: abs(wls[i]-self.IntegrationRange_max.val))

                Int_spec = spec[self.Int_min : self.Int_max]
                
                self.ratio = self.Polarization_Compensation_Ratio.val/100*np.sin(ii*self.step_size_Collection/180*np.pi);
                self.integrated_spectra.append(Int_spec.sum()*(1+self.ratio))                                        ########### where to compensate the polarization dependent

            if self.settings['collect_Si_powermeter']:
                pm_reading_now = self.Si_pm_hw.settings.power.read_from_hardware()
                self.Si_pm_reading.append(pm_reading_now)

            if self.settings['collect_Ge_powermeter']:
                pm_reading_now = self.Ge_pm_hw.settings.power.read_from_hardware()
                self.Ge_pm_reading.append(pm_reading_now)



            #########Closing shutter
            if self.use_shutter.val == True:
                print ('Now closing shutter...')
                self.app.hardware.dual_position_slider.move_fwd()


        ######################################## End of Loop #################################################
        # write data to h5 file on disk

        self.t0 = time.time()


        self.h5_file = h5_io.h5_base_file(app=self.app,measurement=self)
        try:
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)

            #create h5 data arrays

            if self.settings['collect_apd']:
                H['apd_count_rates'] = np.array(self.apd_count_rates)
            if self.settings['collect_lifetime']:
                H['hydraharp_elapsed_time'] = self.hydraharp_elapsed_time
                H['hydraharp_histograms'] = self.hydraharp_histograms
                H['hydraharp_time_array'] = self.hydraharp_time_array
            if self.settings['collect_spectrum']:
                H['wls'] = self.lightfield_readout.wls
                H['spectra'] = np.squeeze(np.array(self.spectra))
                H['integrated_spectra'] = np.array(self.integrated_spectra)
            if self.settings['collect_Si_powermeter']:
                H['pm_reading'] = np.array(self.Si_pm_reading)
            if self.settings['collect_Ge_powermeter']:
                H['pm_reading'] = np.array(self.Ge_pm_reading)



            H['Excitation_Stage_Position'] = np.array(self.Excitation_Stage_position)
            H['Collection_Stage_Position'] = np.array(self.Collection_Stage_position)
            H['Fix_Excitation'] = self.Fix_Excitation_Stage.value
            H['Fix_Collection'] = self.Fix_Collection_Stage.value
            H['IntegrationRange_min'] = self.IntegrationRange_min.value
            H['IntegrationRange_max'] = self.IntegrationRange_max.value
            H['Polarization_Compensation_Ratio(% per 10 deg)'] = self.Polarization_Compensation_Ratio.value

        finally:
            self.log.info("data saved "+self.h5_file.filename)
            self.h5_file.close()



