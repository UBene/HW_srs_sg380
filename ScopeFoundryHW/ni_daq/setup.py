from setuptools import setup

setup(
    name = 'ScopeFoundryHW.ni_daq',
    
    version = '0.0.1',
    
    description = 'ScopeFoundry Hardware plug-in: National Instruments Data Acquisition (DAQmx)',
    
    # Author details
    author='Edward S. Barnard',
    author_email='esbarnard@lbl.gov',

    # Choose your license
    license='BSD',

    package_dir={'ScopeFoundryHW.ni_daq': '.'},
    
    packages=['ScopeFoundryHW.ni_daq',],
    
    #packages=find_packages('.', exclude=['contrib', 'docs', 'tests']),
    #include_package_data=True,  
    
    package_data={
        '':["*.ui"], # include QT ui files 
        '':["README*", 'LICENSE'], # include License and readme 
        },
    )
