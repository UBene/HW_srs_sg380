'''
Created on Sep 17, 2021

@author: lab
'''
from ScopeFoundry.measurement import Measurement
from confocal_measure.sequencer import Sequencer
from ScopeFoundry.base_app import BaseMicroscopeApp


class APP(BaseMicroscopeApp):

    name = 'test_app'

    def setup(self):

        print("Adding Measurement Components")
        self.add_measurement(Sequencer)

        #self.add_measurement(Measurement(self, name='test'))


if __name__ == '__main__':
    import sys
    app = APP(sys.argv)
    sys.exit(app.exec_())
