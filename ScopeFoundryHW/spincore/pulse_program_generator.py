import numpy as np
from pyqtgraph.dockarea.Dock import Dock
import pyqtgraph as pg
from qtpy.QtWidgets import QPushButton
from spinapi import Inst

from ScopeFoundry.measurement import Measurement 
from .pulse_blaster_hw import PulseBlasterHW


class PulseBlasterChannel:

	__slots__ = ['flags', 'start_times', 'pulse_lengths']

	def __init__(self, flags:int,
				start_times:[float],
				pulse_lengths:[float]):
		self.flags = flags
		self.start_times = start_times
		self.pulse_lengths = pulse_lengths
		
	def __str__(self):
		return  f'''Channel: {int(np.log2(self.flags))} 
					flags: {self.flags:024b} 
					#Pulses: {len(self.pulse_lengths)}'''


# short pulse flags:
ONE_PERIOD = 0x200000

pens = {'uW':(255, 165, 0, 200),
		'AOM':'b',
		'I':(165, 42, 42, 200),
		'Q':'#A020F0',
		'DAQ':'c',
		'DAQ_sig':(50, 205, 50, 200),
		'DAQ_ref':(124, 252, 0, 200),
		'STARTtrig':'r',
		'sync_out':(255, 255, 255, 40)}


