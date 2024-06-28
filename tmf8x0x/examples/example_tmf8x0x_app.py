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
- Start a measurement
- Stop a measurement
- Disable+close the device
'''

USE_EVM:bool = True
LOG:bool     = False

EXPECTED_PATCH=0
EXPECTED_BUILD=0   

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

    print("Configuration")
    configuration = tof.getDefaultConfiguration()
    pprint(ctypes2Dict(configuration))

    print("Calibration")
    tof.factoryCalibration()
    calibration = tof.readFactoryCalibration()
    pprint(ctypes2Dict(calibration))
    
    print("Start Measurements")
    tof.measure(config=configuration,calibration=calibration)
    
    print("Results")
    for _ in range(NUMBER_OF_RESULTS):
        resultFrame = tof.readResultFrameInt()
        pprint(ctypes2Dict(resultFrame))
        print("---")

    tof.stop()

    print("PON0")
    tof.pon0()
    time.sleep(2.0)
    print("PON1")
    tof.pon1()

    print("Restart Measurements after PON0-PON1")
    tof.measure(config=configuration,calibration=calibration)

    print("Results")
    for _ in range(NUMBER_OF_RESULTS):
        resultFrame = tof.readResultFrameInt()
        pprint(ctypes2Dict(resultFrame))
        print("---")

    tof.disable()
    tof.close()    
    print("End")
