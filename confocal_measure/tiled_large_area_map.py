from ScopeFoundry.measurement import Measurement
import numpy as np
import pyqtgraph as pg
import time
from qtpy import QtCore, QtGui
from qtpy.QtCore import Qt
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path


class _TiledLargeAreaMapMeasure(Measurement):
    '''
    Not be used directly, see bellow
     - ASIMCLToupcamTiledLargeAreaMapMeasure for an example with two stage (a coarse and a fine stage)
     - AttocubeToupcamTiledLargeAreaMapMeasure for an example with a single stage
    '''

    name = "tiled_large_area_map"

    new_snap_signal = QtCore.Signal()

    def __init__(self, app, name=None,):
        Measurement.__init__(self, app=app, name=name)

    def get_current_rect(self, x=None, y=None):
        if x is None:
            x, y, z = self.get_current_stage_position()
        scale = self.settings['img_scale']
        S = self.settings
        return pg.QtCore.QRectF(x - S['center_x'] * scale / 100,
                                y - S['center_y'] * scale * self.im_aspect / 100,
                                scale,
                                scale * self.im_aspect)

    def setup(self):

        lq = self.settings.New("img_opacity", unit="%", dtype=int, initial=100, vmin=0, vmax=100)
        lq.add_listener(self.on_new_img_opacity)

        lq = self.settings.New("edge_fade", unit="%", dtype=int, initial=10, vmin=0, vmax=100)
        lq.add_listener(self.on_new_edge_fade)

        self.add_operation('Clear All', self.clear_snaps)
        self.add_operation('Snap', self.snap)

        img_scale = self.settings.New("img_scale", dtype=float, unit='um', initial=50.)
        img_scale.add_listener(self.on_new_img_scale)

        self.settings.New("center_x", dtype=float, unit='%', initial=50)
        self.settings.New("center_y", dtype=float, unit='%', initial=50)

        self.settings.New("flip_x", dtype=bool, initial=False)
        self.settings.New("flip_y", dtype=bool, initial=False)

        self.settings.New('survey_scan_activated', bool, initial=False)
        self.settings.New('survey_scan_Nh', initial=2, dtype=int)
        self.settings.New('survey_scan_Nv', initial=3, dtype=int)

        self.snaps = []

    def setup_figure(self):
        self.ui = load_qt_ui_file(sibling_path(__file__, "tiled_large_area_map.ui"))

        self.ui.clear_all_pushButton.clicked.connect(self.clear_snaps)
        self.settings.activation.connect_to_widget(self.ui.run_checkBox)
        self.ui.snap_pushButton.clicked.connect(self.snap)

        self.graph_layout = self.ui.graph_layout
        self.plot = self.graph_layout.addPlot()
        self.img_item = pg.ImageItem()
        self.plot.addItem(self.img_item)
        self.img_item.setZValue(1000)

        self.plot.setAspectLocked(lock=True, ratio=1)

        """self.table_view = QtWidgets.QTableView()
        
        self.table_view_model = SnapsQTabelModel(snaps=self.snaps)
        self.table_view.setModel(self.table_view_model)
        self.table_view.show()
        
        self.new_snap_signal.connect(self.table_view_model.on_update_snaps)
        """

        self.plot.scene().sigMouseClicked.connect(self.on_scene_clicked)

        self.graph_layout_eventProxy = EventProxy(self.graph_layout, self.graph_layout_event_filter)

        self.current_stage_pos_arrow = pg.ArrowItem()
        self.current_stage_pos_arrow.setZValue(1001)
        self.plot.addItem(self.current_stage_pos_arrow)

        self.set_coarse_position_lqs()
        if not self.cstage_x_position is None:
            self.cstage_x_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)
            self.cstage_y_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)

        self.set_fine_position_lqs()
        if not self.fstage_x_position is None:
            self.fstage_x_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)
            self.fstage_y_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)

        self.fine_stage_border_plotline = self.plot.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], pen='r')

        self.set_cam_hw()
        self.cam_hw.settings.connected.connect_to_widget(self.ui.camera_connect_checkBox)        
        self.set_fine_max_position()

    def get_current_coarse_stage_position(self):
        '''override: return (x,y,z) in um (z can be zero)'''
        return (0, 0, 0)

    def set_coarse_stage_position(self, x, y, z=0):
        '''override! set stage position where x,y,z is in um'''
        pass

    def get_current_fine_stage_position(self):
        '''override if applicable: return (x,y,z) in um (z can be zero)'''
        return (0, 0, 0)

    def set_fine_stage_position(self, x, y, z=None):
        '''override if applicable! set stage position where x,y,z is in um'''
        pass

    def set_coarse_position_lqs(self):
        "Override! set x,y position lq"
        self.cstage_x_position = None
        self.cstage_y_position = None

    def set_fine_position_lqs(self):
        "Override! define x,y position lq if applicable"
        self.fstage_x_position = None
        self.fstage_y_position = None

    def set_fine_max_position(self):
        "Override! set fx_max, fy_max in um if applicable"
        self.fx_max = None
        self.fy_max = None

    def set_cam_hw(self):
        '''Override'''
        self.cam_hw = self.app.hardware['toupcam']
        # self.cam_hw = self.app.hardware['flircam']

    def get_rgb_image(self):
        '''Override if not toupcam used'''
        cam = self.app.hardware['toupcam'].cam
        data = cam.get_image_data()
        raw = data.view(np.uint8).reshape(data.shape + (-1,))
        bgr = raw[...,:3]
        return bgr[...,::-1]

    def update_arrow_pos(self):
        x, y, z = self.get_current_stage_position()
        self.current_stage_pos_arrow.setPos(x, y)
        
        
        if self.fx_max != None:
            x0, y0, z0 = self.get_current_coarse_stage_position()
            x1 = x0 + self.fx_max
            y1 = y0 + self.fy_max

            self.fine_stage_border_plotline.setData(
                [x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0]
                )

            self.fine_stage_border_plotline.setZValue(1002)
        else:
            self.fine_stage_border_plotline.setVisible(False)

    def update_display(self):
        im_alpha = edge_fade_img(self.im, tukey_alpha=0.01 * self.settings['edge_fade'])
        # print(alpha.shape, self.im.shape)
        self.img_item.setImage(im_alpha)
        self.img_rect = self.get_current_rect()
        self.img_item.setRect(self.img_rect)

    def get_current_stage_position(self):
        xc, yc, zc = self.get_current_coarse_stage_position()
        xf, yf, zf = self.get_current_fine_stage_position()
        return (xc + xf, yc + yf, zc + zf)

    def move_coarse_stage_delta(self, dx, dy, dz=0):
        x, y, z = self.get_current_stage_position()
        self.set_coarse_stage_position(x + dx, y + dy, z + dz)

    def move_fine_stage_delta(self, dx, dy, dz=0):
        x, y, z = self.get_current_fine_stage_position()
        self.set_fine_stage_position(x + dx, y + dy, z + dz)

    def get_flipped_image(self):
        img = self.get_rgb_image()
        if type(img) == bool:
            return False
        img = np.flip(img.swapaxes(0, 1), 0)

        if self.settings['flip_x']:
            img = img[::-1,:,:]
        if self.settings['flip_y']:
            img = img[:,::-1,:]
        return img

    def run(self):
        self.cam_hw.settings['connected'] = True

        self.im = self.get_flipped_image()
        self.im_aspect = self.im.shape[1] / self.im.shape[0]

        from ScopeFoundry import h5_io

        try:
            self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
            H = self.h5_meas_group = h5_io.h5_create_measurement_group(self, self.h5_file)

            self.snaps_h5 = H.create_dataset('snaps', (self.im.shape + (1,)), dtype=np.uint8, maxshape=(self.im.shape + (None,)))
            self.snaps_c_pos_h5 = H.create_dataset('snaps_coarse_pos', (2, 1), dtype='float', maxshape=(2, None))
            self.snaps_f_pos_h5 = H.create_dataset('snaps_fine_pos', (2, 1), dtype='float', maxshape=(2, None))
            self.snaps_pos_h5 = H.create_dataset('snaps_pos', (2, 1), dtype='float', maxshape=(2, None))

            while not self.interrupt_measurement_called:
                self.im = self.get_flipped_image()
                self.im_aspect = self.im.shape[1] / self.im.shape[0]
                time.sleep(0.1)

                if self.settings['survey_scan_activated']:
                    self._survey_scan()
                    self.settings['survey_scan_activated'] = False

        finally:
            self.h5_file.close()
            print(self.name, 'h5 successfully saved')

    def _survey_scan(self,):
        S = self.settings

        Nh, Nv = int(S['survey_scan_Nh']), int(S['survey_scan_Nv'])

        x0, y0, _ = self.get_current_stage_position()

        dh = S["img_scale"] * (100 - S['edge_fade']) / 100
        dv = dh * self.im_aspect

        for i in range(Nh):
            x, y = x0 + (i - Nh / 2) * dh , y0
            self.set_coarse_stage_position(x, y)
            time.sleep(1.5)
            for j in range(Nv):
                if self.interrupt_measurement_called or self.settings['survey_scan_activated'] == False:
                    self.settings['survey_scan_activated'] = False
                    self.interrupt_measurement_called = False
                    break
                x, y = x0 + (i - Nh / 2) * dh , y0 + (j - Nv / 2) * dv
                self.set_coarse_stage_position(x, y)
                time.sleep(0.5)
                self.snap()

    def snap(self):

        snap = dict()

        snap['img'] = self.im.copy()
        snap['img_item'] = pg.ImageItem(edge_fade_img(snap['img'], tukey_alpha=0.01 * self.settings['edge_fade']))
        # snap['img_item_bg'] = pg.ImageItem(self.im)
        snap['img_rect'] = self.get_current_rect()
        snap['img_item'].setRect(snap['img_rect'])
        # snap['img_item_bg'].setRect(snap['img_rect'])

        cx, cy, cz = self.get_current_coarse_stage_position()
        snap['coarse_pos'] = (cx, cy,)

        fx, fy, fz = self.get_current_fine_stage_position()
        snap['fine_pos'] = (fx, fy,)

        x, y, z = self.get_current_stage_position()
        snap['pos'] = (x, y,)

        self.plot.addItem(snap['img_item'])

        self.snaps.append(snap)
        print ("SNAP")

        # # Write to H5
        self.snaps_h5.resize((self.im.shape + (len(self.snaps),)))
        self.snaps_h5[:,:,:, -1] = self.im
        print("shape", self.snaps_h5.shape)
        self.snaps_c_pos_h5.resize((2, len(self.snaps)))
        self.snaps_c_pos_h5[:, -1] = snap['coarse_pos']
        self.snaps_f_pos_h5.resize((2, len(self.snaps)))
        self.snaps_f_pos_h5[:, -1] = snap['fine_pos']
        self.snaps_pos_h5.resize((2, len(self.snaps)))
        self.snaps_pos_h5[:, -1] = snap['pos']

        # TODO update LQ's in H5

        self.new_snap_signal.emit()

    def clear_snaps(self):

        for snap in self.snaps:
            self.plot.removeItem(snap['img_item'])

        self.snaps = []

    def on_new_img_scale(self):
        for snap in self.snaps:
            x, y = snap['pos']
            snap['img_rect'] = self.get_current_rect(x, y)
            snap['img_item'].setRect(snap['img_rect'])

    def on_new_img_opacity(self):
        op = self.settings['img_opacity'] * 0.01
        self.img_item.setOpacity(op)
        for snap in self.snaps:
            snap['img_item'].setOpacity(op)

    def on_new_edge_fade(self):
        im_alpha = edge_fade_img(self.im, tukey_alpha=0.01 * self.settings['edge_fade'])
        self.img_item.setImage(im_alpha)
        for snap in self.snaps:
            im_alpha = edge_fade_img(snap['img'], tukey_alpha=0.01 * self.settings['edge_fade'])
            snap['img_item'].setImage(im_alpha)

    def on_scene_clicked(self, event):
        p = self.plot
        viewbox = p.vb
        pos = event.scenePos()
        if not p.sceneBoundingRect().contains(pos):
            return

        pt = viewbox.mapSceneToView(pos)
        #print("on_scene_clicked", pt.x(), pt.y())

        x = pt.x()
        y = pt.y()

        x0, y0, z0 = self.get_current_stage_position()

        dx = x - x0
        dy = y - y0

        # Move coarse stage
        if  event.modifiers() == QtCore.Qt.ShiftModifier and event.double():
            # print('Shift+Click', 'double click')
            self.move_coarse_stage_delta(dx, dy, 0)

        # Move fine stage
        if  event.modifiers() == QtCore.Qt.ControlModifier and event.double():
            # print('Ctrl+Click', 'double click')
            self.move_fine_stage_delta(dx, dy, 0)
            if self.get_current_fine_stage_position() == (0, 0, 0):
                print('Warning: get_current_fine_stage_position not defined')

    def graph_layout_event_filter(self, obj, event):
        # print(self.name, 'eventFilter', obj, event)
        try:
            if type(event) == QtGui.QKeyEvent:

                if event.key() == QtCore.Qt.Key_Space:
                    self.snap()
                    print(event.key(), repr(event.text()), event.isAutoRepeat())
        finally:
            return QtCore.QObject.eventFilter(self, obj, event)