class PulseProgramGenerator:
	
	name = 'pulse_generator'
	
	def __init__(self, measurement:Measurement,
				pulse_blaser_hw_name:str='pulse_blaster'):
		self.hw:PulseBlasterHW = measurement.app.hardware[pulse_blaser_hw_name]
		self.settings = measurement.settings
		self.name = measurement.name
		self.measurement = measurement
		
		self.non_pg_setting_names = [x.name for x in self.settings._logged_quantities.values()]
		self.settings.New('program_duration', float, unit='us', initial=160.0)		
		self.settings.New('sync_out', float, unit='MHz', initial=10.0,
						description='to deactivate set negative')
		self.setup_additional_settings()
		self.pg_settings = [x for x in self.settings._logged_quantities.values() if not x.name in self.non_pg_setting_names]
		
	def setup_additional_settings(self) -> None:
		''' Override this to add settings, e.g:
			
		self.settings.New('my_fancy_pulse_duration', unit='us', initial=160.0)	
			
			returns None
			
		Note: PulseProgramGenerators have by default a 'program_duration' and 'sync_out'
			  setting. You can set a value here
	
		self.settings['program_duration'] = 30  # in us
		self.settings['sync_out'] = 3.3333  # in MHz
		'''		
		...

	def make_pulse_channels(self) -> [PulseBlasterChannel]:
		''' Override this!!!
			should return a list of Channels
			Channels can be generated using self.new_channel
		'''
		raise NotImplementedError(f'Overide make_pulse_channels() of {self.name} not Implemented')
	
	@property
	def sync_out_period_ns(self):
		return 1 / self.settings['sync_out'] * 1e3		
	
	@property
	def sync_out_period_multiple(self):
		return int(np.ceil(self.settings['program_duration'] * self.settings['sync_out']))
	
	@property
	def program_duration_ns(self):		
		return self.sync_out_period_ns * self.sync_out_period_multiple
	
	def extend_channels_with_sync_out(self, pb_channels:[PulseBlasterChannel]) -> [PulseBlasterChannel]:
		N = self.sync_out_period_multiple
		if self.settings['sync_out'] > 0:
			sync_out = self.new_channel('sync_out',
										np.arange(N) * self.sync_out_period_ns,
										np.ones(N) * self.sync_out_period_ns / 2)
			pb_channels.extend([sync_out])
		return pb_channels					
		
	def update_pulse_plot(self):
		plot = self.plot
		plot.clear()
		pulse_plot_lines = self.get_pulse_plot_lines()
		# print('update_pulse_plot', pulse_plot_lines)
		for ii, (name, (t, y)) in enumerate(pulse_plot_lines.items()):
			y = np.array(y) - 2 * ii
			t = np.array(t) / 1e9
			if name in pens:
				pen = pens[name]
			else:
				pen = 'w'
			plot.plot(t, y, name=name, pen=pen)
		
		plot.setLabel('bottom', units='s')
		return pulse_plot_lines
	
	def New_dock_UI(self) -> Dock:
		dock = Dock(name=self.name + ' pulse generator',
				widget=self.settings.New_UI(exclude=self.non_pg_setting_names, style='form'))
		
		pb = QPushButton('program and start pulse blaster')
		pb.clicked.connect(self.write_pulse_program_and_start)
		dock.addWidget(pb)

		pb = QPushButton('compare new old')
		pb.clicked.connect(self.compare_new_old)
		dock.addWidget(pb)
		
		graph_layout = pg.GraphicsLayoutWidget(border=(0, 0, 0))
		dock.addWidget(graph_layout)
		self.plot = graph_layout.addPlot(title='pulse profile')
		self.plot.addLegend()

		for lq in self.pg_settings:	
			lq.add_listener(self.update_pulse_plot)

		self.update_pulse_plot()
		return dock

	def get_pulse_plot_lines(self, include_sync_out=True):
		lu = self.hw.rev_flags_lookup
		channels = self.make_pulse_channels()
		if include_sync_out:
			channels = self.extend_channels_with_sync_out(channels)
		pulse_plot_lines = {}
		for c in channels:
			if c.flags in lu:
				channel_name = lu[c.flags]
				den = 1
			else:
				channel_name = str(int(c.flags / ONE_PERIOD)) + ' period'
				den = ONE_PERIOD
			pulse_plot_lines[channel_name] = [[0], [0]]
			for start, dt in zip(c.start_times, c.pulse_lengths):
				if start == 0:
					pulse_plot_lines[channel_name][0].pop(0)
					pulse_plot_lines[channel_name][1].pop(0)
				else:
					pulse_plot_lines[channel_name][0] += [start]
					pulse_plot_lines[channel_name][1] += [0]
					
				pulse_plot_lines[channel_name][0] += [start, start + dt / den]
				pulse_plot_lines[channel_name][1] += [1, 1]	
				
				if start + dt / den != self.program_duration_ns:
					pulse_plot_lines[channel_name][0] += [start + dt / den]
					pulse_plot_lines[channel_name][1] += [0]
		
		# makes plot look better	
		for v in pulse_plot_lines.values():
			v[0] += [self.program_duration_ns]
			v[1] += [v[1][-1]]
			
		self.pulse_plot_lines = pulse_plot_lines
		return pulse_plot_lines
	
	def save_to_h5(self, h5_meas_group):
		for k, v in self.pulse_plot_lines.items():
			h5_meas_group[k] = np.array(v)
		
	def _new_channel(self,
					flags:int,
					start_times:[float],
					lengths:[float]) -> PulseBlasterChannel:
		t_min = self.t_min
		return PulseBlasterChannel(flags,
						[t_min * round(x / t_min) for x in start_times],
						[t_min * round(x / t_min) for x in lengths],
						)
			
	def new_channel(self, channel:str, start_times:[float], lengths:[float]) -> PulseBlasterChannel:
		''' all times and lengths in ns '''
		flags = self.hw.get_flags(channel)
		return self._new_channel(flags, start_times, lengths)
		
	def new_one_period_channel(self, multiple:int, start_times:[float], lengths:[float]) -> PulseBlasterChannel:
		return self._new_channel(int(multiple) * ONE_PERIOD, start_times, lengths)
		
	@property
	def t_min(self):
		'''in ns'''
		return 1e3 / self.hw.settings['clock_frequency']
		
	# New Way
	def program_pulse_blaster_and_start(self,
			pulse_blaster_hw:PulseBlasterHW=None
			):
		if not pulse_blaster_hw:
			pulse_blaster_hw = self.hw
			
		pb_channels = self.make_pulse_channels()
		pb_channels = self.extend_channels_with_sync_out(pb_channels)
		program_duration = self.program_duration_ns
		instructions = continuous_pulse_program_instructions(pb_channels, program_duration)
		# pulse_blaster_hw.write_pulse_program_and_start(instructions)
		return instructions

	# Old Way	
	def compare_new_old(self):
		print('old')
		print_instructions(self.get_pulse_program_instructions())
		print('new')
		print_instructions(self.program_pulse_blaster_and_start())
	
	def write_pulse_program_and_start(self):
		# self. log.warning('write_pulse_program_and_start deprecated, use program_pulse_blaster_and_start instead')
		
		# old
		self.hw.write_pulse_program_and_start(self.get_pulse_program_instructions())
		
		# new
		# self.program_pulse_blaster_and_start()
		
	def get_pulse_program_instructions(self):
		channels = self.make_pulse_channels()
		channels = self.extend_channels_with_sync_out(channels)
		channelBitMasks = self._sequenceEventCataloguer(channels)
		eventTimes = list(channelBitMasks.keys())
		eventDurations = self._event_durations(eventTimes)
		instructions = self._make_cont_pulse_program(channelBitMasks, eventDurations)
		# print('get_pulse_program_instructions', instructions)
		# print(channels, channelBitMasks, eventTimes, eventDurations, instructions, sep='\n')
		return instructions
	
	def _sequenceEventCataloguer(self, channels):
		# Catalogs sequence events in terms of consecutive rising edges on the channels provided. 
		# Returns a dictionary, channelBitMasks, whose keys are event (rising/falling edge) times 
		# and values are the channelBitMask which indicate which channels are on at that time.
		eventCatalog = {}  # dictionary where the keys are rising/falling edge times and the values are the channel bit masks which turn on/off at that time
		# print('sequenceEventCataloguer', channels)
		for channel in channels:
			channelMask = channel.flags
			endTimes = [startTime + pulseDuration for startTime, pulseDuration in zip(channel.start_times, channel.pulse_lengths)]
			for eventTime in channel.start_times + endTimes:
				eventnameMask = channelMask
				if eventTime in eventCatalog.keys():
					eventnameMask = eventCatalog[eventTime] ^ channelMask 
					# I'm XORing instead of ORing here in case someone has a zero-length pulse in the sequence. 
					# In that case, the XOR ensures that the channel does not turn on at the pulse start/end time. 
					# If we did an OR here, it would turn on and only turn off at the next event 
					# (which would have been a rising edge), so this would have given unexpected behaviour.
				eventCatalog[eventTime] = eventnameMask
				
		# print(eventCatalog)
		channelBitMasks = {}
		currentBitMask = 0
		channelBitMasks[0] = currentBitMask
		for event in sorted(eventCatalog.keys()):
			channelBitMasks[event] = currentBitMask ^ eventCatalog[event]
			currentBitMask = channelBitMasks[event]
		# print(channelBitMasks)
		return channelBitMasks
		
	def _event_durations(self, eventTimes):
		numEvents = len(eventTimes)
		numInstructions = numEvents - 1
		eventDurations = np.zeros(numInstructions)
		for i in range(numInstructions):
			if i == numInstructions - 1:
				eventDurations[i] = eventTimes[i + 1] - eventTimes[i]
			else:
				eventDurations[i] = eventTimes[i + 1] - eventTimes[i]
		return eventDurations
		
	def _make_cont_pulse_program(self, channelBitMasks, eventDurations):
		instructions = []
		bitMasks = list(channelBitMasks.values())
		start = [0]
		for i, duration in enumerate(eventDurations):
			if i == len(eventDurations) - 1:  # last instruction 'Branched' to first
				instructions.extend([[bitMasks[i], Inst.BRANCH, start[0], duration]])
			else:
				instructions.extend([[bitMasks[i], Inst.CONTINUE, 0, duration]])
		self.instructions = instructions
		# print('_make_cont_pulse_program', start[0])
		return instructions
		
		
