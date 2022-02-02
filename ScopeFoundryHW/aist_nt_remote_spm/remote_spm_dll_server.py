from msl.loadlib import Server32




lib = r"C:\Users\RAMAN\workspace\NearField\ScopeFoundryHW\aist-nt_remote_spm\dll\remote_spm.dll"
lib = r"C:\aist\aist_3.5.153\aist\remote_spm\remote_spm.dll"


class MyServer(Server32):
    """Wrapper around a 32-bit C++ library 'my_lib.dll' that has an 'add' and 'version' function."""

    def __init__(self, host, port, **kwargs):
        # Load the 'my_lib' shared-library file using ctypes.CDLL

        print('__init__ MyServer')
        super(MyServer, self).__init__(lib, 'cdll', host, port)

        # The Server32 class has a 'lib' property that is a reference to the ctypes.CDLL object

        # Call the version function from the library
        #self.version = self.lib.version()
        
    #def version(self):
    #    return self.lib.version()

    def add(self, a, b):
        # The shared library's 'add' function takes two integers as inputs and returns the sum
        print('called Server add function')
        
        return a + b
        #return self.lib.add(a, b)