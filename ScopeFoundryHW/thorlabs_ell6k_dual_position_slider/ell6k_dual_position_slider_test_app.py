from ScopeFoundry import BaseMicroscopeApp


class TestApp(BaseMicroscopeApp):

    name = 'dual_slider_test_app'

    def setup(self):
        from ScopeFoundryHW.thorlabs_ell6k_dual_position_slider import ELL6KDualPositionSliderHW
        self.ell_hw = self.add_hardware(
            ELL6KDualPositionSliderHW(self, choices=('A', 'B')))

    def setup_ui(self):
        from qtpy import QtWidgets
        widget = QtWidgets.QWidget()
        widget.setMaximumWidth(380)
        layout = QtWidgets.QVBoxLayout(widget)
        self.add_quickbar(widget)
        layout.addWidget(self.ell_hw.New_quick_UI())


if __name__ == '__main__':
    import sys
    app = TestApp(sys.argv)
    app.exec_()
