"""
Wrapper written by Alan Buckley
modified by Benedikt Ursprung
"""

from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent

from bs4 import BeautifulSoup
import binascii
import requests


class DLIPowerSwitchHW(HardwareComponent):

    def setup(self):

        """
        Sets up LoggedQuantities (see :class:`LoggedQuantity`) and defines which bits are indicative of which outlet.
        `self.outlet_dict` contains the aforementioned bit mapping and is used by :meth:`self.read_outlet_status`
        :returns: None
        """
        self.name = "dli_powerswitch"

        self.outlet_dict = {0b00000001: "Outlet_1",
                            0b00000010: "Outlet_2",
                            0b00000100: "Outlet_3",
                            0b00001000: "Outlet_4",
                            0b00010000: "Outlet_5",
                            0b00100000: "Outlet_6",
                            0b01000000: "Outlet_7",
                            0b10000000: "Outlet_8"}
        # Create logged quantities
        for ii in range(8):
            self.settings.New(name='Outlet_{}_Name'.format(ii + 1), dtype=str, initial='Outlet_{}'.format(ii + 1), ro=True)
            self.settings.New(name='Outlet_{}'.format(ii + 1), dtype=bool, initial=False, ro=False)

        # # Credentials
        self.host = self.settings.New(name='host', initial='192.168.0.101', dtype=str, ro=False)
        self.userid = self.settings.New(name='userid', initial='admin', dtype=str, ro=False)
        self.key = self.settings.New(name='key', initial='1234', dtype=str, ro=False)

        self.dummy_mode = self.add_logged_quantity(name='dummy_mode', dtype=bool, initial=False, ro=False)

        self.add_operation('read_all_states', self.read_outlet_status)
        # self.add_operation('read_outlet_names', self.read_outlet_names)

    def update_server(self, server):
        self.SERVER = server

    def connect(self):
        """Connects logged quantities to hardware write functions with :meth:`connect_to_hardware` (:class:`LoggedQuantity`)"""
        if self.debug_mode.val: self.log.debug("Connecting to Power Switch (Debug)")
        for jj in range(8):
            self.settings.get_lq("Outlet_" + str(jj + 1)).connect_to_hardware(
                write_func=lambda x, onum=(jj + 1): self.write_outlet(onum, x))

        self.read_outlet_status()
        self.read_outlet_names()

    def geturl(self, url='index.htm'):
        """Handles http authentication and then opens the specified url, thereby accessing its contents.
        ==============  =========  =====================================================================
        **Arguments:**  **Type:**  **Description:**    
        url             str        URL suffix after hostname
                                   Example: url='status' if the full URL is:
                                   http://192.168.0.100/status
        ==============  =========  =====================================================================
        :returns: requests.get(*args).content    **Type:** bytes
        """

        SERVER = "http://{}/".format(self.settings['host'])
        full_url = "{}{}".format(SERVER, url)
        request = requests.get(full_url, auth=(self.userid.val, self.key.val,))
        return request.content

    def read_outlet_status(self):
        """Parses the power switch status page for hexidecimal value and extracts a byte indicating which outlets are currently powered on.
        :returns: None
        """
        readout = self.geturl(url="status")
        soup = BeautifulSoup(readout, "html.parser")
        hex_value = soup.select("#state")[0].text
        intout = int(binascii.unhexlify(hex_value)[0])
        for i, j in self.outlet_dict.items():
            if i & intout:
                self.settings['{}'.format(j)] = True
            else:
                self.settings['{}'.format(j)] = False

    def read_outlet_names(self):
        readout = self.geturl(url='index.htm')
        soup = BeautifulSoup(readout, "html.parser")
        substring = soup.select("td")[21].text.split("Action")[1].split("Master")[0]
        for i in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            s = substring.split(i)[1].split("Switch")[0]
            # s maybe "<name> OFF" or "<name> ON" (Note that blankspaces in <name> are allowed)
            if s[-2] == "F":
                self.settings['Outlet_{}_Name'.format(i)] = s[0:-4]
            else:
                self.settings['Outlet_{}_Name'.format(i)] = s[0:-3]

    def write_outlet(self, i, status):
        """
        Sends URL based command to power switch in order to toggle a specified outlet.
        ==============  =========  ====================  =============================
        **Arguments:**  **Type:**  **Description:**      **Available values:**
        i               int        index of outlet       1-8
        status          bool       status of the outlet  ON (True)
                                                         OFF (False)
        ==============  =========  ====================  =============================
        :returns: None
        """
        truth_table = {True: "ON",
                       False: "OFF"}
        status_key = truth_table[status]
        self.geturl(url='outlet?{}={}'.format(i, status_key))

    def disconnect(self):
        """
        Disconnects logged quantities from hardware.
        and deletes low-level device object
        :returns: None
        """
        self.settings.disconnect_all_from_hardware()

        # clean up hardware object
        if hasattr(self, 'switch'):
            del self.switch

    def new_mini_Widget(self):
        from qtpy import QtWidgets
        S = self.settings
        widget = QtWidgets.QGroupBox('DLI Powerswitch')
        widget.setFlat(True)
        layout = QtWidgets.QGridLayout(widget)
        cb = QtWidgets.QCheckBox('connected')
        S.connected.connect_to_widget(cb)
        layout.addWidget(cb, 0, 0, 1, 4)
        for ii in range(8):
            cb = QtWidgets.QCheckBox()
            getattr(S, f'Outlet_{ii+1}').connect_to_widget(cb)
            getattr(S, f'Outlet_{ii+1}_Name').add_listener(cb.setText, str)
            layout.addWidget(cb, ii // 4 + 1, ii % 4)
        return widget
