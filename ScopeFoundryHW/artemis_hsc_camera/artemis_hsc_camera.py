import ctypes
dll = ctypes.cdll.LoadLibrary(r"C:\Windows\SysWOW64\ArtemisHSC.dll")

class ArtemisHSCCamera(object):

	def __init__(self):
		pass
	
	
if __name__ == '__main__':
	
	print dll
		