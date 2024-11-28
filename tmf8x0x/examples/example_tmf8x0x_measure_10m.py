# /*****************************************************************************
# * Copyright (c) [2024] ams-OSRAM AG                                          *
# * All rights are reserved.                                                   *
# *                                                                            *
# * FOR FULL LICENSE TEXT SEE LICENSE.TXT                                      *
# ******************************************************************************/
 

''' Example interaction with a TMF8x0x application in 10m mode
- Open the communication
- Enable the device
- Download the RAM patch application 
- Start a measurement 
- Measure NUMBER_OF_RESULTS results
- Stop a measurement
- Disable+close the device
'''

USE_EVM:bool = True
LOG:bool     = False

NUMBER_OF_RESULTS=100

import __init__
import os
from tmf8x0x.tmf8x0x_app import Tmf8x0xApp
from aos_com.register_io import ctypes2Dict

if USE_EVM:
    from aos_com.evm_ftdi import EvmFtdi as Ftdi
else:
    from aos_com.ft2232_ftdi import Ft2232Ftdi as Ftdi

from tmf8x0x.auto.tmf8806_regs import tmf8806StateData

if __name__ == "__main__":

    com = Ftdi(log=False)
    tof = Tmf8x0xApp(ic_com=com,log=LOG, hex_file= os.path.dirname(__file__) + "\\..\\zeromq\\fw_patch\\mainapp_PATCH_Maxwell.hex") 
    print("Open FTDI communication channels")
    tof.open()
    print("Connect to TMF8x0x")
    if tof.enableAndStart() != tof.Status.OK:
        print("The application did not start up as expected")
    print("[app_id, major, minor, patch] are: " , [f'0x{i:02x}' for i in tof.getAppId()])

    print("Configuration")
    configuration = tof.getDefaultConfiguration()

    # Adapt the configuration here
    configuration.data.algo.distanceMode = 1 # 0..2.5m
    configuration.data.repetitionPeriodMs = 100 # ~10Hz
    configuration.data.kIters = 4000 
    configuration.data.algo.reserved = 2 # 10m mode

    # do not calibrate for now
    # print("Calibration")
    # tof.factoryCalibration(timeout=9999999, config=configuration, kilo_iters=40960)
    # calibration = tof.readFactoryCalibration()
    
    print("Start Measurements")
    tof.measure(config=configuration,calibration=None)
    
    print("Results")
    for _ in range(0,NUMBER_OF_RESULTS):
        resultFrame = tof.readResultFrameInt()
        print(f"Distance: {resultFrame.distPeak}mm Confidence: {resultFrame.reliability}")

    tof.stop()
    tof.disable()
    tof.close()    
    print("End") 
