"""
Created on Jan 15, 2023

@author: Benedikt Ursprung
"""
from ScopeFoundry.scanning.base_raster_slow_scan import BaseRaster2DSlowScan

import time


class Base2DSlowScan(BaseRaster2DSlowScan):

    name = "mdt690x_base_2d_slow_scan"

    def __init__(self, app, use_external_range_sync=False, circ_roi_size=0.001, h_limits=(-150, 150), v_limits=(-150, 150), h_unit="V", v_unit="V"):
        BaseRaster2DSlowScan.__init__(self, app, h_limits=h_limits, v_limits=v_limits, h_unit=h_unit, v_unit=v_unit,
                                      use_external_range_sync=use_external_range_sync,
                                      circ_roi_size=circ_roi_size)

    def setup(self):
        BaseRaster2DSlowScan.setup(self)

        self.settings.New("h_axis", initial="x", dtype=str,
                          choices=("x", "y", "z"))
        self.settings.New("v_axis", initial="y", dtype=str,
                          choices=("x", "y", "z"))

        self.stage = self.app.hardware['mdt690x_piezo_controller']

    def _move_position(self, h, v):
        print(self.name, 'moved', h, v)
        S = self.settings
        h_axis, v_axis = S['h_axis'], S['v_axis']
        SS = self.stage.settings
        SS[f"{h_axis}_target_position"] = h
        SS[f"{v_axis}_target_position"] = v

        # SS.x_position.read_from_hardware()
        # SS.y_position.read_from_hardware()
        # SS.z_position.read_from_hardware()

    def move_position_fast(self, h, v, dh, dv):
        self._move_position(h, v)

    def move_position_slow(self, h, v, dh, dv):
        self._move_position(h, v)

    def move_position_start(self, h, v):
        self._move_position(h, v)

    def collect_pixel(self, pixel_num, k, j, i):
        print(self.name, pixel_num, k, j, i)
        time.sleep(0.1)

    def setup_figure(self):
        BaseRaster2DSlowScan.setup_figure(self)
        self.stage.settings.x_target_position.add_listener(
            self.update_arrow_pos)
        self.stage.settings.y_target_position.add_listener(
            self.update_arrow_pos)
        self.stage.settings.z_target_position.add_listener(
            self.update_arrow_pos)

        self.ui.details_groupBox.layout().addWidget(
            self.settings.New_UI(include=('h_axis', 'v_axis')))

    def update_arrow_pos(self):
        S = self.settings
        h_axis, v_axis = S['h_axis'], S['v_axis']
        x = self.stage.settings[f"{h_axis}_target_position"]
        y = self.stage.settings[f"{v_axis}_target_position"]
        self.current_stage_pos_arrow.setPos(x, y)