class EventProxy(QtCore.QObject):

    def __init__(self, qobj, callback):
        QtCore.QObject.__init__(self)
        self.callback = callback
        qobj.installEventFilter(self)

    def eventFilter(self, obj, ev):
        return self.callback(obj, ev)


class SnapsQTabelModel(QtCore.QAbstractTableModel):

    def __init__(self, snaps, *args, **kwargs):
        self.snaps = snaps
        QtCore.QAbstractTableModel.__init__(self, *args, **kwargs)

    def rowCount(self, *args, **kwargs):
        return len(self.snaps)

    def columnCount(self, *args, **kwargs):
        return 5

    def on_update_snaps(self):
        self.layoutChanged.emit()

    def data(self, index, role=Qt.DisplayRole):
        print("table model data", index, role)
        if index.isValid():
            print("valid")
            if role == Qt.DisplayRole or role == Qt.EditRole:
                row = index.row()
                col = index.column()
                text = "{} {}".format(row, col)
                print(text, index)
                return text
        else:
            print("no data", index)
            return None


def edge_fade_img(im, tukey_alpha=0.5):
    """Converts a Ny x Ny x 3 RGB uint image into an
    RGBA image with a Tukey window as the alpha channel
    for fading overlay tiles together.
    tukey_alpha = 0 -->
    tukey_alpha = 1 -->
    """
    Ny, Nx, _ = im.shape
    from scipy.signal import tukey
    alpha_x = tukey(Nx, alpha=tukey_alpha)
    alpha_y = tukey(Ny, alpha=tukey_alpha)
    alpha = 255 * alpha_x.reshape(1, Nx) * alpha_y.reshape(Ny, 1)
    im_alpha = np.dstack((im, alpha.astype(int)))
    return im_alpha


