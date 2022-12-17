import logging

from thorlabs_optical_chopper_HW import ThorlabsOpticalChopperHW

from ScopeFoundry.base_app import BaseMicroscopeApp

level = logging.INFO
logging.basicConfig(level=level)
logging.getLogger('PyQt5').setLevel(level)
logging.getLogger('PyQt6').setLevel(level)


class App(BaseMicroscopeApp):

    name = 'thorlabs_optical_chopper_test_app'

    def setup(self):
        self.add_hardware(ThorlabsOpticalChopperHW(self))


if __name__ == '__main__':

    import sys
    app = App(sys.argv)
    sys.exit(app.exec_())
