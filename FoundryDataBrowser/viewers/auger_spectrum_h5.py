from ScopeFoundry.data_browser import DataBrowserView
import numpy as np
import h5py
import pyqtgraph as pg
from scipy import interpolate
from qtpy import QtWidgets
import os

'''
To fix:
now multi line mostly works
    need either legend or scroll through list with highlight/info, maybe remove one
    list of plots/spectra, fix colors

    parse/display date time?
'''

class AugerSpectrumH5(DataBrowserView):
    #interface to data browser

    name = 'auger_spectrum_h5'
    data_chans = 7  #omicron energy analyzer

    def setup(self):        
            # define interactive viewer controls 
        self.settings.New("Epass_correct", dtype=bool, initial=False)
        self.settings.New("derivative", dtype=bool, initial=False)
        self.settings.New("smooth_data", dtype=bool, initial=False)
        self.settings.New('points', dtype=int, initial=4, vmin = 3, vmax = 50)
        self.settings.New("raw_data", dtype=bool, initial=False)
        self.settings.New("background", dtype=bool, initial=False)
        self.settings.New("loss_ratio", dtype=int, initial=87, vmin = 50, vmax = 100)
        self.settings.New("loss_eV", dtype=int, initial=50, vmin = 5, vmax = 200)

        self.settings.New("add_ref_spec", dtype=bool, initial=False)
        self.settings.New("clear_refs", dtype=bool, initial=False)
        
#         for set in self.settings:
#             set.add_listener(self.update_display)      
        self.settings.raw_data.add_listener(self.update_display)
        self.settings.Epass_correct.add_listener(self.update_display)
        self.settings.derivative.add_listener(self.update_display)
        self.settings.smooth_data.add_listener(self.update_display)
        self.settings.points.add_listener(self.update_display)
        self.settings.background.add_listener(self.update_display)
        self.settings.loss_ratio.add_listener(self.update_display)
        self.settings.loss_eV.add_listener(self.update_display)
        
        self.settings.add_ref_spec.add_listener(self.on_add_ref)
        self.settings.clear_refs.add_listener(self.on_clear_refs)
            
            #render UI
        self.ui = QtWidgets.QWidget()
        self.ui.setLayout(QtWidgets.QHBoxLayout())
        self.ui.layout().addWidget(self.settings.New_UI(), stretch=0)
        self.info_label = QtWidgets.QLabel()
        self.ui.layout().addWidget(self.info_label, stretch=0)
        
            # setup QtGraph
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.ui.layout().addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title="Auger Spectrum")
        self.plot.getAxis('bottom').setGrid(255)
        #self.plot.addLegend()
        self.plot_setup()   
    
 
    def on_change_data_filename(self, fname):        
        try:
            if hasattr(self, 'dat'):
                self.dat.close()
                
            self.dat = h5py.File(fname, 'r')
            self.spec = AugerSpec(fname,self.dat)
            
            self.update_display()
            self.databrowser.ui.statusbar.showMessage("Loaded:" + fname)
            
        except Exception as err:
            self.databrowser.ui.statusbar.showMessage("failed to load %s:\n%s" %(fname, err))
            raise(err)
    
    def on_add_ref(self):
        '''create new reference line based on current spec'''
        pen=pg.mkPen(pg.intColor(len(self.ref_list)+1),width=1)
        line = self.plot.plot([0], pen=pen )
        self.ref_list.append( (self.spec, line) )
        self.settings['add_ref_spec']=False
        self.update_display()
        
    def on_clear_refs(self):
        '''remove reference lines'''
        for p in self.ref_list:
            p[1].clear()
        self.ref_list = []
        self.settings['clear_refs']=False
        self.update_display()
        
    def is_file_supported(self, fname):
        return "auger_spectrum.h5" in fname      
      
    def plot_setup(self):
        ''' create plots for channels and/or sum'''
        print('plot_setup')
        
        self.ref_list = [] #for multiple reference lines        
        self.plot_line = self.plot.plot([0], pen=pg.mkPen('r',width=2)) #for browser file
        
            #channel by channel raw display
        self.raw_lines = []
        for i in range(self.data_chans):
            name = 'Chan {:d}'.format(i)
            self.raw_lines.append( self.plot.plot([0], pen=pg.intColor(i), name=name) )
        #self.plot.setTitle("test")
        
    def clear_plots(self,mode='browse'):
        '''hide plots not needed for current mode, removes data'''
        if mode=='browse':
            for line in self.raw_lines:
                line.clear()
        if mode=='raw':
            self.plot_line.clear()
            for p in self.ref_list:
                p[1].clear()                   

    def update_display(self):
        if not hasattr(self, 'spec'):
            return;
        print("update disp",self.spec.fname) 
               
        if self.settings['raw_data']:
            self.raw_plot()
            return;
        else:
            self.clear_plots()
        
        for p in self.ref_list:
            print('plot ref')
            self.display_plots(*p)
        self.display_plots(self.spec,self.plot_line)
        
        self.axis_labels()
             
    def display_plots(self,spec,line):
        '''display data in existing line based on modes'''
        
        if self.settings['Epass_correct']:
            rate = spec.pass_energy_correct(self.settings['Epass_correct'])
        else:
            rate=spec.rate
        if self.settings['derivative']:
            rate = spec.deriv_data(rate,self.settings['points'])
        elif self.settings['smooth_data']:
            rate = spec.smooth_data(rate,self.settings['points'])
        if self.settings['background'] and not self.settings['derivative']:
            rate = spec.tougaard( rate, 0.01*self.settings['loss_ratio'], self.settings['loss_eV'])

        line.setData(self.spec.ke, rate, name=self.spec.fname)
            
    def raw_plot(self):
        '''display seven channels of raw data counts, no rate conversion, dead time correction etc'''
        self.clear_plots('raw')
        for i in range(self.data_chans):
            self.raw_lines[i].setData(*self.spec.chan_raw(i))
        self.axis_labels()
        
    def axis_labels(self):
        '''adjust plot view axis labels based on mode'''
        self.plot.setLabel('bottom',text="Kintic Energy",units='eV')
        if self.settings['raw_data']:
            self.plot.setLabel('left',text="Counts",units='Cts')       
        elif self.settings['derivative']:
            self.plot.setLabel('left',text="Derivative rate",units='Hz/eV')       
        elif self.settings['Epass_correct']:
            self.plot.setLabel('left',text="Pass energy normalized rate",units='Hz')       
        else:
            self.plot.setLabel('left',text="Count rate",units='Hz')        