class _Toupcam:

    def set_cam_hw(self):
        self.cam_hw = self.app.hardware['toupcam']

    def get_rgb_image(self):
        data = self.cam_hw.cam.get_image_data()
        raw = data.view(np.uint8).reshape(data.shape + (-1,))
        bgr = raw[...,:3]
        return bgr[...,::-1]


class _Flircam:

    def set_cam_hw(self):
        self.cam_hw = self.app.hardware['flircam']

    def get_rgb_image(self):
        if not self.cam_hw.img_buffer:
            return False
        else:
            img = self.cam_hw.img_buffer.pop(0).copy()
            return img


class _ASIStage:

    def get_current_coarse_stage_position(self):
        stageS = self.app.hardware["asi_stage"].settings
        return stageS["x_position"] * 1e3, stageS["y_position"] * 1e3, stageS["z_position"] * 1e3

    def set_coarse_stage_position(self, x, y, z=None):
        stageS = self.app.hardware["asi_stage"].settings
        stageS["x_target"] = x * 1e-3
        stageS["y_target"] = y * 1e-3
        if z != None:
            stageS["z_target"] = z * 1e-3

    def set_coarse_position_lqs(self):
        stageS = self.app.hardware["asi_stage"].settings
        self.cstage_x_position = stageS.x_position
        self.cstage_y_position = stageS.y_position


