import serial
import time

TRIES_BEFORE_FAILURE = 10
RETRY_SLEEP_TIME = 0.010  # in seconds


class ThorlabsELL6K(object):
    """
    Thorlabs ELL6K Dual Position Slider Kit
    """
    
    def __init__(self, port="COM6", debug = False):
        self.port = port
        self.debug = debug
        
        if self.debug: print("ThorlabsELL6K init, port=%s" % self.port)
        
        self.ser = serial.Serial(port=self.port, baudrate=9600, timeout=1.0)
                          
                          
        # Toggle DTR to reset Arduino
        #self.ser.setDTR(False)
        time.sleep(1)
        # toss any data already received, seeW
        # http://pyserial.sourceforge.net/pyserial_api.html#serial.Serial.flushInput
        self.ser.flushInput()
        #self.ser.flush()
        #self.ser.setDTR(True)       
        time.sleep(0.1)
        self.ser.readline()
    
    def send_cmd(self, cmd):
        if self.debug: print("send_cmd:", repr(cmd))
        self.ser.write(cmd + b"\n")
    
    def ask_cmd(self, cmd):
        if self.debug: print("ask:", repr(cmd))
        self.send_cmd(cmd)
        time.sleep(0.01)
        resp = self.ser.readline()
        if self.debug: print("resp:", repr(resp))
        return resp 

    def move_forward(self):
        """ Non-blocking movement of :steps:
        """
        self.send_cmd(b'0fw')
        #print "steps ", steps
    
    def move_backward(self):
        """ Non-blocking movement of :steps:
        """
        self.send_cmd(b'0bw')
        #print "steps ", steps
    def get_position(self):
        #print("Get Position")
        pos = self.ask_cmd(b'0gp')
        #print "steps ", steps
        pos_s = pos.decode("utf-8")
        if pos_s[9:11] == "00":
            pos_str = "Open"
        elif pos_s[9:11] == "1F":
            pos_str = "Closed"
        else:
            print("Dual slider is at unspecified position")
        return pos_str
    
    def close(self):
        self.ser.close()   
        
if __name__ == '__main__':
    W1 = ThorlabsELL6K(debug=True);
    time.sleep(4)
    W1.move_forward()
    pos1 = W1.get_position()
    print('pos :', pos1)
    #pos1s = pos1.decode("utf-8")
    #print(pos1s[9:11])
    time.sleep(4)
    W1.move_backward()  
    pos2 = W1.get_position()  
    print('pos :', pos2)
    #pos2s = pos2.decode("utf-8")
    #print(pos2s[9:11])
    
    
    W1.close()
    pass