# *****************************************************************************
# * Copyright by ams AG                                                       *
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
- configure thresholds for interrupt range
- Start a measurement
- Stop a measurement
- Disable+close the device
'''

USE_EVM:bool=True
LOG:bool=True

import __init__
import time

if USE_EVM:
    from aos_com.evm_ftdi import EvmFtdi as Ftdi
else:
    from aos_com.ft2232_ftdi import Ft2232Ftdi as Ftdi
from tmf8x0x.tmf8x0x_app import Tmf8x0xApp

from aos_com.register_io import ctypes2Dict
from pprint import pprint

def setThresholdsAndMeasure( tof:Tmf8x0xApp, persistence:int, low_threshold:int, high_threshold:int ):
    """
    Function that sets persistence, and thresholds and reads in the given amount of reads.

    Args:
        tof (Tmf8x0xApp): TOF application object
        persistence (int): number of consecutive results within the define distance range to trigger an interrupt
        low_threshold (int): lower boundary of distance range for object detection
        high_threshold (int): upper boundary of distance range for object detection
    Returns:
        None
    """    
    tof.setThresholds( persistence = persistence, low_threshold = low_threshold, high_threshold = high_threshold )
    pers, l_th, h_th = tof.getThresholds()
    print( f"Pesistence={pers}, low threshold={l_th}mm, high threshold={h_th}mm" )
    tof.clearAndEnableInt( tof.TMF8X0X_APP_INTERRUPT_RESULTS )
    tof.measure(tof.getDefaultConfiguration())
    if persistence:
        print( f"Please move an object in front of the sensor in the range {low_threshold} mm to {high_threshold} mm to have the sensor detect it" )
    while tof.readIntStatus() != tof.TMF8X0X_APP_INTERRUPT_RESULTS:         
        pass # wait for the user to place an object in front of hte device
    print(f"Int Status = {tof.readIntStatus()}")   
    pprint(ctypes2Dict(tof.readResultFrameInt()))
    tof.stop()

if __name__ == "__main__":
    com = Ftdi(log=False)
    tof = Tmf8x0xApp(ic_com=com,log=LOG) 
    print("Open FTDI communication channels")
    tof.open()
    print("Connect to TMF8x0x")
    if tof.enableAndStart() != tof.Status.OK:
        print("The application did not start up as expected")
    print("[app_id, major, minor, patch] are: " , [f'0x{i:02x}' for i in tof.getAppId()])

    setThresholdsAndMeasure(tof=tof,persistence=1,low_threshold=200,high_threshold=500)    
    setThresholdsAndMeasure(tof=tof,persistence=0,low_threshold=0,high_threshold=10000)    
    setThresholdsAndMeasure(tof=tof,persistence=1,low_threshold=0,high_threshold=10000)    

    tof.disable()
    tof.close()    
    print("Done")    
