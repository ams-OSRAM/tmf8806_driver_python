# *****************************************************************************
# * Copyright by ams OSRAM AG                                                 *
# * All rights are reserved.                                                  *
# *                                                                           *
# * IMPORTANT - PLEASE READ CAREFULLY BEFORE COPYING, INSTALLING OR USING     *
# * THE SOFTWARE.                                                             *
# *                                                                           *
# * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS       *
# * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT         *
# * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS         *
# * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT  *
# * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,     *
# * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT          *
# * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES LOSS OF USE,      *
# * DATA, OR PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY      *
# * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT       *
# * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE     *
# * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.      *
# *****************************************************************************

    
''' Example interaction with a TMF8x0x application  
- Open the communication 
- Enable the device
- Download the RAM patch application
- Perform a Factory Calibration
- Disable the Device
- Enable the device
- Download the RAM patch application
- Start a measurement
- Stop a measurement
- Hibernate
- Enable the device
- Download the RAM patch application
- Write factory calibration and state data
- Disable+close the device
'''

USE_EVM:bool = True
LOG:bool     = False

NUMBER_OF_RESULTS=1000

import __init__
import time
from pprint import pprint

from tmf8x0x.tmf8x0x_app import Tmf8x0xApp
from aos_com.register_io import ctypes2Dict
from tmf8x0x.auto.tmf8806_regs import tmf8806StateData

if USE_EVM:
    from aos_com.evm_ftdi import EvmFtdi as Ftdi
else:
    from aos_com.ft2232_ftdi import Ft2232Ftdi as Ftdi

if __name__ == "__main__":

    com = Ftdi(log=False)
    tof = Tmf8x0xApp(ic_com=com,log=LOG) 
    
    configuration = tof.getDefaultConfiguration()
    configuration.data.repetitionPeriodMs = 0 # single shoot for this measurement
    configuration.data.kIters = 10 # kilo-iterations (~270us at 10k)

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
    
    ## Factory Calibration ##
    
    print("Calibration")
    tof.enableAndStart()
    tof.factoryCalibration()
    calibration = tof.readFactoryCalibration()
    pprint(ctypes2Dict(calibration))

    print("First run")
    tof.disable()

    print("Start Measurements")
    stateData = None # In the first run, the state data is empty
    for _ in range(NUMBER_OF_RESULTS):
        tof.enableAndStart()
        tof.measure(config=configuration,calibration=calibration, stateData=stateData)
        resultFrame = tof.readResultFrameInt()
        tof.disable()
        time.sleep(0.1) # Hibernate 100ms
        stateData = tmf8806StateData.from_buffer(resultFrame.stateData)
        print("[{:03d}]: {:05d}mm, {:02d}snr, {:02d}°C, state={}".format( resultFrame.resultNum, resultFrame.distPeak, 
                                                                         resultFrame.reliability, resultFrame.temperature, 
                                                                         ctypes2Dict(stateData) ))
        

    tof.close()    
    print("End")
