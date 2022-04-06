import numpy as np
from collections import namedtuple

from spinapi import Inst

from ScopeFoundryHW.spincore.spinapi_hw import PulseBlasterHW
from ScopeFoundry.measurement import Measurement
from pyqtgraph.dockarea.Dock import Dock
import pyqtgraph as pg
# from odmr_measurements.config_measurement import ConfigMeasurement

PBchannel = namedtuple('PBchannel', ['channelNumber', 'startTimes', 'pulseDurations']) 

# Define t_min, time resolution of the PulseBlaster, given by 1/(clock frequency):

# Short pulse flags:
ONE_PERIOD = 0x200000

pens = {'AOM':'g', 'uW':'y', 'DAQ':'b', 'STARTtrig':'r', 'I':'w', 'Q':'p'}


class PulseProgramGenerator:
	
	name = 'pulse_generator'
	
	def __init__(self, measurement:Measurement,
				pulse_blaser_hw_name:str='pulse_blaster'):
		self.hw:PulseBlasterHW = measurement.app.hardware[pulse_blaser_hw_name]
		self.settings = measurement.settings
		
		self.exclude = [x.name for x in self.settings._logged_quantities.values()]
		self.setup_settings()
		self.include_settings = [x for x in self.settings._logged_quantities.values() if not x.name in self.exclude]
				
	def setup_settings(self):
		...

	def make_pulse_channels(self):
		...
				
	def get_pulse_program_instructions(self):
		channels = self.make_pulse_channels()
		channelBitMasks = self._sequenceEventCataloguer(channels)
		eventTimes = list(channelBitMasks.keys())
		eventDurations = self._event_durations(eventTimes)
		instructions = self._pb_instructions(channelBitMasks, eventDurations)
		# print('get_pulse_program_instructions')
		# print(channels, channelBitMasks, eventTimes, eventDurations, instructions, sep='\n')
		return instructions

	def _sequenceEventCataloguer(self, channels):
		# Catalogs sequence events in terms of consecutive rising edges on the channels provided. 
		# Returns a dictionary, channelBitMasks, whose keys are event (rising/falling edge) times 
		# and values are the channelBitMask which indicate which channels are on at that time.
		eventCatalog = {}  # dictionary where the keys are rising/falling edge times and the values are the channel bit masks which turn on/off at that time
		print('sequenceEventCataloguer', channels)
		for channel in channels:
			channelMask = channel.channelNumber
			endTimes = [startTime + pulseDuration for startTime, pulseDuration in zip(channel.startTimes, channel.pulseDurations)]
			for eventTime in channel.startTimes + endTimes:
				eventChannelMask = channelMask
				if eventTime in eventCatalog.keys():
					eventChannelMask = eventCatalog[eventTime] ^ channelMask 
					# I'm XORing instead of ORing here in case someone has a zero-length pulse in the sequence. In that case, the XOR ensures that the channel does not turn on at the pulse start/end time. If we did an OR here, it would turn on and only turn off at the next event (which would have been a rising edge), so this would have given unexpected behaviour.
				eventCatalog[eventTime] = eventChannelMask
				
		print(eventCatalog)
		channelBitMasks = {}
		currentBitMask = 0
		channelBitMasks[0] = currentBitMask
		for event in sorted(eventCatalog.keys()):
			channelBitMasks[event] = currentBitMask ^ eventCatalog[event]
			currentBitMask = channelBitMasks[event]
		print(channelBitMasks)
		return channelBitMasks
		
	def _event_durations(self, eventTimes):
		numEvents = len(eventTimes)
		eventDurations = np.zeros(numEvents - 1)
		numInstructions = numEvents - 1
		for i in range(0, numInstructions):
			if i == numInstructions - 1:
				eventDurations[i] = eventTimes[i + 1] - eventTimes[i]
			else:
				eventDurations[i] = eventTimes[i + 1] - eventTimes[i]
		return eventDurations
		
	def _pb_instructions(self, channelBitMasks, eventDurations):
		instructions = []
		bitMasks = list(channelBitMasks.values())
		start = [0]
		for i, duration in enumerate(eventDurations):
			if i == len(eventDurations) - 1:
				instructions.extend([[bitMasks[i], Inst.BRANCH, start[0], duration]])
			else:
				start[0] = instructions.extend([[bitMasks[i], Inst.CONTINUE, 0, duration]])
		self.instructions = instructions
		return instructions
		
	def program_hw(self):
		instructions = self.get_pulse_program_instructions()
		self.hw.configure()
		self.hw.write_pulse_program(instructions)
		
	def update_pulse_plot(self):
		plot = self.plot
		plot.clear()
		pulse_data = self.get_pulse_data()
		# print('update_pulse_plot', pulse_data)
		for ii, (name, (t, y)) in enumerate(pulse_data.items()):
			y = np.array(y) - 2 * ii
			t = np.array(t) / 1e9
			if name in pens:
				pen = pens[name]
			else:
				pen = 'w'
			plot.plot(t, y, name=name, pen=pen)
		
		plot.addLegend()
		plot.setLabel('bottom', units='s')
		return pulse_data
	
	def make_dock(self):
		dock = Dock(name='pulse_generator', widget=self.settings.New_UI(exclude=self.exclude, style='form'))
		graph_layout = pg.GraphicsLayoutWidget(border=(100, 100, 100))
		dock.addWidget(graph_layout)
		self.plot = graph_layout.addPlot(title='pulse profile')
		for lq in self.include_settings:
			lq.add_listener(self.update_pulse_plot)
		self.update_pulse_plot()
		return dock
		
	def get_pulse_data(self):
		names = {v:k for k, v in self.hw.get_register_addresses_dict().items()}
		sequence = self.make_pulse_channels()
		pulse_data = {}
		max_t = 0
		for c in sequence:
			if c.channelNumber in names:
				name = names[c.channelNumber]
				den = 1
			else:
				name = str(int(c.channelNumber / ONE_PERIOD)) + ' period'
				den = ONE_PERIOD
			pulse_data[name] = [[0], [0]]
			for start, dt in zip(c.startTimes, c.pulseDurations):
				pulse_data[name][0] += [start, start, start + dt / den, start + dt / den]
				pulse_data[name][1] += [0, 1, 1, 0]
				max_t = max(max_t, start + dt)
		
		# makes a plot look better	
		for v in pulse_data.values():
			v[0] += [max_t]
			v[1] += [v[1][-1]]
			
		self.pulse_data = pulse_data
		return pulse_data
	
	def save_to_h5(self, h5_meas_group):
		for k, v in self.pulse_data.items():
			h5_meas_group[k] = np.array(v)
			
	def new_channel(self, channel:str, start_times:[float], durations:[float]):
		''' all times and durations in ns '''
		bit_address = self.hw.get_register_addresses_dict()[channel]
		return self._new_channel(bit_address, start_times, durations)
		
	def _new_channel(self, bit_address, start_times, durations):
		t_min = self.t_min
		return PBchannel(bit_address,
						[t_min * round(x / t_min) for x in start_times],
						[t_min * round(x / t_min) for x in durations],
						)
		
	def new_one_period_channel(self, multiple:float, start_times:[float], durations:[float]):
		return self._new_channel(int(multiple) * ONE_PERIOD, start_times, durations)
		
	@property
	def t_min(self):
		'''in ns'''
		return 1e3 / self.hw.settings['clock_frequency']
		
