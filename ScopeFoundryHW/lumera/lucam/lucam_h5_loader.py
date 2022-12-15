import h5py
import matplotlib.pylab as plt

class LucamH5Loader:
    def __init__(self, filename:str):
        self.filename=filename
        
        with h5py.File(filename) as file:
            M = file['measurement/lucam']
            self.image = M['image'][:]
            self.imshow_extent = M['imshow_extent'][:]
            H = file['hardware/lucam']
            self.exposure = H['settings'].attrs['exposure']
            
    def default_plot(self):
        print(self.filename, 'exposure', self.exposure)
        plt.imshow(self.image*1.0, extent=self.imshow_extent)
        return plt.gca()