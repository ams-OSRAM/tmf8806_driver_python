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
    print("Connect to TMF8x0x")
    if tof.enableAndStart() != tof.Status.OK:
        print("The application did not start up as expected")
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
