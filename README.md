# Python
This folder contains libraries, tools, and tests to interact with the ams OSRAM TMF8806 devices over I2C and GPIO.

## Setup Python Environment
This framework requires to use python 3.6 or newer for Window 10/11.
To install the required packages, run `python -m pip install -r requirements.txt`.

## Adding your own sub-directory
When you add a new sub-directory and want to execute python files there you need to 
`import __init__` before any other local import. Also you need to copy the file `__init__.py` into this subdirectory
and make sure the python root path points to the directory where this readme.md file is located.
`TOF_PYTHON_ROOT_DIR = os.path.normpath(os.path.dirname(__file__) + "/..")`

This is a summary of the files and sub-folders:
	
## ./tmf8x0x
All python classes, files and functions, specific to the TMF8806.
There is a python class to control the device hardware and the bootloader that also allows to download intel hex files to the device.
There is a second class that implements measurement application specific commands and controls and data readout, as well as histogram configuration and readout.

### ./tmf8x0x/examples
Several examples that show the usage:
- how to perform measurements and read them out
- how to configure for histogram dumping and how to read them out
 
### ./tmf8x0x/tests
Python tests to verify functonality of device and/or scripts.