class _MCLASIStage:

    def get_current_coarse_stage_position(self):
        stageS = self.app.hardware["asi_stage"].settings
        return stageS["x_position"] * 1e3, stageS["y_position"] * 1e3, stageS["z_position"] * 1e3

    def set_coarse_stage_position(self, x, y, z=None):
        stageS = self.app.hardware["asi_stage"].settings
        stageS["x_target"] = x * 1e-3
        stageS["y_target"] = y * 1e-3
        if z != None:
            stageS["z_target"] = z * 1e-3

    def set_coarse_position_lqs(self):
        stageS = self.app.hardware["asi_stage"].settings
        self.cstage_x_position = stageS.x_position
        self.cstage_y_position = stageS.y_position

    def get_current_fine_stage_position(self):
        stageS = self.app.hardware["mcl_xyz_stage"].settings
        return stageS["x_position"], stageS["y_position"], stageS["z_position"]

    def set_fine_stage_position(self, x, y, z=None):
        stageS = self.app.hardware["mcl_xyz_stage"].settings
        stageS["x_target"] = x
        stageS["y_target"] = y
        if z != None:
            stageS["z_target"] = z

    def set_fine_position_lqs(self):
        stageS = self.app.hardware["mcl_xyz_stage"].settings
        self.fstage_x_position = stageS.x_position
        self.fstage_y_position = stageS.y_position

    def set_fine_max_position(self):
        self.fx_max = self.app.hardware["mcl_xyz_stage"].settings['x_max']
        self.fy_max = self.app.hardware["mcl_xyz_stage"].settings['y_max']


