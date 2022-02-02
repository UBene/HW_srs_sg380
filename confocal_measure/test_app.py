'''
Created on Sep 17, 2021

@author: lab
'''
from ScopeFoundry.base_app import BaseMicroscopeApp
from confocal_measure.sequencer import Sequencer

class APP(BaseMicroscopeApp):

    name = 'test_app'

    def setup(self):

        print("Adding Measurement Components")
        self.add_measurement(Sequencer)


if __name__ == '__main__':
    import sys
    app = APP(sys.argv)
    sys.exit(app.exec_())
