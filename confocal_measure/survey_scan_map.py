from ScopeFoundry import Measurement, BaseMicroscopeApp
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
import numpy as np
import pyqtgraph as pg
from qtpy import QtGui 
import time
from ScopeFoundry import h5_io

            
class SurveyScanMap(Measurement):
    
    name = 'survey_scan'
    
    
    def setup(self):
        
        self.settings.New("save_full_images", dtype=bool, initial=False)
        
        img_scale = self.settings.New("img_scale", dtype=float, unit='um', initial=280.)
        #img_scale.add_listener(self.on_new_img_scale)
        
#         lq = self.settings.New("img_opacity", unit="%", dtype=int, initial=100, vmin=0, vmax=100)
#         #lq.add_listener(self.on_new_img_opacity)
# 
#         lq = self.settings.New("edge_fade", unit="%", dtype=int, initial=10, vmin=0, vmax=100)
#         lq.add_listener(self.on_new_edge_fade)


        self.settings.New("center_x", dtype=float, unit='%', initial=50)
        self.settings.New("center_y", dtype=float, unit='%', initial=50)
        

        self.settings.New("x0", dtype=float, unit="um", initial=-1000)
        self.settings.New("x1", dtype=float, unit="um", initial=+1000)
        self.settings.New("y0", dtype=float, unit="um", initial=-1000)
        self.settings.New("y1", dtype=float, unit="um", initial=+1000)

        self.settings.New("speed", dtype=float, unit='um/s', initial=1000)


        self.settings.New("camera_exposure", dtype=float, unit="s", spinbox_decimals=6, initial=10e-3, si=True)

        self.settings.New("camera", dtype=str, initial="toupcam", choices=('toupcam', 'flircam', 'genicam'))

        self.settings.New('flip_x', dtype=bool)
        self.settings.New('flip_y', dtype=bool)


    def setup_figure(self):
        
        self.ui = load_qt_ui_file(sibling_path(__file__, "tiled_large_area_map.ui"))
        
        #self.app.hardware['toupcam'].settings.connected.connect_to_widget(self.ui.camera_connect_checkBox)
        #self.ui.clear_all_pushButton.clicked.connect(self.clear_snaps)
        self.settings.activation.connect_to_widget(self.ui.run_checkBox)
        #self.ui.snap_pushButton.clicked.connect(self.snap)
        
        
        
        self.graph_layout = self.ui.graph_layout
        self.plot = self.graph_layout.addPlot()
        #import pyqtgraph.widgets.RawImageWidget as RIW
        #self.imwidget = RIW.RawImageWidget()
        #self.ui.plot_groupBox.layout().addWidget(self.imwidget)
        
        #self.imview = pg.ImageView()
        #self.ui.plot_groupBox.layout().addWidget(self.imview)
        
        #self.img_item = pg.ImageItem()
        #self.plot.addItem(self.img_item)
        #self.img_item.setZValue(1000)

        self.plot.setAspectLocked(lock=True, ratio=1)
        
        self.pre_run()
        

        
    def pre_run(self):
        self.plot.clear()
        self.img_items = dict()
