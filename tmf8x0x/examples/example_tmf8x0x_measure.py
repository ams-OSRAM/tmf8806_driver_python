# /*****************************************************************************
# * Copyright (c) [2024] ams-OSRAM AG                                          *
# * All rights are reserved.                                                   *
# *                                                                            *
# * FOR FULL LICENSE TEXT SEE LICENSE.TXT                                      *
# ******************************************************************************/
 

''' Example interaction with a TMF8x0x application  
- Open the communication
- Enable the device
- Start a measurement 
- Measure in an endless loop
- #Stop a measurement
- #Disable+close the device
'''

USE_EVM:bool = True
LOG:bool     = False

NUMBER_OF_RESULTS=10

import __init__
from tmf8x0x.tmf8x0x_app import Tmf8x0xApp
from aos_com.register_io import ctypes2Dict

if USE_EVM:
    from aos_com.evm_ftdi import EvmFtdi as Ftdi
else:
    from aos_com.ft2232_ftdi import Ft2232Ftdi as Ftdi

from tmf8x0x.auto.tmf8806_regs import tmf8806StateData

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

    print("Configuration")
    configuration = tof.getDefaultConfiguration()

    # Adapt the configuration here
    configuration.data.algo.distanceMode = 0 # 0..2.5m
    configuration.data.repetitionPeriodMs = 33 # ~30Hz
    configuration.data.kIters =  450 # 80kIter = ~2.3ms integration time

    print("Calibration")
    tof.factoryCalibration(timeout=9999999, config=configuration, kilo_iters=40960)
    calibration = tof.readFactoryCalibration()
    
    print("Start Measurements")
    tof.measure(config=configuration,calibration=calibration)
    
    print("Results")
    for _ in range(0,NUMBER_OF_RESULTS):
        resultFrame = tof.readResultFrameInt(timeout=9999999)
        state = tmf8806StateData.from_buffer(resultFrame.stateData)
        print("[{:3d}] {:4d}mm, {:2d}snr, {:2d}C".format(resultFrame.resultNum, resultFrame.distPeak, resultFrame.reliability, resultFrame.temperature))
        print(ctypes2Dict(state))

    tof.stop()

    tof.disable()
    tof.close()    
    print("End")
