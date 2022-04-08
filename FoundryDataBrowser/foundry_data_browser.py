from ScopeFoundry.data_browser import DataBrowser
import logging    
import sys
import traceback


app = DataBrowser(sys.argv)



def _on_load_err(err):
    text = "".join(traceback.format_exc(limit=None, chain=True))
    print("Failed to load viewer with error:", err, file=sys.stderr)
    print(text, file=sys.stderr)


try:
    from FoundryDataBrowser.viewers.h5_tree import H5TreeView, H5TreeSearchView
    app.load_view(H5TreeView(app))
    app.load_view(H5TreeSearchView(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.gauss2d_fit_img import Gauss2DFitImgView, Gauss2DFitAPD_MCL_2dSlowScanView, \
        Gauss2DFit_FiberAPD_View
    app.load_view(Gauss2DFitImgView(app))
    app.load_view(Gauss2DFitAPD_MCL_2dSlowScanView(app))
    app.load_view(Gauss2DFit_FiberAPD_View(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.images import ScipyImreadView
    app.load_view(ScipyImreadView(app))
except ImportError:
    logging.warning("missing scipy")
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.images import PILImageView
    app.load_view(PILImageView(app))
except ImportError:
    logging.warning("missing PIL library")    
except Exception as err: _on_load_err(err)    

try:
    from FoundryDataBrowser.viewers.apd_confocal_npz import ApdConfocalNPZView, ApdConfocal3dNPZView
    app.load_view(ApdConfocalNPZView(app))
    app.load_view(ApdConfocal3dNPZView(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.picoharp_npz import PicoHarpNPZView
    app.load_view(PicoHarpNPZView(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.picoharp_histogram_h5 import PicoHarpHistogramH5View
    app.load_view(PicoHarpHistogramH5View(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.picoquant_histogram_h5 import PicoquantHistogramH5View
    app.load_view(PicoquantHistogramH5View(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.hyperspec_npz import HyperSpecNPZView
    app.load_view(HyperSpecNPZView(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.hyperspec_npz import HyperSpecSpecMedianNPZView
    app.load_view(HyperSpecSpecMedianNPZView(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.trpl_t_x_lifetime import TRPL_t_x_lifetime_NPZView, TRPL_t_x_lifetime_fiber_scan_View, TRPL_t_x_lifetime_H5_View
    app.load_view(TRPL_t_x_lifetime_NPZView(app))
    app.load_view(TRPL_t_x_lifetime_fiber_scan_View(app))
    app.load_view(TRPL_t_x_lifetime_H5_View(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.trpl_npz import TRPLNPZView, TRPL3dNPZView
    app.load_view(TRPLNPZView(app))
    app.load_view(TRPL3dNPZView(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.picoharp_mcl_2dslowscan import Picoharp_MCL_2DSlowScan_View, FiberPicoharpScanView
    app.load_view(Picoharp_MCL_2DSlowScan_View(app))
    app.load_view(FiberPicoharpScanView(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.APD_MCL_2DSlowScanView import APD_MCL_2DSlowScanView, APD_MCL_3DSlowScanView
    app.load_view(APD_MCL_2DSlowScanView(app))
    app.load_view(APD_MCL_3DSlowScanView(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.APD_ASI_2DSlowScanView import APD_ASI_2DSlowScanView
    app.load_view(APD_ASI_2DSlowScanView(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.WinSpecMCL2DSlowScanView import WinSpecMCL2DSlowScanView
    app.load_view(WinSpecMCL2DSlowScanView(app))
    
    from FoundryDataBrowser.viewers.winspec_remote_readout_h5 import WinSpecRemoteReadoutView
    app.load_view(WinSpecRemoteReadoutView(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.power_scan_h5 import PowerScanH5View
    app.load_view(PowerScanH5View(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.sync_raster_scan_h5 import SyncRasterScanH5
    app.load_view(SyncRasterScanH5(app))
except Exception as err: _on_load_err(err)

# try:
#     from FoundryDataBrowser.viewers.auger_spectrum_h5 import AugerSpectrumH5
#     app.load_view(AugerSpectrumH5(app))
#
#     from FoundryDataBrowser.viewers.auger_sync_raster_scan_h5 import AugerSyncRasterScanH5View
#     app.load_view(AugerSyncRasterScanH5View(app))
#
#     from FoundryDataBrowser.viewers.auger_spec_map import AugerSpecMapView
#     app.load_view(AugerSpecMapView(app))
# except Exception as err: _on_load_err(err)

try: 
    from FoundryDataBrowser.viewers.power_scan_npz import PowerScanNPZView
    app.load_view(PowerScanNPZView(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.andor_ccd_readout import AndorCCDReadout
    app.load_view(AndorCCDReadout(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.picam_readout import PicamReadout
    app.load_view(PicamReadout(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.hyperspec_cl_h5 import HyperSpecCLH5View
    app.load_view(HyperSpecCLH5View(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.hyperspec_h5 import HyperSpecH5View
    app.load_view(HyperSpecH5View(app))
    
    from FoundryDataBrowser.viewers.hyperspec_3d_h5 import HyperSpec3DH5View
    app.load_view(HyperSpec3DH5View(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.trpl_h5 import TRPLH5View
    app.load_view(TRPLH5View(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.power_spec_logger_view import PowerSpectrumLoggerView
    app.load_view(PowerSpectrumLoggerView(app))
except Exception as err: _on_load_err(err)

try: 
    from FoundryDataBrowser.viewers.iv_h5 import IVH5View, IVTRPLH5View
    app.load_view(IVH5View(app))
    app.load_view(IVTRPLH5View(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.survey_scan_map_view import SurveyScanMapView
    app.load_view(SurveyScanMapView(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.ranged_optimization_h5 import RangedOptimizationH5View
    app.load_view(RangedOptimizationH5View(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.lakeshore_measure_h5 import LakeshoreH5View
    app.load_view(LakeshoreH5View(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.toupcam_h5 import ToupcamH5
    app.load_view(ToupcamH5(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.config_measurement import ConfigMeasurement
    app.load_view(ConfigMeasurement(app))
except Exception as err: _on_load_err(err)

try:
    from FoundryDataBrowser.viewers.galvo_mirror_2D_apd_scan import GalvoMirror2DApdScan
    app.load_view(GalvoMirror2DApdScan(app))
except Exception as err: _on_load_err(err)


app.settings.browse_dir.update_value(r"F:\User's Data") 

sys.exit(app.exec_())    