#         for ij, img_item in self.img_items.items():
#             img_item
        self.current_stage_pos_arrow = pg.ArrowItem()
        self.current_stage_pos_arrow.setZValue(1001)
        self.plot.addItem(self.current_stage_pos_arrow)

        cstage = self.app.hardware['asi_stage']

        cstage.settings.x_position.updated_value.connect(self.update_arrow_pos)
        cstage.settings.y_position.updated_value.connect(self.update_arrow_pos)


        S = self.settings
        x0 = S['x0']
        x1 = S['x1']
        y0 = S['y0']
        y1 = S['y1']

        self.bounds_plotline = self.plot.plot(color='r')
        self.bounds_plotline.setData(
            [x0, x1,x1,x0, x0], [y0, y0, y1, y1,y0]
            )
        
        self.bounds_plotline.setZValue(1002)
        
        self.settings.x0.add_listener(self.on_update_bounds)
        self.settings.x1.add_listener(self.on_update_bounds)
        self.settings.y0.add_listener(self.on_update_bounds)
        self.settings.y1.add_listener(self.on_update_bounds)
        
        self.img_map_img_item = pg.ImageItem()
        self.plot.addItem(self.img_map_img_item)



    def run(self):
        S = self.settings
        x0 = S['x0']
        x1 = S['x1']
        y0 = S['y0']
        y1 = S['y1']
        
        if self.settings['camera'] == 'toupcam':
            tcam = self.app.hardware['toupcam']
            tcam.settings['connected'] = True
        elif self.settings['camera'] == 'flircam':
            fcam = self.app.hardware['flircam']
            fcam.settings['connected'] = True
        elif self.settings['camera'] == 'genicam':
            gcam = self.app.hardware['genicam']
            gcam.settings['connected'] = True
            gcam.ia.start_image_acquisition()



        #fstage = self.app.hardware['mcl_xyz_stage']
        cstage = self.app.hardware['asi_stage']

        #fstage.settings['connected'] = True
        cstage.settings['connected'] = True
        time.sleep(0.25)

        
        if self.settings['camera'] == 'toupcam':
            tcam.settings['auto_exposure'] = False
            tcam.settings['exposure'] = S['camera_exposure']
            
