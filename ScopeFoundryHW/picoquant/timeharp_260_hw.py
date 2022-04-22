from ScopeFoundry.hardware import HardwareComponent
import time
import numpy as np
import warnings


from ScopeFoundryHW.picoquant.timeharp_260_dev import (STOPCNTMIN,
                                                       STOPCNTMAX,
                                                       SYNCDIVMAX,
                                                       CFDLVLMIN,
                                                       CFDLVLMAX,
                                                       CFDZCMIN,
                                                       CFDZCMAX)


class TimeHarp260HW(HardwareComponent):

    name = 'timeharp_260'

    def __init__(self, app, debug=False, name=None, n_channels=2):
        self.n_channels = n_channels
        HardwareComponent.__init__(self, app, debug=debug, name=name)

    def setup(self):
        S = self.settings

        # Device Connection Parameters
        S.New('DeviceIndex', dtype=int, initial=0, vmin=0, vmax=7)
        S.New("Mode", dtype=str, choices=[
              ("HIST", "HIST"), ("T2", "T2"), ("T3", "T3")], initial='HIST')
        S.New("RefSource", dtype=str, initial='internal',
              choices=('internal', 'external'))

        S.New("Model", dtype=str, ro=True)
        S.New("PartNo", dtype=str, ro=True)
        S.New("Version", dtype=str, ro=True)

        # Acquisition Settings
        S.New("StopOnOverflow", dtype=bool)
        S.New("StopCount", dtype=int, initial=STOPCNTMAX,
              vmin=STOPCNTMIN, vmax=STOPCNTMAX)
        S.New("HistogramBins", dtype=int, ro=False,
              vmin=0, vmax=2**16, initial=2**16, si=False)

        S.New("Tacq", dtype=float, unit="s", si=True,
              initial=1, vmin=1e-3, vmax=100 * 60 * 60)
        S.New("Binning", dtype=int, initial=2, choices=[
              (str(x), x) for x in range(0, 8)])
        S.New("Resolution", dtype=int, unit="ps", ro=True, si=False)
        S.New("ElapsedMeasTime", dtype=float, unit="s", si=True)

        # Sync Channel
        S.New("SyncDivider", dtype=int, choices=[
              ("1", 1), ("2", 2), ("4", 4), ("8", 8), ("16", 16)], initial=1)
        S.New("SyncOffset", dtype=int, vmin=-999,
              vmax=SYNCDIVMAX, si=False, initial=0, unit='ns')

        S.New("CFDLevelSync", dtype=int, unit="mV",
              vmin=CFDLVLMIN, vmax=CFDLVLMAX,
              #vmin=0, vmax=800,
              initial=0, si=False)
        S.New("CFDZeroCrossSync", dtype=int,  unit="mV",
              #vmin=CFDZCMIN, vmax=CFDZCMAX,
              vmin=0, vmax=20,
              initial=0, si=False)

        S.New("SyncRate", dtype=int, ro=True, si=True, unit='Hz')
        S.New("SyncPeriod", dtype=float, unit='ps', ro=True, spinbox_decimals=6)

        # Channels
        for i in range(self.n_channels):
            S.New("ChanEnable{}".format(i), dtype=bool, initial=True)
            S.New("CFDLevel{}".format(i), dtype=int, unit="mV",
                  #vmin=0, vmax=800,
                  vmin=CFDLVLMIN, vmax=CFDLVLMAX,

                  initial=-50, si=False)
            S.New("CFDZeroCross{}".format(i), dtype=int, unit="mV",
                  #vmin=0, vmax=20,
                  vmin=CFDZCMIN, vmax=CFDZCMAX,
                  initial=-10, si=False)
            S.New("ChanOffset{}".format(i), dtype=int, unit='ps')
            S.New("CountRate{}".format(i), dtype=int, ro=True,
                  vmin=0, vmax=100e6, si=True, unit='Hz')

    def connect(self):
        from ScopeFoundryHW.picoquant.timeharp_260_dev import TimeHarp260
        S = self.settings

        self.dev = dev = TimeHarp260(devnum=S['DeviceIndex'],
                                     mode=S['Mode'],
                                     refsource=S['RefSource'],
                                     debug=S['debug_mode'])

        S.DeviceIndex.change_readonly(True)
        S.Mode.change_readonly(True)
        S.RefSource.change_readonly(True)

        S.StopOnOverflow.connect_to_hardware(
            write_func=lambda enable, S=S, dev=dev:
            dev.SetStopOverflow(stop_ofl=enable, stopcount=S['StopCount']))
        S.StopCount.connect_to_hardware(
            write_func=lambda stopcount, S=S, dev=dev:
            dev.SetStopOverflow(stop_ofl=S['StopOnOverflow'], stopcount=stopcount))

        S.Binning.change_choice_list(tuple(range(0, dev.max_bin_steps)))
        S.Binning.connect_to_hardware(write_func=self.dev.SetBinning)
        S.Resolution.connect_to_hardware(read_func=self.dev.GetResolution)
        S.ElapsedMeasTime.connect_to_hardware(
            read_func=lambda dev=dev: 1e-3 * dev.GetElapsedMeasTime())

        S.SyncDivider.connect_to_hardware(
            write_func=dev.SetSyncDiv)
        S.SyncOffset.connect_to_hardware(
            write_func=dev.SetSyncChannelOffset)
        S.CFDLevelSync.connect_to_hardware(
            write_func=lambda level, S=S, dev=dev:
            dev.SetSyncCFD(level, S['CFDZeroCrossSync']))
        S.CFDZeroCrossSync.connect_to_hardware(
            write_func=lambda zerocross, S=S, dev=dev:
            dev.SetSyncCFD(S['CFDLevelSync'], zerocross))

        S.SyncDivider.write_to_hardware()
        S.SyncOffset.write_to_hardware()
        S.CFDLevelSync.write_to_hardware()
        S.CFDZeroCrossSync.write_to_hardware()

        S.SyncRate.connect_to_hardware(
            read_func=dev.GetSyncRate)

        S.SyncPeriod.connect_to_hardware(
            read_func=dev.GetSyncPeriod)

        for i in range(self.n_channels):
            lq = S.get_lq("ChanEnable{}".format(i))
            lq.connect_to_hardware(
                write_func=lambda enable, chan=i, dev=dev:
                dev.SetInputChannelEnable(chan, enable))
            lq.write_to_hardware()

            lq = S.get_lq("CFDLevel{}".format(i))
            lq.connect_to_hardware(
                write_func=lambda level, chan=i, S=S, dev=dev:
                dev.SetInputCFD(chan, level, S["CFDZeroCross{}".format(chan)]))
            lq.write_to_hardware()

            lq = S.get_lq("CFDZeroCross{}".format(i))
            lq.connect_to_hardware(
                write_func=lambda zerocross, chan=i, S=S, dev=dev:
                dev.SetInputCFD(chan, S["CFDLevel{}".format(chan)], zerocross))
            lq.write_to_hardware()
            lq = S.get_lq("ChanOffset{}".format(i))
            lq.connect_to_hardware(
                write_func=lambda offset, chan=i, dev=dev:
                dev.SetInputChannelOffset(chan, offset))
            lq.write_to_hardware()

            S.get_lq("CountRate{}".format(i)).connect_to_hardware(
                read_func=lambda chan=i, dev=dev:
                dev.GetCountRate(chan))

        # self.settings.Resolution.read_from_hardware()
        # S.Binning.add_listener(self.settings.Resolution.read_from_hardware)
        S['Model'] = dev.hw_model
        S['PartNo'] = dev.hw_partno
        S['Version'] = dev.hw_version
        self.read_from_hardware()

    def set_stop_overflow(self, overflow):
        self.dev.SetStopOverflow(self.settings["StopOnOverflow"], overflow)

    def disconnect(self):
        S = self.settings

        S.DeviceIndex.change_readonly(False)
        S.Mode.change_readonly(False)
        S.RefSource.change_readonly(False)

        S.disconnect_all_from_hardware()

        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev

    def threaded_update(self):
        self.settings.SyncRate.read_from_hardware()
        self.settings.ElapsedMeasTime.read_from_hardware()
        for i in range(self.n_channels):
            lq = self.settings.get_lq("CountRate{}".format(i))
            lq.read_from_hardware()
        time.sleep(0.100)

    def start_histogram(self):
        assert self.settings["Mode"] == "HIST"
        Tacq_ms = 1e+3 * self.settings['Tacq']
        self.time_array = self.dev.compute_hist_time_array()
        self.dev.ClearHistMem()
        self.dev.StartMeas(Tacq_ms)

    def stop_histogram(self):
        self.dev.StopMeas()

    def read_histogram_data(self, channel='enabled', clear_after=False):
        '''
        channel     'enabled': returns histograms of enabled channels.
                    'all':     returns histograms of all channels.
                    <int> i:   returns histogram of channel i.
        '''
        if channel == 'enabled':
            hist_data = []
            for i in range(self.n_channels):
                if self.settings["ChanEnable{}".format(i)]:
                    hist_data.append(
                        self.dev.read_histogram_data(i, clear_after))
            return np.array(hist_data)
        elif channel == 'all':
            hist_data = []
            for i in range(self.n_channels):
                hist_data.append(self.dev.read_histogram_data(i, clear_after))
            return np.array(hist_data)
        else:
            return self.dev.read_histogram_data(channel, clear_after)

    def check_done_scanning(self):
        return self.dev.check_done_scanning()

    def update_HistogramBins(self):
        '''sets HistogramBins to minimum needed to cover the SyncPeriod'''
        self.settings.Resolution.read_from_hardware()
        S = self.settings
        sync_period = 1.0 / S['SyncRate']
        HistogramBins = int(np.ceil(sync_period / (S['Resolution'] * 1e-12)))
        if HistogramBins > S.HistogramBins.vmax:
            warnings.warn(
                "Can not cover whole SyncPeriod with current Resolution: Increase Binning!", UserWarning)
        else:
            S['HistogramBins'] = HistogramBins
        return S['HistogramBins']

    @property
    def enabled_channels(self):
        enabled_channels = 0
        for i in range(self.n_channels):
            if self.settings["ChanEnable{}".format(i)]:
                enabled_channels += 1
        return enabled_channels

    @property
    def hist_shape(self):
        return (self.enabled_channels, self.settings['HistogramBins'])

    @property
    def hist_slice(self):
        enabled_channels, HistogramBins = self.hist_shape
        return np.s_[0:enabled_channels, 0:HistogramBins]

    @property
    def sliced_time_array(self):
        return self.time_array[:self.settings['HistogramBins']]
