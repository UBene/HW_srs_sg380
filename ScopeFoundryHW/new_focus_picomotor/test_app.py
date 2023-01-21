from ScopeFoundry.base_app import BaseMicroscopeApp


class TestApp(BaseMicroscopeApp):

    name = "picomotor_test_app"

    def setup(self):
        from ScopeFoundryHW.new_focus_picomotor.hw import HW
        self.picomotor_hw = self.add_hardware(HW(self))

    def setup_ui(self):
        from qtpy import QtWidgets
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        self.add_quickbar(widget)

        layout.addWidget(self.picomotor_hw.New_quick_UI((1, 2, 3)))


if __name__ == '__main__':
    import sys
    app = TestApp(sys.argv)
    sys.exit(app.exec_())
