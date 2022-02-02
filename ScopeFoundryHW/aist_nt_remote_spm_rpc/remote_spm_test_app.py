from ScopeFoundry import BaseMicroscopeApp

class RemoteSpm(BaseMicroscopeApp):

    name = 'remote_spm'
    
    def setup(self):
       
        
        from ScopeFoundryHW.aist_nt_remote_spm_rpc.remote_spm_hw import RemoteSPMHW
        self.add_hardware(RemoteSPMHW(self))

if __name__ == '__main__':
    import sys
    app = RemoteSpm(sys.argv)
    sys.exit(app.exec_())