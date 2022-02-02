import serial
class ThorLabsMCM3000(object):
    
    """
    MCM3000 Direct Serial Communication
    Baud Rate = 9600
    Address = 1
    Conversion factors are for units in nm.
    LNR: 39.0625
    PLS: 211.6667
    AScope Z: 1.0
    BScope: 500.0
    BScope Z: 100.0
    Objective Mover: 1.0
    """
    
    
    def __init__(self, port='COM32'):
        self.port = port
        
        self.ser = serial.Serial(port=self.port, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1.0,) #xonxoff, rtscts, write_timeout, dsrdtr, inter_byte_timeout, exclusive)
        
    
        
    def set_encoder(self, chan=0, ):
        
        """
        This message is used to set the encoder count in the controller
            Command structure (12 bytes):
        
             Header                 | ChanIdent| Encoder Count
             09, 04, 06, 00, 00, 00,| 02, 00, | 00, 00, 00, 00 
             
             09, 04, 06, 00, 00, 00,| 02, 00, | 00, 00, 00, 00 
             
            Field    Description    Format       
            Chan Ident     The channel being addressed    word       
            Encoder count    The new value of the encoder counter as a 32-bit signed integer, encoded in the Intel format. The scaling between real    long     
            
            Example: Set the encoder counter for Axis 2 (stage3) to 0 counts 
            TX 09, 04, 06, 00, 00, 00, 02, 00, 00, 00, 00, 00 
            Position: 00, 00, 00, 00 (0 counts)
        """
        self.ser.write([09, ])
    
    def stop_motion(self, chan=0):
        """
        Stop Command
        This command stops any type of motor move on the specified channel.
        Command structure (6 bytes):  
         
        
         
        Field    Description    Format       
        Chan Ident     The channel being addressed    word       
        Stop Mode    The stop mode defines either an immediate (abrupt) or profiles tops. Set this byte to 0x01 to stop immediately, or to 0x02 to stop in a controller (profiled) manner.     word     
        
        Example: Stop immediately Axis 0 (stage1) 
        TX 65, 04, 02, 01, 00, 00
        """
        
    def query_position(self, chan=0):
        """
        Query Position

        Command structure (6 bytes):
          
        Field    Description    Format       
        Chan Ident     The channel being addressed    word     
        
        Response structure (12 bytes) 
        6 byte header followed by 6 byte data packet as follows:  
        
         
        Field    Description    Format       
        Chan Ident     The channel being addressed    word       
        Encoder count    The new value of the encoder counter as a 32-bit signed integer, encoded in the Intel format. The scaling between real    long     
        
        """
    def goto_position(self, chan=0):
        """
        Go to Position Command
        Command structure (12 bytes):
         
         
        Field    Description    Format       
        Chan Ident     The channel being addressed    word       
        Absolut Distance    The distance to move. This is a 4 byte signed integer that specifies the absolute distance in position encoder counts.     long     
        
        """
    
    def query_motor_status(self, chan=0):
        """
        Query Motor Status (busy or ready)
        Command structure (6 bytes):
         
         
        Field    Description    Format       
        Chan Ident     The channel being addressed    word     
        
        Response:
        Busy: true == (Byte 16) & 0x30
        Axis is set to No Motor: true == (Byte 17) & 0x01
        """
        
    