#         elif self.settings['camera'] == 'flircam':
#             fcam.settings['auto_exposure'] = 0
#             fcam.settings['exposure'] = S['camera_exposure']
       
        
        #self.images = dict()
        self.strip_rects = dict()
        #self.timestamps = dict()
        #self.xys = dict()
        self.image_strips = dict()

        
        # Move to Origin
        cstage.settings['speed_xy'] = 5.0 # Full speed!
        cstage.settings['x_target'] = x0*1e-3
        cstage.settings['y_target'] = y0*1e-3
        t_start = time.time()
        while cstage.is_busy_xy():
            if time.time() - t_start > 10.0:
                print("stage took too long to move to start, fail")
                return

        # Take a snapshot to get pixel size, dimensions and aspect-ratio
        if self.settings['camera'] == 'toupcam':
            self.toupcam_clear_image_and_timestamp_fifo()
            time.sleep(0.1)
            ts, self.im = self.toupcam_pop_image_and_timestamp_fifo()
            self.im = np.flip(self.im.swapaxes(0,1),0)
            print("shape", self.im.shape)
        elif self.settings['camera'] == 'flircam':
            cam = self.app.hardware['flircam']
            self.im = cam.cam.get_image()
            self.im = self.im.swapaxes(0,1)
        elif self.settings['camera'] == 'genicam':
            cam = self.app.hardware['genicam']
            self.im = cam.fetch_image()
            self.im = self.im.swapaxes(0,1)
            
        
        self.im_aspect = self.im.shape[1]/self.im.shape[0]

        
        scale = self.settings['img_scale'] # um per full frame x
        Nx, Ny, Nchan = self.im.shape
        um_per_px = scale / Nx

        #y_step = Ny*um_per_px*0.95 # 5% overlap
        y_step = Ny*um_per_px*0.50 # 50% overlap
        print("y_step", y_step)
        y_array = np.arange(y0, y1, y_step)

        # Define strip size in pixels
        Nx_strip = int(abs(x1-x0) / um_per_px) + Nx
        
        N_strips = len(y_array)
        
        # Define whole map size in pixels
        Ny_map = int(abs(y1-y0) / um_per_px) + Ny
        
        self.img_map = np.zeros( (Nx_strip, Ny_map, Nchan), dtype=np.uint8)
        self.img_map_rect = (
                    x0 - S['center_x']*Nx*um_per_px/100,
                    y0  - S['center_y']*Ny*um_per_px/100, 
                    um_per_px*Nx_strip,
                    um_per_px*Ny_map)
        self.img_map[:,:,0] = 128
        
        # Setup HDF5 File
        h5file = h5_io.h5_base_file(self.app, measurement=self)
        M = h5_io.h5_create_measurement_group(self, h5file)
        M.create_dataset("image_strips", (N_strips, Nx_strip,Ny,Nchan), dtype=np.uint8)
        M['y_array'] = y_array
        M.create_dataset("strip_rects", (N_strips, 4), dtype=float)
        
        if S['save_full_images']:
            images = []
            image_coords = []
            image_times = []
            images_h5 = h5_io.create_extendable_h5_dataset(
                                M, 'images', (1, Nx, Ny,Nchan), axis=0, dtype=np.uint8)
            image_coords_h5 = h5_io.create_extendable_h5_dataset(
                                M, 'image_coords', (1, 2), axis=0, dtype=float)
            image_times_h5 = h5_io.create_extendable_h5_dataset(
                                M, 'image_times', (1,), axis=0, dtype=float)
            
        
        image_i = 0
        
        try:
            for j,y in enumerate(y_array):
                if self.interrupt_measurement_called:
                    break
                
                self.set_progress(100*(j+0.5)/N_strips)
    
                # Create empty strip image
                img_strip = self.image_strips[j] = np.zeros((Nx_strip,Ny,Nchan), dtype=np.uint8)
                #print("img_strip shape", img_strip.shape)
                
                self.strip_rects[j] =(  
                    x0 - S['center_x']*Nx*um_per_px/100,
                    y  - S['center_y']*Ny*um_per_px/100, 
                    um_per_px*Nx_strip,
                    um_per_px*Ny)
                
                M['strip_rects'][j] = self.strip_rects[j]
    
                #print("strip rect:", self.strip_rects[j])
                
                # Move Y
                cstage.settings['y_target'] = y*1e-3
                t_start = time.time()
                while cstage.is_busy_xy():
                    if time.time() - t_start > 1.0:
                        print("stage took too long to move, fail")
                        break
    
                # Move to start of line at full speed
                cstage.settings['speed_xy'] = 5.0 #mm/s
                cstage.settings['x_target'] = x0*1e-3
                while cstage.is_busy_xy():
                    if time.time() - t_start > 15.0:
                        print("stage took too long to move, fail")
                        break
                # Settle time
                time.sleep(0.5)
    
                    
                # Slow down for stripe scan
                cstage.settings['speed_xy'] = S['speed']/1000. 
                speed = 1e3*cstage.settings['speed_xy'] # um/s
                
                if self.settings['camera'] == 'toupcam':
                    # Dump buffer of old images
                    self.toupcam_clear_image_and_timestamp_fifo()
    
                # Start X-motion
                print("starting line", j," at ", x0, "traveling to", x1)
                cstage.settings['x_target'] = x1*1e-3
                t_start = time.time()
                
                if self.settings['camera'] == 'flircam':
                    cam = self.app.hardware['flircam']
                    ts, _ = cam.cam.get_image(return_timestamp=True)
                    t_start = ts*1e-9 # convert from ns -> seconds
                elif self.settings['camera'] == 'genicam':
                        cam = self.app.hardware['genicam']
                        ts, _ = cam.fetch_image(return_timestamp=True)
                        t_start = ts*1e-9 # convert from ns -> seconds (CHECK!)                    
    
                i = 0 # count of images capture in strip
                while cstage.is_busy_xy():
                    if self.settings['camera'] == 'toupcam':
                        ts, self.im = self.toupcam_pop_image_and_timestamp_fifo()
                        if ts is None:
                            continue
                        self.im = np.flip(self.im.swapaxes(0,1),0)
                    elif self.settings['camera'] == 'flircam':
                        cam = self.app.hardware['flircam']
                        ts, self.im = cam.cam.get_image(return_timestamp=True)
                        self.im = np.flip(self.im.swapaxes(0,1))
                        ts = ts*1e-9 # convert from ns -> seconds
                        #time.sleep(0.05)
                    elif self.settings['camera'] == 'genicam':
                        cam = self.app.hardware['genicam']
                        ts, self.im = cam.fetch_image(return_timestamp=True)
                        self.im = np.flip(self.im.swapaxes(0,1))

                        ts = ts*1e-9 # convert from ns -> seconds (CHECK!)

    
                    #predicted x position:
                    # ts is timestamp of image
                    x = x0 + np.sign(x1-x0)*speed*(ts-t_start)                
    
                    ii0 = int( (x - x0) / um_per_px )
                    if not (0 < ii0 < img_strip.shape[0]):
                        continue
                    
                    jj0 = int( (y - y0) / um_per_px )
                    jj1 = jj0 + Ny
    
                    try:
                        clip = 300 #int(Nx*0.25)
                        img_strip[ii0+clip:ii0+Nx-clip,:,:] =\
                            self.im[clip:-clip,:,:]
                    except Exception as err:
                        print("skipping image", i,  err)
                        
                    try:
                        clip = 300
                        self.img_map[ii0+clip:ii0+Nx-clip, jj0:jj1, :] = \
                            self.im[clip:-clip,:,:]
                    except Exception as err:
                        print(f"skipping image {i} at ({x}{y}). Err: {err}")

                    if S['save_full_images']:
                        #h5_io.extend_h5_dataset_along_axis(images_h5, new_len=image_i+1, axis=0)
                        #images_h5[image_i,:,:,:] = self.im
                        #h5_io.extend_h5_dataset_along_axis(image_coords_h5, new_len=image_i+1, axis=0)
                        #image_coords_h5[image_i,:] = (x,y)
                        #h5_io.extend_h5_dataset_along_axis(image_times_h5, new_len=image_i+1, axis=0)
                        #image_times_h5[image_i] = ts
                        #print("Saving image", image_i)
                        images.append(self.im)
                        image_coords.append( (x,y) )
                        image_times.append(ts)

                    i+=1
                    image_i += 1
                    
                # After Strip
                
                # Save all full images in the strip to h5
                if S['save_full_images']:
                    N = images_h5.shape[0]
                    h5_io.extend_h5_dataset_along_axis(images_h5, new_len=image_i, axis=0)
                    h5_io.extend_h5_dataset_along_axis(image_coords_h5, new_len=image_i, axis=0)
                    h5_io.extend_h5_dataset_along_axis(image_times_h5, new_len=image_i, axis=0)
                    for n in range(N, image_i):
                        images_h5[n] = images[n]
                        image_coords_h5[n] = image_coords[n]
                        image_times_h5[n] = image_times_h5[n]
                    

                h5file.flush()
                
                # Copy strip to h5    
                M['image_strips'][j] = self.image_strips[j]
        finally:
            print("closing h5file", h5file)
            h5file.close()
            
            if self.settings['camera'] == 'genicam':
                cam = self.app.hardware['genicam']
                cam.ia.stop_image_acquisition()


            
    def update_display(self):
        #return
        t0 = time.time()
        
        self.display_update_period = 0.5
        if not hasattr(self, 'img_items'):
            self.img_items = dict()

        for j, img_strip in self.image_strips.items():
            if not j in self.img_items.keys():
                img_item = self.img_items[j] = pg.ImageItem()
                self.plot.addItem(img_item)
                print("plot pizel size", self.plot.getViewBox().viewPixelSize())
                p,_ = self.plot.getViewBox().viewPixelSize()
                if p < 4:
                    img_item.setImage(img_strip[:,::-1,:], levels=(0,255), autoLevels=False)#, levels=(0,255), autoDownsample=True)
                else:
                    img_item.setImage(img_strip[::8,::-8,:], levels=(0,255), autoLevels=False)#, levels=(0,255), autoDownsample=True)
                    
                img_item.setRect(pg.QtCore.QRectF(*self.strip_rects[j]))

            
            else:
                img_item = self.img_items[j]
                img_item.updateImage()

            print("strip pixel size", j, img_item.pixelSize())
