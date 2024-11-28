# /*****************************************************************************
# * Copyright (c) [2024] ams-OSRAM AG                                          *
# * All rights are reserved.                                                   *
# *                                                                            *
# * FOR FULL LICENSE TEXT SEE LICENSE.TXT                                      *
# ******************************************************************************/
 

''' Example interaction with a TMF8x0x application  
- Open the communication
- Enable the device
- select several GPIO settings
- Start a measurement
- Stop a measurement
- Disable+close the device
'''

USE_EVM:bool = True
LOG:bool     = False

NUMBER_OF_RESULTS=10

import __init__
import time
from pprint import pprint

from tmf8x0x.tmf8x0x_app import Tmf8x0xApp
from aos_com.register_io import ctypes2Dict
if USE_EVM:
    from aos_com.evm_ftdi import EvmFtdi as Ftdi
else:
    from aos_com.ft2232_ftdi import Ft2232Ftdi as Ftdi

if __name__ == "__main__":

    com = Ftdi(log=False)
    tof = Tmf8x0xApp(ic_com=com,log=LOG) 
    print("Open FTDI communication channels")
    tof.open()
    try:
        print("Connect to TMF8x0x")
        if tof.enableAndStart() != tof.Status.OK:
            print("The application did not start up as expected")
    except:
        print("Could not connect to TMF8x0x. Exiting.")
        print("Is the FTDI controller attached?")
        quit()

    print("[app_id, major, minor, patch] are: " , [f'0x{i:02x}' for i in tof.getAppId()])

    tof.enableInt(tof.TMF8X0X_APP_INTERRUPT_RESULTS)

    print("Configuration")
    configuration = tof.getDefaultConfiguration()
    configuration.data.gpio.gpio0 = 3 # 3 .. VCSEL pulse output
    configuration.data.gpio.gpio1 = 3 # 3 .. VCSEL pulse output
    configuration.data.daxDelay100us = 10 # set this to value >0 to enable VCSEL pulse output
    pprint(ctypes2Dict(configuration))

    print("Start Measurements")
    tof.measure(config=configuration)
    
    print("Results")
    for _ in range(NUMBER_OF_RESULTS):
        resultFrame = tof.readResultFrameInt()
        pprint(ctypes2Dict(resultFrame))
        print("---")

    tof.stop()



    tof.disable()
    tof.close()    
    print("End")