class AugerSpec:
    
    name = 'auger_spec'
    
    #instrument specific parameters
    display_chans = 7
    dispersion = 0.02   #Omicron SCA per-channel resolution/pass energy
    dead_time = 70e-9   #for electron counting dead time correction

    def __init__(self,fname,dat):        
        print( 'AugerSpec init')
        # extract data from hdf5                        
        self.path = fname
        self.fname = os.path.basename(fname)
        A = dat['app/settings']
        self.save_dir = A.attrs['save_dir']
        self.sample = A.attrs['sample']
           
        M = dat['measurement/auger_spectrum']
        self.chan_data = M['chan_data']
        self.chan_ke = M['ke']
        self.dwell_time = M['settings'].attrs['dwell']
        self.pass_energy = M['settings'].attrs['pass_energy']
        self.crr_ratio = M['settings'].attrs['crr_ratio']
        self.cae = M['settings'].attrs['CAE_mode']
        self.ke_start = M['settings'].attrs['ke_start']
        self.ke_end = M['settings'].attrs['ke_end']
        self.ke_delta = M['settings'].attrs['ke_delta']
        
        self.data()

    def chan_raw(self,index):
        # raw counts per channel as acquired
        x = self.chan_ke[index,:]
        y = self.chan_data[index,:]
        return x,y
    
    def chan_rate(self,index):
        # convert raw counts to count rate with dead time correction
        y = np.asarray(self.chan_data[index,:],dtype=np.float64)
        y /= self.dwell_time #rate
        y = y / (1 - self.dead_time * y) #dead time
        return y
        
    def data(self):                                
        #sum auger channels, correct for analyzer dispersion       
        self.ke = np.arange(self.ke_start,self.ke_end,self.ke_delta,dtype=float)
        self.rate = np.zeros_like(self.ke)
        for i in range(self.display_chans):
            x = self.chan_ke[i,:]
            y = self.chan_rate(i)
            ff = interpolate.interp1d(x,y,bounds_error=False,fill_value='extrapolate')
            self.rate += ff(self.ke)

    def pass_energy_correct(self,correct):
        #normalize counts by spec resolution, Hz/eV
        if self.cae:
            return self.rate / (self.dispersion * self.pass_energy)
        else:
            return self.rate * self.crr_ratio / (self.dispersion * self.ke)
        
    def tougaard( self, rate, ratio, loss ):
        #Tougaard background correction
        norm_rate = rate - rate[-1]