#         if not hasattr(self, 'img_map_img_item'):
#             print("Asdf")
#             self.img_map_img_item = pg.ImageItem()
#         self.plot.addItem(self.img_map_img_item)
        print("ASdf2")
        #self.img_map_img_item.setImage(self.img_map[:,:,:])
        #self.img_map_img_item.setRect(pg.QtCore.QRectF(*self.img_map_rect))
        #self.imview.setImage(self.img_map, autoLevels=False)
        #self.imwidget.setImage(self.img_map)
        print('update_display took {} seconds'.format(time.time() - t0))


            
    def toupcam_pop_image_and_timestamp_fifo(self):
        cam = self.app.hardware['toupcam'].cam

        ts, data = cam.pop_image_and_timestamp_fifo()
        if ts == None:
            return None, None
        raw = data.view(np.uint8).reshape(data.shape + (-1,))
        bgr = raw[..., :3]
        return (ts, bgr[..., ::-1])
    
    def toupcam_clear_image_and_timestamp_fifo(self):
        cam = self.app.hardware['toupcam'].cam
        cam.clear_image_and_timestamp_fifo()


    def get_current_stage_position(self):
        #fstage = self.app.hardware['mcl_xyz_stage']
        cstage = self.app.hardware['asi_stage']
        
        x = 1e3*cstage.settings['x_position']# + fstage.settings['x_position']
        y = 1e3*cstage.settings['y_position']# + fstage.settings['y_position']
        #x = 1e3*cstage.settings['x_target']# + fstage.settings['x_position']
        #y = 1e3*cstage.settings['y_target']# + fstage.settings['y_position']
        return x,y


    def get_current_rect(self, x=None, y=None):
        if x is None:
            x,y = self.get_current_stage_position()
        scale = self.settings['img_scale']
        S = self.settings
        return (x-S['center_x']*scale/100,
                y-S['center_y']*scale*self.im_aspect/100, 
                scale,
                scale*self.im_aspect)
        
        
    def update_arrow_pos(self):
        x,y = self.get_current_stage_position()
        self.current_stage_pos_arrow.setPos(x,y)
        
    def on_update_bounds(self):
        S = self.settings
        x0 = S['x0']
        x1 = S['x1']
        y0 = S['y0']
        y1 = S['y1']

        self.bounds_plotline.setData(
            [x0, x1,x1,x0, x0], [y0, y0, y1, y1,y0]
            )



