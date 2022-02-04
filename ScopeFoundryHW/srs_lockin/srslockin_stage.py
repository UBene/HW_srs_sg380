import logger, time

class LockinStage(object):
    DVMAX = 1.0 # max single step in voltage
    DVDTMAX = 20.0 # max rate to change voltage, in volts/sec
    VMIN = 0.0
    VMAX = 10.0
    last_time = -1
    
    def __init__(self, srs, POSMIN=0.0, POSMAX=20.0, zPOSMIN=-10, zPOSMAX=10, channels={'x':1, 'y':2, 'z':3}):
        self.srs = srs
        self.POSMIN = float(POSMIN)
        self.POSMAX = float(POSMAX)
        self.zPOSMIN = float(zPOSMIN)
        self.zPOSMAX = float(zPOSMAX)
        self.channels = channels # map axis to aout channel
        
        #self.setvoltage(1, 0)
        #self.setvoltage(2, 0)
        #self.setvoltage(3, 0)
    
    def close(self):
        self.setvoltage(1, 0)
        self.setvoltage(2, 0)
        self.setvoltage(3, 0)
    
    def voltage2pos(self, v):
        # VMIN=POSMIN, VMAX=POSMAX
        return float(v-self.VMIN)/(self.VMAX-self.VMIN) * (self.POSMAX - self.POSMIN) + self.POSMIN

    def voltage2posZ(self, v):
        # VMIN=POSMIN, VMAX=POSMAX
        return float(v-self.VMIN)/(self.VMAX-self.VMIN) * (self.zPOSMAX - self.zPOSMIN) + self.zPOSMIN
    
    def pos2voltage(self, pos):
        # POSMIN=VMIN, POSMAX=VMAX
        return float(pos-self.POSMIN) / (self.POSMAX - self.POSMIN) * (self.VMAX-self.VMIN) + self.VMIN

    def pos2voltageZ(self, pos):
        # POSMIN=VMIN, POSMAX=VMAX
        print "pos2voltageZ"
        return float(pos-self.zPOSMIN) / (self.zPOSMAX - self.zPOSMIN) * (self.VMAX-self.VMIN) + self.VMIN

    
    def getvoltage(self, channel):
        return self.srs.get_aoutput(channel)
    
    def setvoltage(self, channel, voltage):
        assert self.VMIN <= voltage <= self.VMAX
        current_voltage = self.getvoltage(channel)
        t = time.time()
        
        diff = voltage - current_voltage
        dt = t - self.last_time
        
        if abs(diff) > self.DVMAX:
            # doing a big jump, so do it in steps no bigger than MAX_STEP and
            # at a rate <= MAX_SCAN_RATE
            nsteps = int(abs(diff) / self.DVMAX) + 1
            step = diff / nsteps
            pause = self.DVMAX / self.DVDTMAX
            #print 'srslockin_stage.setvoltage : big jump..'
            #print ' start = %s' % current_voltage
            #print ' stop = %s' % voltage
            #print ' nsteps = %g, step=%g' % (nsteps, step)
            for i in range(nsteps-1):
                v = current_voltage + (i+1)*step
                self.setvoltage(channel, v)
                #self.srs.set_aoutput(channel, v)
                time.sleep(pause)
        elif abs(diff) / dt > self.DVDTMAX:
            # doing a small step but too quickly (dV/dT too big)
            pause = abs(diff) / self.DVDTMAX
            print 'srslockin_stage.setvoltage : changing voltage too quickly, pausing for %gs' % pause
            time.sleep(pause)
        
        # can just do any remaining change in a single step..
        #print 'srslockIN-stage.setvoltage : ch %g : %gV' % (channel, voltage)
        self.srs.set_aoutput(channel, voltage)
        self.last_time = time.time()
        return self.getvoltage(channel)
    
    def getvoltage(self, channel):
        return self.srs.get_aoutput(channel)
    
    def setpos(self, axis, position):
        if axis not in self.channels: return None
        if axis == 'z':
            position = min(self.zPOSMAX, max(self.zPOSMIN, position))
            voltage = self.pos2voltageZ(position)
        elif axis == 'x' or axis =='y':
            position = min(self.POSMAX, max(self.POSMIN, position))
            voltage = self.pos2voltage(position)
        else:
            print "invalid axis"
        
        voltage = min(self.VMAX, max(self.VMIN, voltage))
        self.setvoltage(self.channels[axis], voltage)
        return self.getpos(axis)
    
    def getpos(self, axis):
        if axis not in self.channels: return None
        if axis == 'z':
            return self.voltage2posZ(self.getvoltage(self.channels[axis]))
        elif axis == 'x' or axis =='y':
            return self.voltage2pos(self.getvoltage(self.channels[axis]))
        else:
            print "invalid axis"

    def getx(self): return self.getpos('x')
    def setx(self, pos): return self.setpos('x', pos)
    def gety(self): return self.getpos('y')
    def sety(self, pos): return self.setpos('y', pos)
    def getz(self): return self.getpos('z')
    def setz(self, pos): return self.setpos('z', pos)

if __name__ == '__main__':
    import srslockin
    srs = srslockin.SRSlockin()
    stage = LockinStage(srs, POSMIN=-50, POSMAX=50)
    
    for i in range(20):
        print i, stage.pos2voltage(i)
        #stage.setpos('x', i)
    
    stage.setpos('x', -15)
    stage.setpos('y', -20)
    stage.close()
