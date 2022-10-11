# Requirements

Although this code does NOT use spinapi directly  (but a wrapper`utils\spinapi.py`) found elsewhere, a `pip install spinapi` is still required.

`pip install spinapi`

`pip install scopefoundry`  

more info on [ScopeFoundry here](https://www.scopefoundry.org/).

The code assumes that [SpinAPI: SpinCore API and Driver Suite](http://www.spincore.com/support/spinapi/) is installed on the computer or (at least the driver and dll)

tested with python 3.7.11 and 3.10.6. 

# Datatypes and info
Datatypes some further explanations can be found in `utils\pb_typing.py`.



# Using PulseProgramGenerator

Inherit PulseProgramGenerator and override the following two functions:

```python
class ExamplePulseProgramGenerator(PulseProgramGenerator):

    def setup_additional_settings(self) -> None:
        self.settings.New('some_time', unit='us', initial=1.0)
        self.settings.New('some_duration', unit='ns', initial=500.0)
        self.settings['all_off_padding'] = 100 #in ns, or latter in GUI.

    def make_pulse_channels(self) -> None:
        S = self.settings
        start_times = np.arange(2) * (S['some_time'] * us)
        lengths = [S['some_duration'] * ns] * 2
        # assuming there are channels called 'channel_name_1' and 'channel_name_2'
        self.new_channel('channel_name_1', start_times, lengths)
        self.new_channel('channel_name_2', [1000, 2000, 3000],  [S['some_duration'] * ns] * 3)
        

```



1. Each pulse program now has  `all_off_padding` 
2. Define pulse programs in `make_pulse_channels(self)` using `new_channel` for each channel everything.
3. When you see in the console:
   `WARNING: Applied short_pulse_feature. This might affect pulse program duration.`
   this means that there is somewhere an instruction in your program that is shorter than the minimal instruction length (`5*clock_period_ns)` and therefore the pulse feature will be used. (see short pulse feature) spincore manual.