class SurveyScanMapCalib(Measurement):
    
    name = 'survey_scan_calib'
    
    def setup(self):
    
        self.settings.New('shift_distance', unit="um")
        
        img_scale = self.settings.New("img_scale", dtype=float, unit='um', initial=50.)
        img_scale.add_listener(self.on_new_img_scale)
        
        lq = self.settings.New("img_opacity", unit="%", dtype=int, initial=100, vmin=0, vmax=100)
        lq.add_listener(self.on_new_img_opacity)

        lq = self.settings.New("edge_fade", unit="%", dtype=int, initial=10, vmin=0, vmax=100)
        lq.add_listener(self.setImages)

        lq = self.settings.New("center_x", dtype=float, unit='%', initial=50)
        lq.add_listener(self.on_new_img_scale)
        lq = self.settings.New("center_y", dtype=float, unit='%', initial=50)
        lq.add_listener(self.on_new_img_scale)

        
        lq = self.settings.New('flip_x', dtype=bool)
        lq.add_listener(self.setImages)
        lq = self.settings.New('flip_y', dtype=bool)
        lq.add_listener(self.setImages)
        
        rot = self.settings.New("rotation", dtype=float, vmin=-180, vmax=180, initial=3.40, unit='deg')
        rot.add_listener(self.on_new_img_scale)

        

        
        

    def setup_figure(self):
        self.graph_layout = self.ui = pg.GraphicsLayoutWidget()
        self.plot = self.graph_layout.addPlot()

        self.plot.setAspectLocked(lock=True, ratio=1)
        
    def pre_run(self):
        self.plot.clear()
        self.img_items = dict()
        self.centers_plotdata = self.plot.plot(pen=None, symbol='x')
        self.centers_plotdata.setZValue(1000)
        
    def run(self):
        cstage = self.app.hardware['asi_stage']

        # starting stage position (in um)
        x0 = cstage.settings['x_position']*1e3
        y0 = cstage.settings['y_position']*1e3

        
        try:
            cstage.settings['x_target'] = x0*1e-3
            cstage.settings['y_target'] = y0*1e-3
    
            x_shift = self.settings['shift_distance']
            y_shift = x_shift / 1.6
            
            self.images = dict()
            self.xy_positions = dict()
            
            ij_list = [ (i,j) for j in range(-2,3) for i in range(-2,3)]
            
    #        for i,j in [(0,0), (0,1), (1,1), (1,0)]:        
            for i,j in ij_list:
                if self.interrupt_measurement_called:
                    break
                
                print(i,j)
                
                x = (x0+i*x_shift)
                y = (y0+j*y_shift)
                
                cstage.settings['x_target'] = x*1e-3
                cstage.settings['y_target'] = y*1e-3
    
                while cstage.is_busy_xy():
                    time.sleep(0.1)
    
                cam = self.app.hardware['flircam']
                im = cam.cam.get_image()
                im = im.swapaxes(0,1)
                
    
            
                self.im_aspect = im.shape[1]/im.shape[0]
    
                self.images[(i,j)] = im
                self.xy_positions[(i,j)] = (x,y)
        finally:
            # Go back to starting point
            cstage.settings['x_target'] = (x0)*1e-3
            cstage.settings['y_target'] = (y0)*1e-3


            
        
    def update_display(self):
        t0 = time.time()
        
        self.display_update_period = 0.01
        
        
        if not hasattr(self, 'img_items'):
            self.img_items = dict()
        
        for ij, img in self.images.items():
            if not ij in self.img_items.keys():
                img_item = self.img_items[ij] = pg.ImageItem()
                self.plot.addItem(img_item)
            #img_item = self.img_items[ij]  
            #print("setImage", ij, img.shape)
            #img_item.setImage(img, autoLevels=False)
        
        self.setImages() 
        self.on_new_img_scale()
        self.on_new_img_opacity()
        
        
        #if not hasattr(self, 'centers_plotdata'):
            
            
    def on_new_img_scale(self):
        S = self.settings
        xs = []
        ys = []
        for ij, img in self.images.items():
            img_item = self.img_items[ij]  
            x, y = self.xy_positions[ij]
            xs.append(x)
            ys.append(y)
            
            scale = self.settings['img_scale'] # um per full frame x
            Nx, Ny, Nchan = img.shape
            um_per_px = scale / Nx

            img_rect = (
                    x - S['center_x']*Nx*um_per_px/100,
                    y  - S['center_y']*Ny*um_per_px/100, 
                    um_per_px*Nx,
                    um_per_px*Ny)

            #print(ij, img_rect)
            #img_item.setImage(255*np.ones((100,100,3), dtype=np.uint8))
            
            
            #img_item.setRect(pg.QtCore.QRectF(*img_rect))