#            delta function test simulation
#         rate = np.zeros_like(rate)
#         rate[rate.size-100] = 1000
        t_kernel = self.kernel(ratio, loss, self.ke_delta)
        conv = self.ke_delta * np.convolve(norm_rate,t_kernel[::-1],mode='full')
        print('size kernel',t_kernel.size, 'back', conv.size, 'rate', rate.size)
#         if norm_rate.size > t_kernel.size:
#         else:
        back = conv[-norm_rate.size::]
        return norm_rate - back
    
    def kernel( self, ratio, loss, dE):
        """Physical convolution kernel for Tougaard background"""
        dE = np.abs(dE)
        x = np.arange(0,self.ke_end,self.ke_delta,dtype=float)
        y= (8.0/np.pi**2)*ratio*loss**2 * x / ((2.0*loss/np.pi)**2 + x**2)**2

        #B, C = p
        #K_ = B * E / (C + E**2)**2
        y = y*(y>0) #positive definite    
        return y
    
    def smooth_data(self,y,points):        
        points = 2*points+1
        if points < 7:
            order = 2
        else:
            order = 4
        return savitzky_golay(y, 2*points+1, order)

    def deriv_data(self,y,points):        
        points = 2*points+1
        if points < 7:
            order = 2
        else:
            order = 4
        return savitzky_golay(y, 2*points+1, order, deriv=1)/self.ke_delta
    
'''
    Smooth (and optionally differentiate) data with a Savitzky-Golay filter.
    The Savitzky-Golay filter removes high frequency noise from data.
    It has the advantage of preserving the original shape and
    features of the signal better than other types of filtering
    approaches, such as moving averages techniques.
    Parameters
    ----------
    y : array_like, shape (N,)
        the values of the time history of the signal.
    window_size : int
        the length of the window. Must be an odd integer number.
    order : int
        the order of the polynomial used in the filtering.
        Must be less then `window_size` - 1.
    deriv: int
        the order of the derivative to compute (default = 0 means only smoothing)
    Returns
    -------
    ys : ndarray, shape (N)
        the smoothed signal (or it's n-th derivative).
    Notes
    -----
    The Savitzky-Golay is a type of low-pass filter, particularly
    suited for smoothing noisy data. The main idea behind this
    approach is to make for each point a least-square fit with a
    polynomial of high order over a odd-sized window centered at
    the point.
    Examples
    --------
    t = np.linspace(-4, 4, 500)
    y = np.exp( -t**2 ) + np.random.normal(0, 0.05, t.shape)
    ysg = savitzky_golay(y, window_size=31, order=4)
    import matplotlib.pyplot as plt
    plt.plot(t, y, label='Noisy signal')
    plt.plot(t, np.exp(-t**2), 'k', lw=1.5, label='Original signal')
    plt.plot(t, ysg, 'r', label='Filtered signal')
    plt.legend()
    plt.show()
    References
    ----------
    .. [1] A. Savitzky, M. J. E. Golay, Smoothing and Differentiation of
       Data by Simplified Least Squares Procedures. Analytical
       Chemistry, 1964, 36 (8), pp 1627-1639.
    .. [2] Numerical Recipes 3rd Edition: The Art of Scientific Computing
       W.H. Press, S.A. Teukolsky, W.T. Vetterling, B.P. Flannery
       Cambridge University Press ISBN-13: 9780521880688
'''

def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    from math import factorial
    
    window_size = np.abs(np.int(window_size))
    order = np.abs(np.int(order))
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')

            
