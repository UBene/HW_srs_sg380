from ScopeFoundry import HardwareComponent

from .chameleon_laser_dev import ChameleonUltraIILaser


class ChameleonUltraIILaserHW(HardwareComponent):

    name = 'chameleon_laser'

    def setup(self):
        S = self.settings
        S.New('wavelength', float, si=False, unit='nm')
        S.New('uf_power', float, si=False, ro=0, unit='mW')
        S.New('port', str, initial='COM22')

    def connect(self):
        if hasattr(self, 'laser'):
            return
        S = self.settings
        dev = self.dev = ChameleonUltraIILaser(
            port=S['port'], debug=S['debug_mode'])
        S.wavelength.connect_to_hardware(
            dev.read_wavelength, dev.write_wavelength)
        S.uf_power.connect_to_hardware(dev.read_uf_power)

    def disconnect(self):
        if not hasattr(self, 'laser'):
            return
        self.settings.disconnect_all_from_hardware()
        self.dev.close()
        del self.dev
