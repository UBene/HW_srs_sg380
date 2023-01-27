ScopeFoundryHW.thorlabs_galvo_mirrors_nidaq
===========================================

ScopeFoundry hardware plug-in to control thorlabs galvo mirrors using a NI Data aquisition card.


ScopeFoundry is a Python platform for controlling custom laboratory 
experiments and visualizing scientific data

<http://www.scopefoundry.org>

This software is not made by or endorsed by the device manufacturer

Caution
-------
The product of the initializer arguments `max_step_degree` and `rate` define the fasted step (degrees/sec) that do not break the galvos. See manual of device manufacturer


Author
----------

Benedikt Ursprung 

Requirements
------------

	* ScopeFoundry
	* numpy
	* nidaqmx
	* ScopeFoundry.scanning (for scan measurement)
	
	
History
--------

### 0.1.0	2023-01-27	Initial public release.

Plug-in has been used internally and has been stable.
Check Git repository for detailed history.
