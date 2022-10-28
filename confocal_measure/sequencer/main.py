'''
Created on Sep 17, 2021

@author: lab
'''
from confocal_measure.sequencer import Sequencer, SweepSequencer
from dummy.app import RandomNumberGenerator
from ScopeFoundry.base_app import BaseMicroscopeApp


class App(BaseMicroscopeApp):

    name = 'sequencer_test_app'

    def setup(self):

        self.add_hardware(RandomNumberGenerator(self))

        print("Adding Measurement Components")
        self.add_measurement(Sequencer(self))
        self.add_measurement(SweepSequencer(self))


if __name__ == '__main__':
    import sys
    app = App(sys.argv)
    sys.exit(app.exec_())
