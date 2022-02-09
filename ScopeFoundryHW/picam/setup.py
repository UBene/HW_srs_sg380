from setuptools import setup

setup(
    name = 'ScopeFoundryHW.picam',
    
    version = '0.1.0',
    
    description = 'ScopeFoundry Hardware plug-in: PICAM Princeton Instruments Camera',
    
    # Author details
    author='Edward S. Barnard',
    author_email='esbarnard@lbl.gov',

    # Choose your license
    license='BSD',

    package_dir={'ScopeFoundryHW.picam': '.'},
    
    packages=['ScopeFoundryHW.picam',],
        
    package_data={
        '':["README*", 'LICENSE', # include License and readme 
            "*.ui", # include QT ui files 
            ], 
        },
    )
