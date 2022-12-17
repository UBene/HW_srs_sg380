"""Written by Alan Buckley 9-19-2016"""

class Chameleon(object):


	def __init__(self, port="COM1", debug=False, dummy=False): #change port according to device listing in windows.
		
		self.debug = debug
		self.dummy = dummy
		self.port = port
		
		if not self.dummy:

			self.ser = serial.Serial(port=self.port, baudrate=19200, bytesize=8, parity=None, stopbits=1, xonxoff=False)
	        #self.ser.flushInput()
	        self.ser.reset_input_buffer()
	        #self.ser.flushOutput()
	        self.ser.reset_output_buffer()
	    self.faults_table = 

	def write_cmd(self, cmd):
		self.ser.write(cmd+'\r\n')
		if self.debug:
			print ('write:', cmd)
		response = self.ser.readline()
		if self.debug:
			print ('response:', response[:-2])
		return response

	def write_baudrate(self, rate):
		"""Sets the RS232 serial port baud rate to the
		specified value."""
		assert rate in [1200,2400,4800,9600,19200,38400,57600,115200]
		self.write_cmd("BAUDRATE=%i" % rate)

	def write_echo_mode(self, echo=False):
		"""Toggle Echo mode. Note: A change in echo mode takes 
		effect with the first command sent after the echo command."""
		if echo:
			n = 1
		else:
			n = 0
		self.write_cmd("ECHO=%i" % n)

	def write_laser_flash(self):
		"""Flash Verdi laser output below lasing threshold to allow 
		single frequency mode to recenter."""
		self.write_cmd("FLASH=%i" % 1)

	def write_home_stepper(self):
		"""Homes the tuning motor. This can take 3 to 30 seconds."""
		self.write_cmd("HOME STEPPER=%i" % 1)

	def write_laser(self, active=False):
		"""Allows user to activate laser or place it in standby mode.
		Activating laser resets faults and powers on laser. Lasing resumes
		of there are no active faults. Keyswitch must be in ON position for
		operation of laser."""
		if active:
			n = 1
		else:
			n = 0
		self.write_cmd("LASER=%i" % n)

	def write_LBO_heater(self, active=False):
		"Turns LBO heater on/off."
		if active:
			n = 1
		else:
			n = 0
		self.write_cmd("LBO HEATER=%i" % n)

	def write_LBO_optimize(self, active=False):
		"""Begins optimization routine. If run with active flag, 
		device begins optimization routine."""
		if active:
			n = 1
		else:
			n = 0
		self.write_cmd("LBO OPTIMIZE=%i" % n)

	def write_front_panel_lock(self, enabled=False):
		"""Enables/disables user input from the front panel."""
		if enabled:
			n = 0 #No, this isn't a typo according to the manual.
		else:
			n = 1 
		self.write_cmd("LOCK FRONT PANEL=%i" % n)

	def write_prompt(self, enabled=False):
		"""Turns "CHAMELEON>" prompt on/off."""
		if enabled:
			n = 1
		else:
			n = 0
		self.write_cmd("PROMPT=%i" % n)

	def write_search_modelock(self, enabled=True):
		"""Enables/disables search for modelocking."""
		if enabled:
			n = 0
		else:
			n = 1
		self.write_cmd("SEARCH MODELOCK=%i" % n)

	def write_shutter(self, _open=False):
		"""Changes state of external shutter."""
		if _open:
			n = 1
		else:
			n = 0
		self.write_cmd("SHUTTER=%i" % n)

	def write_wavelength(self, _lambda):
		"""Sets the Chameleon Ultra wavelength to the specified 
		value in nanometers. If the specified wavelength is 
		beyond the allowed range of wavelengths, the wavelength 
		is set to either the upper or lower limit. (Whichever 
			is closer to the specified wavelength."""
		wl = int(_lambda)
		self.write_cmd("WAVELENGTH=%i" % wl)

	def write_wavelength_step(self, _delta):
		"""Changes Chameleon Ultra wavelength by the specified amount in nanometers."""
		delta = int(_delta)
		self.write_cmd("WAVELENGTH STEP=%i" % delta)

	def write_heartbeat(self, enabled=False):
		"""Heartbeat is defined by the manufacturer as a timeout 
		for laser operation. When heartbeat is enabled, laser 
		shuts down in absence of RS232 activity after a set duration."""
		if enabled:
			n = 1
		else:
			n = 0
		self.write_cmd("HEARTBEAT=%i" % n)

	def write_heartbeat_rate(self, timeout):
		"""Heartbeat is defined by the manufacturer as a timeout 
		for laser operation. Heartbeat rate is defined as the laser 
		timeout in seconds. Range: 1 to 100 s."""
		assert 1 <= time <= 100
		self.write_cmd("HEARTBEATRATE=%i" % int(time))

	def write_recovery_sequence(self):
		"""Initiates recovery sequence. This can take up to 2 minutes to complete."""
		self.write_cmd("RECOVERY=%i" % 1)

	def write_alignment_mode(self, enabled=True):
		"""Enables alignment mode. Exits alignment mode otherwise."""
		if enabled:
			n = 1
		else:
			n = 0
		self.write_cmd("ALIGN=%i" % n)

	## Queries section ##

	self.faults_table = {
    0: "No Faults",
    1: "Laser Head Interlock Fault",
    2: "External Interlock Fault",
    3: "PS Cover Interlock Fault",
    4: "LBO Temperature Fault",
    5: "LBO Not Locked At Set Temp",
    6: "Vanadate Temp. Fault",
    7: "Etalon Temp. Fault",
    8: "Diode 1 Temp. Fault",
    9: "Diode 2 Temp. Fault",
    10: "Baseplate Temp. Fault",
    11: "Heatsink 1 Temp. Fault",
    12: "Heatsink 2 Temp. Fault",
    16: "Diode 1 Over Current Fault",
    17: "Diode 2 Over Current Fault",
    18: "Over Current Fault",
    19: "Diode 1 Under Volt Fault",
    20: "Diode 2 Under Volt Fault",
    21: "Diode 1 Over Volt Fault",
    22: "Diode 2 Over Volt Fault",
    25: "Diode 1 EEPROM Fault",
    26: "Diode 2 EEPROM Fault",
    27: "Laser Head EEPROM Fault",
    28: "PS EEPROM Fault",
    29: "PS-Head Mismatch Fault",
    30: "LBO Battery Fault",
    31: "Shutter State Mismatch",
    32: "CPU PROM Checksum Fault",
    33: "Head PROM Checksum Fault",
    34: "Diode 1 PROM Checksum Fault",
    35: "Diode 2 PROM Checksum Fault",
    36: "CPU PROM Range Fault",
    37: "Head PROM Range Fault",
    38: "Diode 1 PROM Range Fault",
    39: "Diode 2 PROM Range Fault",
    40: "Head - Diode Mismatch",
    43: "Lost Modelock Fault",
    47: "Ti-Sapph Temp. Fault",
    49: "PZT X Fault",
    50: "Cavity Humidity Fault",
    51: "Tuning Stepper Motor Homing",
    52: "Lasing Fault",
    53: "Laser Failed to Begin Modelocking",
    54: "Headboard Communication Fault",
    55: "System Lasing Fault",
    56: "PS-Head EEPROM Mismatch Fault",
    57: "Modelock Slit Stepper Motor Homing Fault",
    58: "CHAMELEON_VERDIEEPROM_FAULT",
    59: "CHAMELEON PRECOMPENSATOR HOMING FAULT",
    60: "CHAMELEON_CURVEEEPROM_FAULT",
    }

	def read_laser_status(self):
		resp = self.write_cmd("PRINT LASER")[:-2]
		if int(resp) == 0:
			print("Laser status: Off (Standby)")
		elif int(resp) == 1:
			print("Laser status: On")
		elif int(resp) == 2:
			print("Laser status: Off due to a fault.")

	def read_faults(self):
		"""Returns a list of number codes of all active faults, separated by an "&" 
		or returns "System OK" if there are no active faults."""
		resp = self.write_cmd("PRINT FAULTS")[:-2]
		if resp == "System OK":
			print(resp)
		else:
			faults = resp.split("&")
			for code in faults:
				print(self.faults_table[int(code)])

	def read_fault_history(self):
		"""Returns a list of number codes of all faults that have 
		occurred since the last laser on command, separated by an
		"&", or returns "System OK" if there are no latched faults. The "laser on" command or the EXIT button on the power
		supply (when the fault screen is active) clears the fault 
		history and fault screen."""
		resp = self.write_cmd("PRINT FAULT HISTORY")[:-2]
		if resp == "System OK":
			print(resp)
		else:
			faults = resp.split("&")
			for code in faults:
				print(self.faults_table[int(code)])

	def read_shutter_status(self):
		"""Returns the status of the exernal shutter"""
		resp = self.write_cmd("PRINT SHUTTER")[:-2]
		if int(resp) == 0:
			print("Shutter Closed")
		elif int(resp) == 1:
			print("Shutter Open")

	def read_UF_power(self):
		"""Returns actual UF (Chameleon) power, nnn.nn, in milliwatts."""
		resp = self.write_cmd("PRINT UF POWER")[:-2]
		print(resp)

	def read_cavity_peak_hold(self):
		"""Returns the status of the cavity peak hold."""
		resp = self.write_cmd("PRINT CAVITY PEAK HOLD")[:-2]
		if int(resp) == 0: 
			print("Cavity Peak Hold OFF")
		if int(resp) == 1:
			print("Cavity Peak Hold ON")

	def read_cavity_PZT_mode(self):
		"""Returns the mode of the cavity PZT."""
		resp = self.write_cmd("PRINT CAVITY PZT MODE")[:-2]
		if int(resp) == 0:
			print("Auto")
		elif int(resp) == 1:
			print("Manual")

	def read_cavity_PZT_X(self):
		"""Returns the cavity PZT X (Rd) voltage, n.nn, in volts."""
		resp = self.write_cmd("PRINT CAVITY PZT X")[:-2]
		return(float(resp))

	def read_cavity_PZT_Y(self):
		"""Returns the cavity PZT Y (Rd) voltage, n.nn, in volts."""
		resp = self.write_cmd("PRINT CAVITY PZT Y")
		return(float(resp))

	def read_pump_peak_hold(self):
		"""Returns the status of the pump peak hold."""
		resp = self.write_cmd("PRINT PUMP PEAK HOLD")[:-2]
		return(float(resp))

	def read_pump_PZT_mode(self):
		"""Returns the mode of the pump PZT."""
		resp = self.write_cmd("PRINT PUMP PZT MODE")[:-2]
		if int(resp) == 0:
			print("Auto")
		elif int(resp) == 1:
			print("Manual")

	def read_pump_PZT_X(self):
		"""Returns pump PZT X (Rd) voltage, n.nn, in volts."""
		resp = self.write_cmd("PRINT PUMP PZT X")[:-2]
		return(resp)

	def read_pump_PZT_Y(self):
		"""Returns pump PZT Y (Rd) voltage, n.nn, in volts."""
		resp = self.write_cmd("PRINT PUMP PZT Y")[:-2]
		return(resp)

	def read_power_track(self):
		"""Returns state of the PowerTrack."""
		resp = self.write_cmd("PRINT POWER TRACK")[:-2]
		if int(resp) == 0:
			print("PowerTrack Off")
		elif int(resp) == 1:
			print("PowerTrack On")

	def read_chameleon_state(self):
		"""Returns state of the Chameleon Ultra."""
		resp = self.write_cmd("PRINT MODELOCKED")[:-2]
		if int(resp) == 0:
			print("Off (Standby)")
		elif int(resp) == 1:
			print("Modelocked")
		elif int(resp) == 2:
			print("CW")

	def read_pump_setting(self):
		"""Returns pump power setpoint as a fraction of 
		QS to CW pump band."""
		resp = self.write_cmd("PRINT PUMP SETTING")[:-2]
		return(resp)

	def read_tuning_status(self):
		"""Returns the tuning status."""
		resp = self.write_cmd("PRINT TUNING STATUS")[:-2]
		if int(resp) == 0:
			print("Ready (i.e. no tuning operation in progress)")
		elif int(resp) == 1:
			print("Tuning in progress")
		elif int(resp) == 2:
			print("Search for Modelock in progress")
		elif int(resp) == 3:
			print("Recovery operation in progress")

	def read_search_modelock(self):
		"""Returns the status of search for modelocking."""
		resp = self.write_cmd("PRINT SEARCH MODELOCK")[:-2]
		if int(resp) == 0:
			print("Disabled")
		if int(resp) == 1:
			print("Enabled")

	def read_homed(self):
		"""Returns the homing status of the tuning motor."""
		resp = self.write_cmd("PRINT HOMED")[:-2]
		if int(resp) == 0:
			print("Tuning motor has not been homed")
		if int(resp) == 1:
			print("Tuning motor has been homed")

	def read_wavelength(self):
		"""Returns the last commanded UF (Chameleon) wavelength,
		nnn, in nanometers."""
		resp = self.write_cmd("PRINT WAVELENGTH")[:-2]
		return(resp)

	def read_stepper_position(self):
		"""Returns the position (counts) that the motor was last moved 
		to for a desired tuning."""
		resp = self.write_cmd("PRINT STEPPER POSITION")[:-2]
		return(resp)

	def read_average_diode_current(self):
		"""Returns the measured average diode current, nn.n, in amps."""
		resp = self.write_cmd("PRINT CURRENT")[:-2]
		return(resp)

	def read_diode1_current(self):
		"""Returns laser diode #1 measured current, nn.n, in amps."""
		resp = self.write_cmd("PRINT DIODE1 CURRENT")[:-2]
		return(resp)

	def read_diode2_current(self):
		"""Returns laser diode #2 measured current, nn.n, in amps."""
		resp = self.write_cmd("PRINT DIODE2 CURRENT")[:-2]
		return(resp)
	
	def read_baseplate_temp(self):
		"""Returns laser head baseplate measured temperature, nn.nn, in °C."""
		resp = self.write_cmd("PRINT BASEPLATE TEMP")[:-2]
		return(resp)

	def read_diode1_temp(self):
		"""Returns laser diode #1 set temperature, nn.nn, in °C."""
		resp = self.write_cmd("PRINT DIODE1 TEMP")[:-2]
		return(resp)

	def read_diode2_temp(self):
		"""Returns laser diode #2 set temperature, nn.nn, in °C."""
		resp = self.write_cmd("PRINT DIODE2 TEMP")[:-2]
		return(resp)

	def read_vanadate_temp(self):
		"""Returns vanadate set temperature, nn.nn, in °C."""
		resp = self.write_cmd("PRINT VANADATE TEMP")[:-2]
		return(resp)

	def read_LBO_temp(self):
		"""Returns LBO measured temperature, nnn.nn, in °C."""
		resp = self.write_cmd("PRINT LBO TEMP")[:-2]
		return(resp)

	def read_etalon_temp(self):
		"""Returns etalon measured temperature, nn.nn, in °C."""
		resp = self.write_cmd("PRINT ETALON TEMP")[:-2]
		return(resp)

	def read_diode1_set_temp(self):
		"""Returns laser diode #1 set temperature, nn.nn, in °C."""
		resp = self.write_cmd("PRINT DIODE1 SET TEMP")[:-2]
		return(resp)

	def read_diode2_set_temp(self):
		"""Returns laser diode #2 set temperature, nn.nn, in °C."""
		resp = self.write_cmd("PRINT DIODE2 SET TEMP")[:-2]
		return(resp)

	def read_vanadate_set_temp(self):
		"""Returns vanadate set temperature, nn.nn, in °C."""
		resp = self.write_cmd("PRINT VANADATE SET TEMP")[:-2]
		return(resp)

	def read_LBO_set_temp(self):
		"""Returns LBO set temperature, nnn.nn, in °C."""
		resp = self.write_cmd("PRINT LBO SET TEMP")[:-2]
		return(resp)

	def read_etalon_set_temp(self):
		"""Returns etalon set temperature, nn.nn, in °C."""
		resp = self.write_cmd("PRINT ETALON SET TEMP")[:-2]
		return(resp)

	def read_diode1_temp_drive(self):
		"""Returns laser diode #1 temperature servo drive setting."""
		resp = self.write_cmd("PRINT DIODE1 TEMP DRIVE")[:-2]
		return(resp)

	def read_diode2_temp_drive(self):
		"""Returns laser diode #2 temperature servo drive setting."""
		resp = self.write_cmd("PRINT DIODE2 TEMP DRIVE")[:-2]
		return(resp)

	def read_vanadate_drive(self):
		"""Returns LBO temperature servo drive setting."""
		resp = self.write_cmd("PRINT VANADATE DRIVE")[:-2]
		return(resp)

	def read_LBO_drive(self):
		"""Returns LBO temperature servo drive setting."""
		resp = self.write_cmd("PRINT LBO DRIVE")[:-2]
		return(resp)

	def read_etalon_drive(self):
		"""Returns etalon temperature servo drive setting."""
		resp = self.write_cmd("PRINT ETALON DRIVE")[:-2]
		return(resp)

	def read_diode1_heatsink_temp(self):
		"""Returns laser diode #1 heat sink measured temperature, nn.nn, in °C."""
		resp = self.write_cmd("PRINT DIODE1 HEATSINK TEMP")[:-2]
		return(resp)

	def read_diode2_heatsink_temp(self):
		"""Returns laser diode #2 heat sink measured temperature, nn.nn, in °C."""
		resp = self.write_cmd("PRINT DIODE2 HEATSINK TEMP")[:-2]
		return(resp)

	def read_LBO_heater(self):
		"""Returns the status of the LBO heater."""
		resp = self.write_cmd("PRINT LBO HEATER")[:-2]
		if int(resp) == 0:
			print("Off (Cooldown)")
		elif int(resp) == 1:
			print("On (Heating)")

	def read_light_reg_status(self):
		"""Returns the status of the light loop servo."""
		resp = self.write_cmd("PRINT LIGHT REG STATUS")[:-2]
		if int(resp) == 0:
			print("Open (Current Regulation)")
		elif int(resp) == 1:
			print("Locked")
		elif int(resp) == 2:
			print("Seeking")
		elif int(resp) == 3: 
			print("Fault")

	def read_diode1_servo_status(self):
		"""Returns the status of diode #1 temperature servo."""
		resp = self.write_cmd("PRINT DIODE1 SERVO STATUS")[:-2]
		if int(resp) == 0:
			print("Open")
		elif int(resp) == 1:
			print("Locked")
		elif int(resp) == 2:
			print("Seeking")
		elif int(resp) == 3: 
			print("Fault")

	def read_diode2_servo_status(self):
		"""Returns the status of diode #2 temperature servo."""
		resp = self.write_cmd("PRINT DIODE2 SERVO STATUS")[:-2]
		if int(resp) == 0:
			print("Open")
		elif int(resp) == 1:
			print("Locked")
		elif int(resp) == 2:
			print("Seeking")
		elif int(resp) == 3: 
			print("Fault")

	def read_vanadate_servo_status(self):
		"""Return the status of the vanadate temperature servo."""
		resp = self.write_cmd("PRINT VANADATE SERVO STATUS")[:-2]
		if int(resp) == 0:
			print("Open")
		elif int(resp) == 1:
			print("Locked")
		elif int(resp) == 2:
			print("Seeking")
		elif int(resp) == 3: 
			print("Fault")

	def read_LBO_servo_status(self):
		"""Returns the status of the LBO temperature servo."""
		resp = self.write_cmd("PRINT LBO SERVO STATUS")[:-2]
		if int(resp) == 0:
			print("Open")
		elif int(resp) == 1:
			print("Locked")
		elif int(resp) == 2:
			print("Seeking")
		elif int(resp) == 3: 
			print("Fault")

	def read_etalon_servo_status(self):
		"""Returns the status of the etalon temperature servo."""
		resp = self.write_cmd("PRINT ETALON SERVO STATUS")[:-2]
		if int(resp) == 0:
			print("Open")
		elif int(resp) == 1:
			print("Locked")
		elif int(resp) == 2:
			print("Seeking")
		elif int(resp) == 3: 
			print("Fault")

	def read_diode1_hours(self):
		"""Returns the number of operating hours on laser diode #1."""
		resp = self.write_cmd("PRINT DIODE1 HOURS")[:-2]
		return(resp)

	def read_diode2_hours(self):
		"""Returns the number of operating hours on laser diode #2."""
		resp = self.write_cmd("PRINT DIODE2 HOURS")[:-2]
		return(resp)

	def read_head_hours(self):
		"""Returns the number of operating hours on the system head."""
		resp = self.write_cmd("PRINT HEAD HOURS")[:-2]
		return(resp)

	def read_diode1_voltage(self):
		"""Returns the measured voltage across diode #1, n.n, in volts."""
		resp = self.write_cmd("PRINT DIODE1 VOLTAGE")[:-2]
		return(resp)

	def read_diode2_voltage(self):
		"""Returns the measured voltage across diode #2, n.n, in volts."""
		resp = self.write_cmd("PRINT DIODE2 VOLTAGE")[:-2]
		return(resp)

	def read_software_version(self):
		"""Returns the version number of the power supply software."""
		resp = self.write_cmd("PRINT SOFTWARE")[:-2]
		return(resp)

	def read_modem_baud_rate(self):
		"""Returns the present modem port baudrate."""
		resp = self.write_cmd("PRINT MODEM BAUDRATE")[:-2]
		return(resp)

	def read_power_supply_ID(self):
		"""Returns "2BC" or "2BS" for 2-bar power supply, "1BC" or "1BS" for 1-bar 
		power supply." """
		resp = self.write_cmd("PRINT POWER SUPPLY ID")[:-2]
		return(resp)

	def read_battery_voltage(self):
		"""Returns the measured voltage across the battery, nn.nn, in volts."""
		resp = self.write_cmd("PRINT BAT VOLTS")[:-2]
		return(resp)

	def read_automodelock(self):
		"""Returns the status of the automodelock routing."""
		resp = self.write_cmd("PRINT AUTOMODELOCK")[:-2]
		return(resp)

	def read_PZT_control_state(self):
		"""Returns an integer, followed by a space, followed by a short text of the PZT
		control state as displayed on the PZT control screen."""
		resp = self.write_cmd("PRINT PZT CONTROL STATE")[:-2]
		return(resp)

	def read_tuning_limit_max(self):
		"""Returns value of maximum available wavelength in nm."""
		resp = self.write_cmd("PRINT TUNING LIMIT MAX")[:-2]
		return(resp)
	
	def read_tuning_limit_max(self):
		"""Returns value of minimum available wavelength in nm."""
		resp = self.write_cmd("PRINT TUNING LIMIT MIN")[:-2]
		return(resp)

	def read_alignment_mode(self):
		"""Returns the status of the alignment mode."""
		resp = self.write_cmd("?ALIGN")[:-2]
		return(resp)

	def read_available_laser_power(self):
		"""Returns the laser power available in mW with 
		alignment mode enabled."""
		resp = self.write_cmd("?ALIGNP")[:-2]
		return(resp)

	def read_alignment_mode_wl(self):
		"""Returns the alignment mode laser wavelength in nm."""
		resp = self.write_cmd("?ALIGNW")[:-2]
		return(resp)

	def read_lock_front_panel_status(self):
		"""Returns the lock front panel status."""
		resp = self.write_cmd("?LFP")[:-2]
		if int(resp) == 1:
			print(Locked)
		elif int(resp) == 0:
			print(Unlocked)

	def read_cavity_power_map_X_PZT(self):
		"""Returns the last power map result for the cavity X PZT 
		position as a percentage of the available range."""
		resp = self.write_cmd("?PZTXCM")[:-2]
		return(resp)

	def read_cavity_X_PZT_position(self):
		"""Returns the current cavity X PZT position as a percentage
		of available range."""
		resp = self.write_cmd("?PZTXCP")[:-2]
		return(resp)

	def read_pump_power_map_X_PZT(self):
		"""Returns the last power map result for the pump X PZT
		position as a percentage of the available range."""
		resp = self.write_cmd("?PZTXPM")[:-2]
		return(resp)

	def read_pump_X_PZT_position(self):
		"""Returns the current pump X PZT position as a percentage 
		of the available range."""
		resp = self.write_cmd("?PZTXPP")[:-2]
		return(resp)

	def read_cavity_power_map_Y_PZT(self):
		"""Returns the last power map result for the cavity Y PZT 
		position as a percentage of available range."""
		resp = self.write_cmd("?PZTYCM")[:-2]
		return(resp)

	def read_cavity_Y_PZT_position(self):
		"""Returns the current cavity Y PZT position as a percentage
		of available range."""
		resp = self.write_cmd("?PZTYCP")[:-2]
		return(resp)

	def read_pump_power_map_Y_PZT(self):
		"""Returns the last power map result for the pump Y PZT
		position as a percentage of the available range."""
		resp = self.write_cmd("?PZTYPM")[:-2]
		return(resp)

	def read_pump_Y_PZT_position(self):
		"""Returns the current pump Y PZT position as a percentage of the available range."""
		resp = self.write_cmd("?PZTYPP")[:-2]
		return(resp)

	def read_relative_humidity(self):
		"""Returns the relative humidity as a percentage value."""
		resp = self.write_cmd("?RH")[:-2]
		return(resp)

	def read_serial_number(self):
		"""Returns the Chameleon Ultra serial number."""
		resp = self.write_cmd("?SN")[:-2]
		return(resp)

	def read_operating_status(self):
		"""Returns the current operating status as a text string, such as "Starting" or "OK".
		"""
		resp = self.write_cmd("?ST")[:-2]
		return(resp)
		