#           #img_item.rotate(self.settings['rotation'])
            
            """
            QT Transforms follow this pattern:
            
            The item's base transform is applied (transform())
            The item's transformations list is applied in order (transformations())
            The item is rotated relative to its transform origin point (rotation(), transformOriginPoint())
            The item is scaled relative to its transform origin point (scale(), transformOriginPoint())

            """
            
            
            #sets the transform from pixel coordinates to real-space coordinates
            
            def T_scale(s):
                return  np.array(
                    [[s, 0, 0],
                     [0, s, 0],
                     [0, 0, 1]])
            def T_rotate(deg):
                rad = deg*np.pi/180.
                return np.array(
                    [[+np.cos(rad), +np.sin(rad), 0],
                     [-np.sin(rad), +np.cos(rad), 0],
                     [0           ,            0, 1]])
            def T_translate(tx,ty):
                return np.array([
                    [1, 0, tx],
                    [0, 1, ty],
                    [0, 0, 1]])
            
            q = Nx/2
                
            T =(
                T_translate(x,y) @ 
                T_scale(um_per_px) @ 
                #T_translate(+Nx*S['center_x']/100,+Ny*S['center_y']/100) @ 
                T_rotate(self.settings['rotation']) @
                T_translate(-Nx*S['center_x']/100,-Ny*S['center_y']/100) 
                )
            
            
            img_item.setTransform(QtGui.QTransform(*T.T.flat))
            
            
            
            
        self.centers_plotdata.setData(xs, ys)


    def on_new_img_opacity(self):
        op = self.settings['img_opacity']*0.01
        for img_item in list(self.img_items.values()):
            img_item.setOpacity(op)
            
    #def on_new_edge_fade(self):
    def setImages(self):
        for ij, img in list(self.images.items()):
            if self.settings['flip_x']:
                img = np.flip(img, axis=0)
            if self.settings['flip_y']:
                print("flip_y")
                img = np.flip(img, axis=1)
            img_item = self.img_items[ij]  
            im_alpha = edge_fade_img(img, tukey_alpha=0.01*self.settings['edge_fade'])
            img_item.setImage(im_alpha, autoLevels=True)
            
    
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



