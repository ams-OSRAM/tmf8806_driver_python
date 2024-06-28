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
- Get histograms and measurement data
- Stop a measurement
- Disable+close the device
'''

USE_EVM:bool=True

# disable verbose logging 
LOG:bool=False

import __init__
if USE_EVM:
    from aos_com.evm_ftdi import EvmFtdi as Ftdi
else:
    from aos_com.ft2232_ftdi import Ft2232Ftdi as Ftdi
from tmf8x0x.tmf8x0x_app import Tmf8x0xApp,HistogramsAndResult
import time
import os
import csv

t = time.localtime()
MEASUREMENT_DATA_FILE = os.path.dirname(__file__) + f"\\..\\csv_files\\tmf8x0x_measure-{t.tm_year}-{t.tm_mon:02}-{t.tm_mday:02}-{t.tm_hour:02}_{t.tm_min:02}_{t.tm_sec:02}.csv"

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

    f = open( MEASUREMENT_DATA_FILE, 'w', encoding='UTF8', newline='' )
    writer = csv.writer(f,delimiter=';')
    f.write( "sep=;\n" )

    print( "Configure sensor" )
    # warning: EC histograms and optical histograms only come when this is the initial measurement!
    tof.configureHistogramDumping(ec=True,prox=True,distance=True,distance_puc=True,summed=True)

    print( "Start measurements" )
    tof.measure(tof.getDefaultConfiguration())

    # read all available histograms and one result frame
    _, hr = tof.readHistogramsAndResult()
    
    # print histograms and result to the CSV file
    hr.toCSVBytes(writer)

    print( "Stop measurements" )
    tof.stop()
    tof.disable()
    tof.close()
    f.close()  
    print("End")
