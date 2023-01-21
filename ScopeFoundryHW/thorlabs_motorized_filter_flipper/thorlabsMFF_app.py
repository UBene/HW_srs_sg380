'''
Created on Feb 28, 2017

@author: Alan Buckley
         Benedikt Ursprung
'''
from ScopeFoundry.base_app import BaseMicroscopeApp


class ThorlabsMFFApp(BaseMicroscopeApp):

    name = "thorlabs_MFF_app"

    def setup(self):
        from ScopeFoundryHW.thorlabs_motorized_filter_flipper.thorlabsMFF_hardware import ThorlabsMFFHW
        self.mff_hw = self.add_hardware(ThorlabsMFFHW(self))

    def setup_ui(self):
        from qtpy import QtWidgets
        widget = QtWidgets.QWidget()
        widget.setMaximumWidth(380)
        layout = QtWidgets.QVBoxLayout(widget)
        self.add_quickbar(widget)

        layout.addWidget(self.mff_hw.New_quick_UI())


if __name__ == '__main__':
    import sys
    app = ThorlabsMFFApp(sys.argv)
    sys.exit(app.exec_())
