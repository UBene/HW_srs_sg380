from cffi import  FFI
ffi = FFI()
with open('uc480.h','r') as f:
    ffi.cdef(f.read())
C = ffi.dlopen(None)