class _AttocubeStage:

    def get_current_coarse_stage_position(self):
        stageS = self.app.hardware["attocube_xyz_stage"].settings
        return stageS["x_position"] * 1e3, stageS["y_position"] * 1e3, stageS["z_position"] * 1e3

    def set_coarse_stage_position(self, x, y, z=None):
        stageS = self.app.hardware["attocube_xyz_stage"].settings
        stageS["x_target_position"] = x * 1e-3
        stageS["y_target_position"] = y * 1e-3
        if z != None:
            stageS["z_target_position"] = z * 1e-3

    def set_coarse_position_lqs(self):
        stageS = self.app.hardware["attocube_xyz_stage"].settings
        self.cstage_x_position = stageS.x_position
        self.cstage_y_position = stageS.y_position
        # self.cstage_z_position = stageS.z_position


# Only Attocube stage (tested on IR microscope)
class AttocubeToupcamTiledLargeAreaMapMeasure(_AttocubeStage,
                                              _Toupcam,
                                              _TiledLargeAreaMapMeasure):
    pass


# Asi as coarse stage, MCL as fine stage (tested on Hip microscope)
class ASIMCLToupcamTiledLargeAreaMapMeasure(_MCLASIStage,
                                            _Toupcam,
                                            _TiledLargeAreaMapMeasure):
    pass


# Only ASI Stage, (tested on survey microscope).
class ASIFlircamTiledLargeAreaMapMeasure(_ASIStage,
                                         _Flircam,
                                         _TiledLargeAreaMapMeasure):
    pass
