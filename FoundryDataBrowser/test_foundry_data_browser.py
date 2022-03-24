from ScopeFoundry.data_browser import DataBrowser
import sys
import traceback


app = DataBrowser(sys.argv)



def _on_load_err(err):
    text = "".join(traceback.format_exc(limit=None, chain=True))
    print("Failed to load viewer with error:", err, file=sys.stderr)
    print(text, file=sys.stderr)



# try:
#     from FoundryDataBrowser.viewers.power_scan_h5 import PowerScanH5View
#     app.load_view(PowerScanH5View(app))
# except Exception as err: _on_load_err(err)


try:
    from FoundryDataBrowser.viewers.hyperspec_base_view import HyperSpectralBaseView
    app.load_view(HyperSpectralBaseView(app))
except Exception as err: _on_load_err(err)

app.settings['browse_dir'] = r'C:\Users\bened\OneDrive\PHD\data_analysis'
sys.exit(app.exec_())    

