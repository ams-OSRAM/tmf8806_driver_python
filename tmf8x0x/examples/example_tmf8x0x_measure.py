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
    # tof = Tmf8x0xApp(ic_com=com,log=LOG, hex_file=Tmf8x0xApp.DEFAULT_PATCH_FILE_UNENCRYPTED) 
    print("Open FTDI communication channels")
    tof.open()
    print("Connect to TMF8x0x")
    if tof.enableAndStart() != tof.Status.OK:
        print("The application did not start up as expected")
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
