'''
Created on Jun 15, 2021

@author: lab
'''
from confocal_measure.stage_live_cam import StageLiveCam
from ScopeFoundry.measurement import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
import pyqtgraph as pg
from qtpy import QtCore, QtGui
from qtpy.QtCore import Qt
import numpy as np
import time


class LiveCamTiledLargeAreaMapMeasure(Measurement):
    '''requires 
    - StageLiveCam implementation
    '''


    name = "tiled_large_area_map"
    
    new_snap_signal = QtCore.Signal()
        
    def __init__(self, app, name=None, ):
        Measurement.__init__(self, app=app, name=name)        

        
    def setup(self):

        
        lq = self.settings.New("img_opacity", unit="%", dtype=int, initial=100, vmin=0, vmax=100)
        lq.add_listener(self.on_new_img_opacity)

        lq = self.settings.New("edge_fade", unit="%", dtype=int, initial=10, vmin=0, vmax=100)
        lq.add_listener(self.on_new_edge_fade)


        self.add_operation('Clear All', self.clear_snaps)
        self.add_operation('Snap', self.snap)
        
        
        self.settings.New('Nh', initial=10, dtype=int)
        self.settings.New('Nv', initial=10, dtype=int)
        self.add_operation('explore', self.explore)
        
        self.set_coarse_stage()
        
        
        self.snaps = []

    def set_coarse_stage(self):
        self.cstage_x_position = None#self.app.attocube_xy_stage.x_position
        self.cstage_y_position = None#self.app.attocube_xy_stage.x_position
        
        self.cstage_x_target_position = None#self.app.attocube_xy_stage.x_position
        self.cstage_y_target_position = None#self.app.attocube_xy_stage.x_position
        
        
    
    def setup_figure(self):
        #self.graph_layout = self.ui= pg.GraphicsLayoutWidget()
        
        self.ui = load_qt_ui_file(sibling_path(__file__, "tiled_large_area_map.ui"))        
        self.plot.scene().sigMouseClicked.connect(self.on_scene_clicked)
    
        self.graph_layout_eventProxy = EventProxy(self.graph_layout, self.graph_layout_event_filter)
        
        self.current_stage_pos_arrow = pg.ArrowItem()
        self.current_stage_pos_arrow.setZValue(1001)
        self.plot.addItem(self.current_stage_pos_arrow)

        self.cstage_x_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)
        self.cstage_y_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)

        self.fine_stage_border_plotline = self.plot.plot([0,1,1,0,0],[0,0,1,1,0],pen='r')

        
    def get_current_rect(self, x=None, y=None):
        if x is None:
            x,y = self.get_current_stage_position()
        scale = self.settings['img_scale']
        S = self.settings
        return pg.QtCore.QRectF(x-S['center_x']*scale/100,
                                y-S['center_y']*scale*self.im_aspect/100, 
                                scale,
                                scale*self.im_aspect)





    def update_arrow_pos(self):
        cx, cy = self.cstage_x_position.value(), self.cstage_y_position.value()
        self.current_stage_pos_arrow.setPos(cx,cy)
    
    
    def update_display(self):
        im_alpha = edge_fade_img(self.im, tukey_alpha=0.01*self.settings['edge_fade'])
        #print(alpha.shape, self.im.shape)
        self.img_item.setImage(im_alpha)
        self.img_rect = self.get_current_rect()
        self.img_item.setRect(self.img_rect)
        
    def get_current_stage_position(self):
        #fstage = self.app.hardware['mcl_xyz_stage']
        cstage = self.app.hardware['attocube_xyz_stage']
        
        x = self.cstage_x_position #+ fstage.settings['x_position']
        y = self.cstage_y_position #+ fstage.settings['y_position']
        return x,y

        


    def run(self):
        
        tcam = self.app.hardware['toupcam']
        tcam.settings['connected'] = True
        
        
        #fstage = self.app.hardware['mcl_xyz_stage']
        cstage = self.app.hardware['attocube_xyz_stage']

        #fstage.settings['connected'] = True
        cstage.settings['connected'] = True
        
        self.im = self.get_rgb_image()
        self.im = np.flip(self.im.swapaxes(0,1),0)
        self.im_aspect = self.im.shape[1]/self.im.shape[0]
        
        
        from ScopeFoundry import h5_io

        try:
            self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
    
            self.snaps_h5 = H.create_dataset('snaps', (self.im.shape + (1,)), dtype=np.uint8, maxshape=(self.im.shape +(None,)))
            self.snaps_c_pos_h5 = H.create_dataset('snaps_coarse_pos', (2,1), dtype='float', maxshape=(2,None))
            #self.snaps_f_pos_h5 = H.create_dataset('snaps_fine_pos', (2,1), dtype='float', maxshape=(2,None))
            self.snaps_pos_h5 = H.create_dataset('snaps_pos', (2,1), dtype='float', maxshape=(2,None))
    
            while not self.interrupt_measurement_called:
                self.im = self.get_rgb_image()
                self.im = np.flip(self.im.swapaxes(0,1),0)
                self.im_aspect = self.im.shape[1]/self.im.shape[0]
                time.sleep(0.1)
        finally:
            print('heelooo')            
            #self.h5_file.close()
            
    def explore(self,):
        S = self.settings
        
        Nh,Nv = int(S['Nh']),int(S['Nv'])
        
        cstage = self.app.hardware['attocube_xyz_stage']
        x0 = cstage.settings['x_position']
        y0 = cstage.settings['y_position']
        
        dh = S["img_scale"]*0.9
        dv = dh*756.0/1024 
        for i in range(Nh) :
            for j in range(Nv):
                cstage.settings['x_target_position'] = x0 + (i - Nh//2) * dh 
                cstage.settings['y_target_position'] = y0 + (j - Nv//2) * dv
                print('moving to ',i,j, x0 + (i - Nh//2) * dh, y0 + (j - Nv//2) * dv)
                time.sleep(1)
                self.snap()
                
                
            
    def snap(self):

        snap = dict()
        
        snap['img'] = self.im.copy()
        snap['img_item'] = pg.ImageItem(edge_fade_img(snap['img'], tukey_alpha=0.01*self.settings['edge_fade']))
        #snap['img_item_bg'] = pg.ImageItem(self.im)
        snap['img_rect'] = self.get_current_rect()
        snap['img_item'].setRect(snap['img_rect'])
        #snap['img_item_bg'].setRect(snap['img_rect'])
        
        #fstage = self.app.hardware['mcl_xyz_stage'] # Fine
        cstage = self.app.hardware['attocube_xyz_stage'] # Coarse
        
        #snap['fine_pos'] = (fstage.settings['x_position'], fstage.settings['y_position'])
        snap['coarse_pos'] = (cstage.settings['x_position'], cstage.settings['y_position'])
        
        #fx, fy = snap['fine_pos']
        cx, cy = snap['coarse_pos']

        #snap['pos'] = (cx+fx, cy+fy)
        snap['pos'] = (cx, cy)
        
        #snap['img_item_bg'].setZValue(-1)
        #self.plot.addItem(snap['img_item_bg'])
        self.plot.addItem(snap['img_item'])
        
        self.snaps.append(snap)
        print ("SNAP")
                

        ## Write to H5
        self.snaps_h5.resize((self.im.shape +( len(self.snaps),)))
        self.snaps_h5[:,:,:,-1] = self.im
        print("shape", self.snaps_h5.shape)
        self.snaps_c_pos_h5.resize((2, len(self.snaps)))
        self.snaps_c_pos_h5[:,-1] = snap['coarse_pos']
        #self.snaps_f_pos_h5.resize((2, len(self.snaps)))
        #self.snaps_f_pos_h5[:,-1] = snap['fine_pos']
        self.snaps_pos_h5.resize((2, len(self.snaps)))
        self.snaps_pos_h5[:,-1] = snap['pos']
        
        # TODO update LQ's in H5
        
        self.new_snap_signal.emit()
    
    def clear_snaps(self):

        for snap in self.snaps:
            self.plot.removeItem(snap['img_item'])
            
        self.snaps = []
        
    def on_new_img_scale(self):
        for snap in self.snaps:
            x,y = snap['pos']
            snap['img_rect'] = self.get_current_rect(x,y)
            snap['img_item'].setRect(snap['img_rect'])

    def on_new_img_opacity(self):
        op = self.settings['img_opacity']*0.01
        self.img_item.setOpacity(op)
        for snap in self.snaps:
            snap['img_item'].setOpacity(op)
            
    def on_new_edge_fade(self):
        im_alpha = edge_fade_img(self.im, tukey_alpha=0.01*self.settings['edge_fade'])
        self.img_item.setImage(im_alpha)
        for snap in self.snaps:
            im_alpha = edge_fade_img(snap['img'], tukey_alpha=0.01*self.settings['edge_fade'])
            snap['img_item'].setImage(im_alpha)
            
            
    def on_scene_clicked(self, event):
        p = self.plot
        viewbox = p.vb
        pos = event.scenePos()
        if not p.sceneBoundingRect().contains(pos):
            return
                
        pt = viewbox.mapSceneToView(pos)
        print("on_scene_clicked", pt.x(), pt.y())
        
        
        x = pt.x()
        y = pt.y()
        
        
        #fstage = self.app.hardware['mcl_xyz_stage']
        cstage = self.app.hardware['attocube_xyz_stage']
        
        #fx, fy = fstage.settings['x_position'] , fstage.settings['y_position']
        cx, cy = cstage.settings['x_position'] , cstage.settings['y_position']

        #x0,y0 = self.get_current_stage_position()
        x0 = cx# + fx
        y0 = cy# + fy
        
        dx = x - x0
        dy = y - y0
        
        print("dx, dy", dx,dy)
        
        #self.plot.plot([x0,x],[y0,y], pen='r')


        
        
        # Move coarse stage
        if  event.modifiers() == QtCore.Qt.ShiftModifier and event.double():            
            print('Shift+Click', 'double click')
                        
#             cstage.settings['x_target'] = (x-fx)/1000
#             cstage.settings['y_target'] = (y-fy)/1000
            cstage.settings['x_target_position'] = cstage.settings['x_position'] + dx
            cstage.settings['y_target_position'] = cstage.settings['y_position'] + dy
            
        # Move fine stage
        #if  event.modifiers() == QtCore.Qt.ControlModifier and event.double():            
        #    print('Shift+Click', 'double click')
            
            
        #    fstage.settings['x_target'] = fstage.settings['x_position'] + dx
        #    fstage.settings['y_target'] = fstage.settings['y_position'] + dy

    def graph_layout_event_filter(self, obj,event):
        #print(self.name, 'eventFilter', obj, event)
        try:
            if type(event) == QtGui.QKeyEvent:
                
                if event.key() == QtCore.Qt.Key_Space:
                    self.snap()
                    print(event.key(), repr(event.text()), event.isAutoRepeat())
                    #event.accept()
                    #return True
        finally:
            # standard event processing            
            return QtCore.QObject.eventFilter(self,obj, event)



class EventProxy(QtCore.QObject):
    def __init__(self, qobj, callback):
        QtCore.QObject.__init__(self)
        self.callback = callback
        qobj.installEventFilter(self)
        
    def eventFilter(self, obj, ev):
        return self.callback(obj, ev)


class SnapsQTabelModel(QtCore.QAbstractTableModel):
    
    def __init__(self, snaps,*args, **kwargs):
        self.snaps  = snaps
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
            if role == Qt.DisplayRole or role==Qt.EditRole:
                row = index.row()
                col = index.column()
                text = "{} {}".format(row,col)
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
    alpha = 255*alpha_x.reshape(1,Nx)*alpha_y.reshape(Ny,1)
    im_alpha = np.dstack((im, alpha.astype(int)))
    return im_alpha 