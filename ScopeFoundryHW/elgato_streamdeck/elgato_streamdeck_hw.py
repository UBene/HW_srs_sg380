from ScopeFoundry import HardwareComponent
from .StreamDeck import StreamDeck as StreamDeck
from qtpy import  QtCore
import numpy as np

class ElgatoStreamDeckHW(HardwareComponent):
    
    name = 'stream_deck'
    
    key_changed_signal = QtCore.Signal((int,bool)) 
    key_pressed_signal = QtCore.Signal(int)
    key_released_signal = QtCore.Signal(int)
    
    def setup(self):
        
        self.settings.New('dev_num', dtype=int, initial=0)
        self.settings.New('brightness', dtype=int, initial=50, unit="%")
        
    def connect(self):
        S = self.settings
                
        manager = StreamDeck.DeviceManager()
        decks = manager.enumerate()

        print("Found {} Stream Decks.".format(len(decks)), flush=True)

        self.deck = d = decks[S['dev_num']]
        
        d.open()
        d.reset()
        d.set_brightness(S['brightness'])
    
        #for k in range(d.key_count()):
        #    d.set_key_image(k, get_random_key_colour_image(d))
    
        current_key_states = d.key_states()
        print("Initial key states: {}".format(current_key_states))
    
        d.set_key_callback(self.key_change_callback)
        
        S.brightness.connect_to_hardware(write_func = self.deck.set_brightness)
        
        self.key_changed_signal.connect(self.signal_listener)

    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'deck'):
            self.deck.close()
            
    
    def key_change_callback(self, deck, key, state):
        #print("Deck {} \n\tKey {} = {}".format(deck.id(), key, state), flush=True)
        
        self.key_changed_signal.emit(key,state)
        if state: # key pressed 
            self.key_pressed_signal.emit(key)
        else: # key released
            self.key_released_signal.emit(key)
    
    def signal_listener(self, key,state):
        print("signal_listener", key, state, flush=True)
        
        
    def connect_key_to_lq_toggle(self, key_num, lq,text="", active_color=(0,255,0), inactive_color=(255,0,0)):
                
        def set_key_img_state(state):
            if state:
                self.set_key_image(key_num, 
                                   self.text_img(text, fgcolor=(0,0,0), bgcolor=active_color))
            else:
                self.set_key_image(key_num, 
                                   self.text_img(text, fgcolor=(0,0,0), bgcolor=inactive_color))
        
        def on_lq_update():
            state = lq.value
            set_key_img_state(state)
        lq.add_listener(on_lq_update)
    
        def on_key_pressed(k):
            if k == key_num:
                lq.update_value(not lq.value)
                set_key_img_state(lq.value)
                
        self.key_pressed_signal.connect(on_key_pressed)
        set_key_img_state(lq.value)
    
    def connect_key_to_lq_momentary(self, key_num, lq, text="", active_color=(0,255,0), inactive_color=(255,0,0)):
        
        def set_key_img_state(state):
            if state:
                #self.deck.set_key_image(key_num, self.solid_color_img((0,255,0)).flat)
                self.set_key_image(key_num, 
                                   self.text_img(text, fgcolor=(0,0,0), bgcolor=active_color))
            else:
                #self.deck.set_key_image(key_num, self.solid_color_img((0,0,255)).flat)
                self.set_key_image(key_num, 
                                   self.text_img(text, fgcolor=(0,0,0), bgcolor=inactive_color))

        def on_lq_update():
            state = lq.value
            set_key_img_state(state)
        lq.add_listener(on_lq_update)
        
        def on_key_changed(k, state):
            if k == key_num:
                lq.update_value(state)
                set_key_img_state(state)
        self.key_changed_signal.connect(on_key_changed)
        
        set_key_img_state(lq.value)
    
    
    def add_key_press_listener(self, key_num, callback):        
        def on_key_pressed(k):
            if k == key_num:
                callback()
        self.key_pressed_signal.connect(on_key_pressed)
    
    def set_key_image(self,key_num, img):
        self.deck.set_key_image(key_num, np.array(img)[:,::-1,::-1].flat)
    
    def solid_color_img(self, color):
        key_image_format = self.deck.key_image_format()
    
        width, height = (key_image_format['width'], key_image_format['height'])
        depth = key_image_format['depth']

        #grid_x, grid_y = np.mgrid[0:1:width*1j, 0:1:height*1j]
        img = np.zeros((height, width, depth), dtype=int)

        img[:,:,0] = color[0]
        img[:,:,1] = color[1]
        img[:,:,2] = color[2]
        return img
    
    
    def text_img(self, text, fgcolor=(255,255,255), bgcolor=(0,0,0)):
        key_image_format = self.deck.key_image_format()
        Nx, Ny = (key_image_format['width'], key_image_format['height'])

        A = np.zeros((Ny,Nx,3), dtype=int)
        for i in range(3):
            A[:,:,i] = bgcolor[i]

        def px_func(i,j):
            A[j,i,:] = fgcolor
            
        from . import bitmapfont

        with bitmapfont.BitmapFont(Ny,Nx, px_func) as bf:
            bf.text(text, 5,5)
            
        return A
    
    
    def img_icon(self, icon_name, text="", bgcolor=(255,255,255), textcolor=(0,0,0)):
        from . import bitmapfont
        from PIL import Image
        
        def add_text_to_img(img, text, loc=(0,0), color=(0,0,0)):
            A = img.load()
        
            def px_func(i,j):
                A[i,j] = color
                
            Ny, Nx = img.size
        
            with bitmapfont.BitmapFont(Ny,Nx, px_func) as bf:
                bf.text(text, *loc)
                
            return img

        bg = Image.new('RGBA',(72,72),bgcolor)
        fg = Image.new('RGBA',(72,72),(0,0,0,0))
        ico = Image.open("open-iconic-png/{}-6x.png".format(icon_name))
        fg.paste(ico,(12,6))
        #fg = fg.resize((72,72))
        #bg.paste(fg)
        #bg
        combined = Image.alpha_composite(bg,fg)
        add_text_to_img(combined, text, loc=(5,60), color=textcolor)
        return np.array(combined.convert('RGB'))


        