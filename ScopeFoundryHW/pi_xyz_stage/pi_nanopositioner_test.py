from __future__ import division
import ctypes
from ctypes import create_string_buffer, c_bool, c_int, c_byte, c_ubyte, c_char, c_char_p, c_short, c_double, cdll, pointer,POINTER, byref


# print platform.architecture()
# 
# if platform.architecture()[0] == '64bit':
#     pilib_path = os.path.abspath(
#                     os.path.join(os.path.dirname(__file__),"PI_64bit/piLib.dll"))
# else:
#     pilib_path = os.path.abspath(
#                     os.path.join(os.path.dirname(__file__),"piLib.dll"))
# 
#     wdapilib_path = os.path.abspath(
#                 os.path.join(os.path.dirname(__file__),"wdapi1010.dll"))
#     wdapidll = cdll.LoadLibrary(wdapilib_path)

pilib_path = r'C:\Users\Public\PI\PI_Programming_Files_PI_GCS2_DLL\noGUI\PI_GCS2_DLL_x64.dll'

print ("loading DLL:", repr(pilib_path))


pilib = cdll.LoadLibrary(pilib_path)
szBuffer = create_string_buffer(40)
iBufferSize = c_int()
iBufferSize = 40
szFilter = c_char()
szFilter = 'E-727'

#pilib.PI_EnumerateUSB.restype = c_int
#PI_TryConnectUSB 
#uid = 0
#print('is connected? ', pilib.PI_IsConnected(uid) )
print("Enuverate USB",pilib.PI_EnumerateUSB(szBuffer, iBufferSize, szFilter))




uid = c_int()
uid = pilib.PI_ConnectUSB(szBuffer) 
#print("Error 1:",pilib.PI_GetError(uid))
print("uid", uid)
tid = c_int()
tid = pilib.PI_TryConnectUSB(szBuffer)
cid = c_int()
cit = pilib.PI_GetControllerID(tid)

pilib.PI_SetErrorCheck(uid, c_bool(True))


eax_axis = c_byte(8)
eax_axis = "1 2 3"
eax = (c_int*3)(1)
#svo = (c_int*3)([1,1,1])
#print("Error 2",pilib.PI_GetError(uid))
#szAnswer = create_string_buffer(8)
iansBufferSize = 8
pilib.PI_GcsCommandset(uid, "*IDN?")

piAnswerSize = c_int()
pilib.PI_GcsGetAnswerSize(uid, byref(piAnswerSize))

szAnswer  = create_string_buffer(piAnswerSize)
pilib.PI_GcsGetAnswer(uid, szAnswer, piAnswerSize)

print("Get Answer ", c_byte(szAnswer) )
print("Error 4",pilib.PI_GetError(uid))
pilib.PI_EAX.argtypes = [c_int, c_byte, c_int]
#print("EAX?",pilib.PI_EAX(uid, eax_axis ,eax))

#print("svo ",pilib.PI_SVO( uid, eax_axis, svo) )
##pilib.PI_CMO( uid, eax_axis, cmo)
#print("svo ", c_bool(svo[2]))
#print('EAX?',pilib.PI_EAX(uid, eax_axis ,eax))
print("Error",pilib.PI_GetError(uid))

#szAxes = c_char("1 2 3")
#pos = (c_double*3)()
#pilib.PI_qPOS.argtypes = [c_int, c_char, POINTER(c_double)]
#pilib.PI_qPOS(uid, '1 2 3' , pos)
szAxes_x = c_byte()
szAxes_x = '1'
szAxes_y = c_byte()
szAxes_y = '2'
szAxes_z = c_byte()
szAxes_z = '3'
min_x = c_double()
min_y = c_double()
min_z = c_double()
pilib.PI_qCMN (uid, szAxes_x, min_x)
pilib.PI_qTMN (uid, szAxes_y, min_y)
pilib.PI_qTMN (uid, szAxes_z, min_z)
max_x = c_double()
max_y = c_double()
max_z = c_double()
pilib.PI_qCMX (uid, szAxes_x, max_x)
pilib.PI_qTMX (uid, szAxes_y, max_y)
pilib.PI_qTMX (uid, szAxes_z, max_z)
pos_x = c_double()
pos_y = c_double()
pos_z = c_double()
pos = (c_double*3)()
pos_axis = c_byte(8)
pos_axis = "1 2 3"
pilib.PI_POS.argtypes = [c_int, c_byte, POINTER(c_double)]
pilib.PI_POS.restypes = c_bool()
print("qPos?",pilib.PI_qPOS(uid, pos_axis ,byref(pos)))
print("Error",pilib.PI_GetError(uid))
pilib.PI_qPOS (uid, szAxes_y, pos_y)
pilib.PI_qPOS (uid, szAxes_z, pos_z)
print('is connected? ', pilib.PI_IsConnected(uid) )
print('USB Thread ID ', tid)
print('USB ID ', uid)
print('Controller ID', cid.value)
print("Buffer size ", iBufferSize)
print("szBuffer", szBuffer)
print('Enable axis', eax_axis, c_bool(eax[1]))
print('min_x ', min_x.value)
print('min_x ', min_y.value)
print('min_x ', min_z.value)
print('max_x ', max_x.value)
print('max_x ', max_y.value)
print('max_x ', max_z.value)
print('pos_x ', pos_x)
print('pos_x ', pos_y.value)
print('pos_x ', pos_z.value)

#pilib.PI_CloseConnection(uid)