def pulse_blaster_flags_length_lists(channels:[PulseBlasterChannel], program_duration:float) -> ([int], [float]):
	'''
	Convenience function used to generate Pulse Blaster PULSE_PROGRAM
	
	returns ([flags], [length])
		flags: 	flags is an int that contains a the desired output state of the PULSE BLASTER
				output. In its binary representation, the i-th least significant bit, 
				tells the i-th channel to turn high or low. 
		length: the duration the state lasts
	'''
	
	# To ensure the first duration is counted from t=0 
	# we add first elements.
	_times = [0]
	_flags_list = [0] 
	
	for c in channels:
		for start_time, length in zip(c.start_times, c.pulse_lengths):
			_times.append(start_time)
			_flags_list.append(c.flags)			
			_times.append(start_time + length)
			_flags_list.append(c.flags)			
	_times.append(program_duration)
	
	# sort event w.r.t. times
	_times = np.array(_times)
	indices = np.argsort(_times)
	_flags_list = np.array(_flags_list)[indices[:-1]]
	
	# duration between events
	_lengths = np.diff(_times[indices])	
	# note that some elements in _lengths are zero, 
	# e.g. when we turn two channels high at same time
		
	flags_list = []
	lengths = []
	# current_time = _times[0]		
	flags = _flags_list[0]  # initialize: (everything is low)
	for length, update_flags in zip(_lengths, _flags_list):			
		if length == 0: 
			# we will not move in time and hence
			# we just evaluate the change on the flags
			flags = flags ^ update_flags
		else: 
			# register states that last >0
			flags_list.append(flags ^ update_flags)
			flags = flags_list[-1]
			lengths.append(length)
			
		# current_time += length
		# print(f'{flags:024b}', current_time)
			
	return flags_list, lengths


def print_flags_lengths(flags_list, lengths):
	print('{:<24} ns'.format('flags'))
	for flags, length in zip(flags_list, lengths):
		print(f'{flags:024b}', length)

		
def print_instructions(instructions):
	print('{:<7} {:<24} inst ns'.format('', 'flags'))
	for flags, inst, inst_data, length in instructions:
		print(f'{flags:>7} {flags:024b} {inst}, {inst_data} {length:0.1f}')	


def pulse_program_instructions(channels:[PulseBlasterChannel], program_duration):
	flags_list, lengths = pulse_blaster_flags_length_lists(channels, program_duration)
	instructions = []
	for flags, duration in zip(flags_list, lengths):
		instructions.append([flags, Inst.CONTINUE, 0, duration])
	return instructions


def make_continueous(instructions, offset=0):
	# change the last instruction to 'branch' back 
	# to the instruction 'offset'. (instructions are zero-indexed)
	instructions[-1][1] = Inst.BRANCH
	instructions[-1][2] = int(offset)
	return instructions


def continuous_pulse_program_instructions(channels:[PulseBlasterChannel], program_duration):
	return make_continueous(pulse_program_instructions(channels, program_duration))

