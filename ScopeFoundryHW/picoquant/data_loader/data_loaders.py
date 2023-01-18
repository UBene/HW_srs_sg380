import h5py
import numpy as np


def extract_start_stop_times(raw_event_times, data_mask, resolution, debug):
    start_stops = np.bitwise_and(raw_event_times>> 10, 0b111111111111111)
    if debug:
        print("event times                      start-stop")
        for i in range(10):
            print(
                np.binary_repr(raw_event_times[i], 32),
                np.binary_repr(start_stops[i], 15),
            )
    return start_stops[data_mask] * resolution


def extract_sync_times(raw_event_times, overflow_mask, data_mask, sync_rate, debug):
    sync_counters = np.bitwise_and(raw_event_times, 0b1111111111)
    if debug:
        print("event times                      sync counter   is_overflow_marker")
        for i in range(10):
            print(
                np.binary_repr(raw_event_times[i], 32),
                np.binary_repr(sync_counters[i], 10),
                overflow_mask[i],
            )
    wrap_around = 2**15
    overflow_indices = np.argwhere(overflow_mask)
    for i in range(1, len(overflow_indices)):
        s = overflow_indices[i - 1][0] + 1
        e = overflow_indices[i][0]
        sync_counters[s:e] = sync_counters[s:e] + ((i) * wrap_around)
    sync_counters[e + 1 :] = sync_counters[e + 1 :] + (i + 1) * wrap_around
    return sync_counters[data_mask] * sync_rate

def extract_channel_masks(channel_bits, is_data):
    channel_masks = []
    flags = 0
    for _ in range(6):
        channel_masks.append((channel_bits == flags)[is_data])
        flags = (flags * 2) + 1
    return channel_masks


class T3DataLoader:
    def __init__(self, file_name, debug=False) -> None:

        with h5py.File(file_name) as file:
            measure_name = "_".join(file_name.split(".")[0].split("_")[2:])
            hw_name = "_".join(measure_name.split("_")[:-1])
            H = file[f"hardware/{hw_name}"]
            mode = H["settings"].attrs["Mode"]
            assert mode == "T3"
            resolution = H["settings"].attrs["Resolution"]
            sync_rate = H["settings"].attrs["SyncRate"]
            M = file[f"measurement/{measure_name}"]
            raw_event_times = np.concatenate(M["event_times"][:])

        self.process_data(raw_event_times, resolution, sync_rate, debug)

    def process_data(self, raw_event_times, resolution, sync_rate, debug):
        channel_bits = raw_event_times >> 25
        overflow_mask = channel_bits == 0b1111111
        data_mask = np.logical_not(overflow_mask)

        self.channel_masks = extract_channel_masks(channel_bits, data_mask)
        self.sync_times = extract_sync_times(
            raw_event_times, overflow_mask, data_mask, sync_rate, debug
        )
        self.start_stop_times = extract_start_stop_times(
            raw_event_times, data_mask, resolution, debug
        )
        # all eventimes, not channel sorted
        self._event_times = self.sync_times + self.start_stop_times

    def get_times(self, chan):
        return self._event_times[self.channel_masks[chan]]

    def get_start_stop_times(self, chan=0):
        return self.start_stop_times[self.channel_masks[chan]]

    def calc_time_histograms(self, bins=21, **kwargs):
        self.time_histograms = []
        for i in range(6):
            hist, edges = np.histogram(self.get_start_stop_times(i), bins, **kwargs)
            if i == 0:
                self.time_array = edges[:-1]
            self.time_histograms.append(hist)

    def calc_event_times(self):
        self.event_times = []
        for i in range(6):
            self.event_times.append(self.get_times(i))
        return self.event_times


class HistogramDataLoader:
    def __init__(self, file_name) -> None:
        with h5py.File(file_name) as file:
            measure_name = "_".join(file_name.split(".")[0].split("_")[2:])
            # hw_name = "_".join(measure_name.split('_')[:-1])
            # H = file[f"hardware/{hw_name}"]
            # mode = H['settings'].attrs['Mode']
            # resolution = H['settings'].attrs['Resolution']
            # sync_rate = H['settings'].attrs['SyncRate']
            M = file[f"measurement/{measure_name}"]
            # print(M.keys())
            self.time_array = M["time_array"][:]
            self.time_histograms = M["time_histogram"][:]
