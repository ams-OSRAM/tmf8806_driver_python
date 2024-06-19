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
"""
tmf8x0x app0 class and sample test with fixed hex file for download
"""

import __init__
import time
from typing import List
import csv
import os
from intelhex import IntelHex
import ctypes
from typing import Tuple

# local imports
from aos_com.ic_com import IcCom
from tmf8x0x.tmf8x0x_device import Tmf8x0xDevice
from tmf8x0x.auto.tmf8806_regs import tmf8806MeasureCmd, tmf8806FactoryCalibData, tmf8806DistanceResultFrame, tmf8806StateData

class Histogram:
    """class for storing a single histogram with bin list and histogram type"""

    # depending on the state the FW is when waiting for histogram readout, the host can determine
    # the type of histogram that is provided
    HISTOGRAM_UNKNOWN:int   = 0  # unknown histogram type
    HISTOGRAM_EC:int        = 22 # identifier for EC histogram
    HISTOGRAM_OPTICAL:int   = 23 # identifier for optical histogram
    HISTOGRAM_PROXIMITY:int = 25 # identifier for proximity histogram
    HISTOGRAM_DISTANCE:int  = 28 # identifier for distance histogram
    HISTOGRAM_SUM:int       = 29 # identifier sum histogram
    HISTOGRAM_PUC:int       = 30 # identifier for pile-up corrected histograms

    def __init__(self):
        self.type:int = self.HISTOGRAM_UNKNOWN
        self.bins:List[int] = None

    def toCSV(self, csvwriter:csv.writer):
        """
        Dump the given histograms (all 5 TDCs) to the given csvwriter in a format like the EVM does.
        Scale bin values for output.

        Args:
            csvwriter (csv.writer): a writer instance that is used to dump in csv format to a file.
        Returns:
            None.
        """
        do_scale = True
        name = ""

        if ( self.type == Histogram.HISTOGRAM_EC ):
            name = "#CI"
        elif ( self.type == Histogram.HISTOGRAM_OPTICAL ):
            name = "#CO"
        elif ( self.type == Histogram.HISTOGRAM_PROXIMITY ):
            name = "#PT"
        elif ( self.type == Histogram.HISTOGRAM_DISTANCE ):
            name = "#TG"
        elif ( self.type == Histogram.HISTOGRAM_SUM ):
            if self.bins[127] == 0: # summed histograms only fill 120 bins
                name = "#SUM"
            else:
                name = "#TGPUC" # pile-up corrected distance histograms, they fill all 128 bins
            do_scale = False
        else:
            name = "#UNKNOWN"
            do_scale = False

        msg =  [ name ] + ( Tmf8x0xApp._scaleBins(self.bins) if do_scale else self.bins )
        csvwriter.writerow(msg)

class HistogramsAndResult:
    """class for storing a set of histograms and the associated result frame"""
    def __init__(self):
        self.histogramsEc:List[List[int]]      = []
        self.histogramsOc:List[List[int]]      = []
        self.histogramsProx:List[List[int]]    = []
        self.histogramsDist:List[List[int]]    = []
        self.histogramsProcPuc:List[List[int]] = []
        self.histogramsDistPuc:List[List[int]] = []
        self.histogramSum:List[int]            = []
        self.result:tmf8806DistanceResultFrame = tmf8806DistanceResultFrame()

    def toCSVBytes(self,csvwriter:csv.writer):
        """Write all available histograms and one result frame to a CSV file.
           Write result frame as list of bytes.
        Args:
            csvwriter (csv.writer): CSV writer object
        """
        for i in range(len(self.histogramsEc)):
            csvwriter.writerow( [ f"#CI{i}" ] + self.histogramsEc[i] )
        for i in range(len(self.histogramsOc)):
            csvwriter.writerow( [ f"#CO{i}" ] + self.histogramsOc[i] )
        for i in range(len(self.histogramsProx)):
            csvwriter.writerow( [ f"#PT{i}" ] + self.histogramsProx[i] )
        for i in range(len(self.histogramsDist)):
            csvwriter.writerow( [ f"#TG{i}" ] + self.histogramsDist[i] )
        for i in range(len(self.histogramsProcPuc)):
            csvwriter.writerow( [ f"#PTPUC{i+1}" ] + self.histogramsProcPuc[i] )
        for i in range(len(self.histogramsDistPuc)):
            csvwriter.writerow( [ f"#TGPUC{i+1}" ] + self.histogramsDistPuc[i] )
        if len(self.histogramSum) > 0:
            csvwriter.writerow( [ "#SUM"] + self.histogramSum )
        if self.result:
            csvwriter.writerow( ["#RES"] + list(bytes(self.result)))

    def toCSV(self,csvwriter:csv.writer,distance_correction_factor:float=1.0, write_raw_result:bool = True):
        """Write all available histograms and one result frame to a CSV file.
           Write result frame as list of bytes in the same format as the TMF8x0x EVM GUI.
        Args:
           csvwriter (csv.writer): CSV writer object
           distance_correction_factor(float): factor to correct measured distances
           write_raw_result(bool): If True, write the raw result frame before the parsed result.
        """
        for i in range(len(self.histogramsEc)):
            csvwriter.writerow( [ f"#CI{i}" ] + self.histogramsEc[i] )
        for i in range(len(self.histogramsOc)):
            csvwriter.writerow( [ f"#CO{i}" ] + self.histogramsOc[i] )
        for i in range(len(self.histogramsProx)):
            csvwriter.writerow( [ f"#PT{i}" ] + self.histogramsProx[i] )
        for i in range(len(self.histogramsDist)):
            csvwriter.writerow( [ f"#TG{i}" ] + self.histogramsDist[i] )
        for i in range(len(self.histogramsProcPuc)):
            csvwriter.writerow( [ f"#PTPUC{i+1}" ] + self.histogramsProcPuc[i] )
        for i in range(len(self.histogramsDistPuc)):
            csvwriter.writerow( [ f"#TGPUC{i+1}" ] + self.histogramsDistPuc[i] )
        if len(self.histogramSum) > 0:
            csvwriter.writerow( [ "#SUM"] + self.histogramSum )
        if self.result:
            if write_raw_result:
                csvwriter.writerow( ["#RES"] + list(bytes(self.result)))
            out  = [ "#OBJ" ]
            out += [ str(int(time.time()*1000)) ]
            if self.result.reliability > 0:
                out += [ 1 ]                         # number of detected objects
                out += [ self.result.reliability ]   # confidence level of object
                out += [ round(self.result.distPeak*distance_correction_factor) ]
                out += [ self.result.referenceHits ] # reference photon count
                out += [ self.result.objectHits ]    # object photon count
            else:
                out += [ 0, 0, 0, 0, 0 ]
            csvwriter.writerow( out )
            csvwriter.writerow( [ "#TMP", self.result.temperature ])

class Tmf8x0xApp(Tmf8x0xDevice):
    """The TMF8x0x application class to interface the Koloth/Dahar/Leica application as a host driver would.
    """
    DEFAULT_PATCH_FILE_UNENCRYPTED = os.path.dirname(__file__) + "\\..\\..\\firmware\\app\\main_app\\PATCH_Maxwell\\objects\\mainapp_PATCH_Maxwell.hex"   

    # Version log
    # 1.0 first working version
    # 1.1 after review by M. Pelzmann
    # 2.0 rework with data structures created from C header files
    VERSION = 2.0

    LOG:bool = False

    # constants for byte / word handling
    UINT8_MAX = (1<<8)-1
    UINT16_MAX = (1<<16)-1

    TMF8X0X_COM_APP_ID = 0x0               # The application ID register.
    TMF8X0X_COM_REQ_APP_ID = 0x2           # The application switch request register.
    TMF8X0X_COM_APP_ID__application = 0xC0
    TMF8X0X_COM_APP_ID__bootloader = 0x80

    TMF8X0X_BL_MAX_DATA_SIZE = 0x80 # Number of bytes that can be written or read with one BL command

    TMF8X0X_COM_CMD_STAT                        = 0x08 # bootloader commands must be written to this address
    TMF8X0X_COM_CMD_STAT__bl_cmd_reset          = 0x10
    TMF8X0X_COM_CMD_STAT__bl_cmd_remap_reset    = 0x11 # Bootloader command to remap the vector table into RAM (Start RAM application).
    TMF8X0X_COM_CMD_STAT__bl_cmd_romremap_reset = 0x12 # Map ROM to address 0, then start.
    TMF8X0X_COM_CMD_STAT__bl_cmd_upload_init    = 0x14 # Bootloader command to set the seed for the encryption
    TMF8X0X_COM_CMD_STAT__bl_cmd_upper_16kb     = 0x19 # Enable/disable th upper 16kB main RAM.
    TMF8X0X_COM_CMD_STAT__bl_cmd_test_ram       = 0x2a # Run a main-RAM BIST.
    TMF8X0X_COM_CMD_STAT__bl_cmd_test_hist      = 0x2b # Run a histogram-RAM BIST.
    TMF8X0X_COM_CMD_STAT__bl_cmd_test_i2c       = 0x2c # Run an I2C-RAM BIST.
    TMF8X0X_COM_CMD_STAT__bl_cmd_r_ram          = 0x40 # Read from BL RAM.
    TMF8X0X_COM_CMD_STAT__bl_cmd_w_ram          = 0x41 # Write to BL RAM.
    TMF8X0X_COM_CMD_STAT__bl_cmd_crc_ram        = 0x42 # Write to BL RAM.
    TMF8X0X_COM_CMD_STAT__bl_cmd_addr_ram       = 0x43 # Select the BL RAM address to read/write to.
    TMF8X0X_COM_CMD_STAT__stat_ok               = 0x0 # Everything is okay

    TMF8X0X_COM_CMD_STAT__bl_header             = 3   # every response from bootloader has this size 

    TMF8X0X_APP_ID_MINOR                        = 0x12
    TMF8X0X_APP_CMD_STAT                        = 0x10 # application commands must be written to this register address
    TMF8X0X_APP_MODE_REG                        = 0x03 # the MODE is published here
    TMF8X0X_APP_MODE__ignore_check              = 0x7F # flag for python script only to ignore the mode

    TMF8X0X_APP_CMD_STAT__stat_ok                   = 0x0 # Everything is okay
    TMF8X0X_APP_CMD_STAT__cmd_stop                  = 0xff # Stop a measurement
    TMF8X0X_APP_CMD_STAT__cmd_factory_calibration   = 0x0a      # run factory calibration
    TMF8X0X_APP_CMD_STAT__cmd_wr_calibration        = 0x0b      # write factory calibration
    TMF8X0X_APP_CMD_STAT__cmd_set_gpio              = 0x0f      # set GPIO state without starting a measurement
    TMF8X0X_APP_CMD_STAT__cmd_wr_add_config         = 0x08      # 2 new commands to read and write additional configuration parameter
    TMF8X0X_APP_CMD_STAT__cmd_rd_add_config         = 0x09
    TMF8X0X_APP_CMD_STAT__cmd_histogram_readout     = 0x30      # 1-32-bit word as parameter
    TMF8X0X_APP_CMD_STAT__cmd_continue              = 0x32      # when a complete histogram is read, continue command is required
    TMF8X0X_APP_CMD_STAT__cmd_read_serial_number    = 0x47      # read device serial number
    TMF8X0X_APP_CMD_STAT__cmd_change_i2c_address    = 0x49      # change the I2C slave address
    TMF8X0X_APP_CMD_STAT__cmd_read_histogram        = 0x80      # start reading a complete histogram

    TMF8X0X_APP_CMD_DATA_0                          = 0x0F # application data #0 register address
    TMF8X0X_APP_CMD_DATA_1                          = 0x0E # application data #1 register address
    TMF8X0X_APP_CMD_DATA_3                          = 0x0C # application data #3 register address
    TMF8X0X_APP_CMD_DATA_4                          = 0x0B # application data #4 register address
    TMF8X0X_APP_CMD_DATA_9                          = 0x06 # application data #9 register address

    # status register values below 6 are ok
    TMF8X0X_APP_NO_ERROR                            = 0x06      # values below 6 are no error for Status register are ok
    TMF8X0X_APP_NO_CALIBRATION                      = 0x27      # no calibration data, a Warning only

    # state register values - only IDLE and ERROR state are used
    TMF8X0X_APP_STATE_IDLE                          = 1         # state IDLE and ERROR are special states
    TMF8X0X_APP_STATE_ERROR                         = 2         # state IDLE and ERROR are special states

    # some registers for the Application
    TMF8806_COM_DIAG_INFO                           = 0x1a      # diagnostic register address
    TMF8X0X_APP_COM_STATE                           = 0x1c      # tells the internal state of the statemachine, important for histogram type detected
    TMF8X0X_APP_COM_STATUS                          = 0x1d      # depending on the state regsiter this can be an error or not
    TMF8X0X_APP_COM_CONTENT                         = 0x1e
    TMF8X0X_APP_COM_TID                             = 0x1f
    TMF8X0X_APP_COM_RESULT_NUMBER                   = 0x20      # result number or histogram start
    TMF8X0X_APP_COM_CONFIDENCE                      = 0x21      # [5:0] bits are confidence
    TMF8X0X_APP_COM_DISTANCE_LSB                    = 0x22
    TMF8X0X_APP_COM_DISTANCE_MSB                    = 0x23
    TMF8X0X_APP_COM_SYS_TICK_0                      = 0x24      # SYS-Tick is 4 bytes long
    TMF8X0X_APP_COM_SERIAL_NUMBER_0                 = 0x28
    TMF8X0X_APP_COM_CROSSTALK_MSB                   = 0x30      # warning Crosstalk is big-endian encoded!!!!
    TMF8X0X_APP_COM_CROSSTALK_LSB                   = 0x31
    TMF8X0X_APP_COM_TEMPERATURE                     = 0x32
    TMF8X0X_APP_COM_REFERENCE_PHOTONCOUNT_0         = 0x33      # photon count is 4 bytes long
    TMF8X0X_APP_COM_TARGET_PHOTONCOUNT_0            = 0x37

    TMF8X0X_APP_COM_PERSISTENCE                     = 0x20
    TMF8X0X_APP_COM_LOW_THRESHOLD_LSB               = 0x21
    TMF8X0X_APP_COM_LOW_THRESHOLD_MSB               = 0x22
    TMF8X0X_APP_COM_HIGH_THRESHOLD_LSB              = 0x23
    TMF8X0X_APP_COM_HIGH_THRESHOLD_MSB              = 0x24

    # some sizes or values
    TMF8X0X_APP_RESULT_HEADER_SIZE                  = 4
    TMF8X0X_APP_RESULT_SIZE                         = ctypes.sizeof(tmf8806DistanceResultFrame) + TMF8X0X_APP_RESULT_HEADER_SIZE # read in some bytes [0x1C] ..
    TMF8X0X_APP_COM_CONTENT_result                  = 0x56      # results must have this value in register CONTENT

    # factory calibartion is uploaded to this address
    TMF8X0X_APP_FACTORY_CALIBRATION_START           = 0x20      # factory calibration data starts at this address
    TMF8X0X_APP_FACTORY_CALIBRATION_SIZE            = ctypes.sizeof(tmf8806FactoryCalibData)
    # state data is uploaded for simplicity here only together with factory calibraiton, if at all
    TMF8X0X_APP_STATE_DATA_START                    = (TMF8X0X_APP_FACTORY_CALIBRATION_START+TMF8X0X_APP_FACTORY_CALIBRATION_SIZE)
    TMF8X0X_APP_STATE_DATA_SIZE                     = 11

    TMF8X0X_APP_WRITE_CALIB  = [ 0x0F, 0x01, 0x0B ] # write calib data command, starts at register 0x0f, with bits indicatin if calib data or/and state

    # interrupt handling, bits that represent the different type of interrupt source
    TMF8X0X_APP_INTERRUPT_RESULTS   = 0x01  # bit 0 is result interrupt
    TMF8X0X_APP_INTERRUPT_DIAG      = 0x02  # bit 1 is diagnostic interrupt

    TMF8806_DIAG_HIST_ALG_PILEUP    = 16    # if TMF8806_COM_DIAG_INFO >> 1 & 0x1F == 16 -> pileup-corrected histogram

    def __init__(self, ic_com: IcCom, hex_file:str="", log:bool=False, exception_level:Tmf8x0xDevice.ExceptionLevel = Tmf8x0xDevice.ExceptionLevel.DEVICE):
        """The default constructor. It initializes the TMF8X0X driver.
        Args:
            log (bool, optional): Enable verbose driver outputs. False per default.
            exception_level (Tmf8x0xDevice.ExceptionLevel, optional): runtime exception level
            hex_file (str): The hex file to load with enableAndStart. If empty, run the ROM application. Defaults to ''.
        """
        super().__init__(ic_com=ic_com,log=log,exception_level=exception_level)
        self.hex_file = hex_file
        self._defaultConfig = tmf8806MeasureCmd()
        self._defaultConfig.data.command = 0x2
        self._defaultConfig.data.kIters = 900
        self._defaultConfig.data.repetitionPeriodMs = 100
        self._defaultConfig.data.algo.distanceEnabled = 1 # short + long distance mode
        self._defaultConfig.data.algo.distanceMode = 0 # 2.5m
        self._defaultConfig.data.algo.vcselClkDiv2 = 0 # 40MHz
        self._defaultConfig.data.snr.threshold = 0 # use default = 6.
        self._defaultConfig.data.snr.vcselClkSpreadSpecAmplitude = 0 # off
        self._defaultConfig.data.gpio.gpio0 = 0 # off
        self._defaultConfig.data.gpio.gpio1 = 0 # off
        self._defaultConfig.data.daxDelay100us = 0 # off
        self._defaultConfig.data.spreadSpecSpadChp.amplitude = 0 # off
        self._defaultConfig.data.spreadSpecSpadChp.config = 0 # two-frequency mode
        self._defaultConfig.data.spreadSpecVcselChp.amplitude = 0 # off
        self._defaultConfig.data.spreadSpecVcselChp.config = 0 # two-frequency mode
        self._defaultConfig.data.spreadSpecVcselChp.singleEdgeMode = 0 # randomize both edges

    def _log(self,msg:str):
        """generic logging function

        Args:
            msg (str): string to log
        """
        if self.LOG:print(msg)

    def switchLog(self,log:bool):
        """enable or disable log for all functions in the class

        Args:
            log (bool): True to enable class-wide logging, False otherwise
        """
        self.LOG=log

    def isAppRunning(self)->bool:
        """Check if the application is running.
        Returns:
            bool: True if the application is running, False if not
        """
        val = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_COM_APP_ID], 1)
        return val and val[0] == self.TMF8X0X_COM_APP_ID__application

    def getAppId(self)->list:
        """Get the application version.

        Returns:
            [int, int, int, int]: app_id, major, minor, patch
        """
        valA = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_COM_APP_ID], 2)
        valB = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_APP_ID_MINOR], 2)
        return valA + valB

    def _checkAppStatus(self)->Tmf8x0xDevice.Status:
        """
        Check if the application is in the error state, and if it is, then check the
        status register.
        Returns:
            Tmf8x0xDevice.Status.OK: if ok, else an error has a different value.
        """
        stateRegister = self.TMF8X0X_APP_COM_STATE
        regs = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [stateRegister], 2)
        if regs[0] == self.TMF8X0X_APP_STATE_ERROR:
            msg = "ERROR Tmf8x0xApp._checkAppStatus in ERROR state register 0x{:02x} has value 0x{:02x}, register 0x{:02x} has value 0x{:02x})".format(stateRegister,regs[0],stateRegister+1, regs[1])
            self._log(msg)
            self._setError(msg)
            return self.Status.APP_ERROR
        # only when in STATE==IDLE==1, or STATE==ERROR==2 interpret STATUS
        # this is an error code
        elif ( regs[0] == self.TMF8X0X_APP_STATE_IDLE ) and ( regs[1] > self.TMF8X0X_APP_NO_ERROR and regs[1] != self.TMF8X0X_APP_NO_CALIBRATION):
            msg = "ERROR Tmf8x0xApp._checkAppStatus state register 0x{:02x} has value 0x{:02x}, status register 0x{:02x} has value 0x{:02x})".format(stateRegister,regs[0],stateRegister+1, regs[1])
            self._log(msg)
            self._setError(msg)
            return self.Status.APP_ERROR
        else:
            msg = "Tmf8x0xApp._checkAppStatus state register 0x{:02x} has value 0x{:02x}, register 0x{:02x} has value 0x{:02x})".format(stateRegister,regs[0],stateRegister+1, regs[1])
            self._log(msg)
            return self.Status.OK

    def _checkCmdDone(self, cmd:int, timeout: float)->Tmf8x0xDevice.Status:
        """
        Check if the command is completed
        Args:
            cmd (int): A valid command for the device application.
            timeout (float): how long to try to figure out that the command is done.
        Returns:
            Tmf8x0xDevice.Status.OK: if ok, else an error has a different value.
        """
        maxTime = time.time() + timeout
        regAddr = self.TMF8X0X_APP_CMD_STAT
        while True:
            regs = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [regAddr], 2)
            if ( regs[0] == 0 ) and ( regs[1] == cmd ):
                msg1 = "Tmf8x0xApp._checkCmdDone register 0x{:02x} has value 0x{:02x}, register 0x{:02x} has value 0x{:02x})".format(regAddr,regs[0],regAddr+1, regs[1])
                self._log(msg1)
                return self.Status.OK # okay, done, if one after command regsister is command, then command is done
            if ( time.time() > maxTime):
                break # do while loop - usefull when stepping through

        msg2="Tmf8x0xApp._checkCmdDone Timeout expected register 0x{:02x} has value 0x{:02x}, register 0x{:02x} has value 0x{:02x})".format(regAddr,0,regAddr+1,cmd)
        self._setError(msg2)
        return self.Status.APP_ERROR

    def _checkAppStatusAndCommandDone(self,cmd:int, timeout: float)->Tmf8x0xDevice.Status:
        """check if an error occured during command execution and if command execution is finished, convenience wrapper

        Args:
            cmd (int): A valid command for the device application.
            timeout (float): how long to try to figure out that the command is done.

        Returns:
            Tmf8x0xDevice.Status.OK: if ok, else an error has a different value.
        """
        status:Tmf8x0xDevice.Status = self._checkCmdDone(cmd=cmd,timeout=timeout)
        if status == self.Status.OK:
            return self._checkAppStatus()
        return status

    def _waitForCalibrationDone(self,timeout:float=10.0)->Tmf8x0xDevice.Status:
        """wait until factory calibration has finished

        Args:
            timeout (float, optional): maximum time to wait for calibration execution finish. Defaults to 10.0.

        Returns:
            Tmf8x0xDevice.Status: _description_
        """
        maxTime = time.time() + timeout
        while True:
            interrupt = self.readAndClearInt(self.TMF8X0X_APP_INTERRUPT_RESULTS)
            if ( interrupt == self.TMF8X0X_APP_INTERRUPT_RESULTS ):
                blob = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [ self.TMF8X0X_APP_COM_CONTENT ], 1)
                if (len(blob) > 0) and (blob[0] == self.TMF8X0X_APP_CMD_STAT__cmd_factory_calibration):
                    return self.Status.OK
            if ( time.time() > maxTime ):
                return self.Status.TIMEOUT_ERROR

    def factoryCalibration(self, config:tmf8806MeasureCmd=None, kilo_iters:int = 40960, timeout: float = 10.0)->Tmf8x0xDevice.Status:
        """
        Execute a factory calibration sequence.
        Args:
            config (tmf8806MeasureCmd, optional): The measurement config with the settings for the calibration. kIters and calibration type will be overwritten. Defaults to None.
            kilo_iters (int, optional): The kilo-iterations for the factory calibration. Defaults to 40960.
            timeout (float, optional): Maximum time to wait for factory calibration completion. Defaults to 10.0.

        Returns:
            Tmf8x0xDevice.Status.OK: if ok, else an error has a different value.
        """
        # clear the result place to check if it becomes non-zero == command completed
        if not config:
            config = self._defaultConfig
        fact_cal = tmf8806MeasureCmd.from_buffer_copy(bytes(config))
        fact_cal.data.kIters = kilo_iters
        fact_cal.data.command = self.TMF8X0X_APP_CMD_STAT__cmd_factory_calibration
        self.measure(fact_cal)
        return self._waitForCalibrationDone(timeout=timeout)

    def getDefaultConfiguration(self)->tmf8806MeasureCmd:
        """
        Provide default configuration for re-use in example programs
        Returns:
            tmf8806MeasureCmd: tmf8806MeasureCmd object
        """
        return tmf8806MeasureCmd.from_buffer_copy(bytes(self._defaultConfig)) # deep copy

    def readFactoryCalibration(self)->tmf8806FactoryCalibData:
        """
        Read back the factory calibration.
        Returns:
            tmf8806FactoryCalibData: calibration data object or None
        """
        blob = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_APP_FACTORY_CALIBRATION_START], self.TMF8X0X_APP_FACTORY_CALIBRATION_SIZE)
        if not blob:
            msg = "ERROR Tmf8x0xApp.readFactoryCalibration failed (reading register 0x{:02x} and the following {})".format(self.TMF8X0X_APP_FACTORY_CALIBRATION_START,self.TMF8X0X_APP_FACTORY_CALIBRATION_SIZE)
            self._log(msg)
            self._setError(msg)
            return None
        return tmf8806FactoryCalibData.from_buffer_copy(bytes(blob))

    def setFactoryCalibration(self,calibration:tmf8806FactoryCalibData, timeout: float = 0.01)->Tmf8x0xDevice.Status:
        """
        Upload the factory calibration data to the register where it will be read in by the FW when the Write-Calibration command
        is issued by this function.
        Args:
            calibration (Tmf8806FactoryCalibrationData, optional): calibration data object
            timeout (float, optional): How long to wait until command is completed. Defaults to 0.01.
        Returns:
            Tmf8x0xDevice.Status.OK: if ok, else an error has a different value.
        """
        data = [self.TMF8X0X_APP_FACTORY_CALIBRATION_START] + list(bytes(calibration))
        msg = "Tmf8x0xApp.setFactoryCalibration set calibration data: ",  [f'0x{i:02x}' for i in data]
        self._log(msg)
        self.com.i2cTx(self.I2C_SLAVE_ADDR, data)
        if ( timeout == 0.0 ):
            return self.Status.OK           # do not send the calibration command
        msg = "Tmf8x0xApp.setFactoryCalibration WRITE CALIBRATION TO DEVICE"
        self._log(msg)
        cmd = self.TMF8X0X_APP_WRITE_CALIB
        self.com.i2cTx(self.I2C_SLAVE_ADDR, cmd )
        return self._checkAppStatusAndCommandDone(cmd=self.TMF8X0X_APP_CMD_STAT__cmd_wr_calibration, timeout=timeout)

    def setThresholds(self, persistence:int=0, low_threshold:int=0,high_threshold:int=10000, timeout:float=0.001)->Tmf8x0xDevice.Status:
        """Set additional configuration
        Args:
            persistence(int): how many times a result needs to be in the specified range to provide a result and trigger an interrupt. Defaults to 0 (always).
            low_threshold(int): any result that is >= then this threshold will be reported (if persistence is achieved). defaults to 0.
            high_threshold(int): any result that is <= this will be reported (if persistence is achieved). defaults to 0
            timeout (float, optional): How long to wait until command is completed. Defaults to 0.001.
        Returns:
            Tmf8x0xDevice.Status.OK: if ok, else an error has a different value.
        """
        # saturate input values
        persistence = persistence if persistence < self.UINT8_MAX else self.UINT8_MAX
        low_threshold = low_threshold if low_threshold < self.UINT16_MAX else self.UINT16_MAX
        high_threshold = high_threshold if high_threshold < self.UINT16_MAX else self.UINT16_MAX

        cmd = [ self.TMF8X0X_APP_CMD_DATA_4, 0, 0, 0, 0, 0, self.TMF8X0X_APP_CMD_STAT__cmd_wr_add_config ]
        cmd[1] = persistence
        cmd[2] = low_threshold % 256
        cmd[3] = low_threshold // 256
        cmd[4] = high_threshold % 256
        cmd[5] = high_threshold // 256
        self.com.i2cTx(self.I2C_SLAVE_ADDR, cmd )
        return self._checkAppStatusAndCommandDone(cmd=self.TMF8X0X_APP_CMD_STAT__cmd_wr_add_config, timeout=timeout)

    def getThresholds(self, timeout:float=0.001)->Tuple[int,int,int]:
        """Read back the additional configuration of the device
            timeout (float, optional): How long to wait until command is completed. Defaults to 0.001.
        Returns:
            persistence, low_threshold, high_threshold values
        """
        cmd = [ self.TMF8X0X_APP_CMD_STAT, self.TMF8X0X_APP_CMD_STAT__cmd_rd_add_config ]
        self.com.i2cTx(self.I2C_SLAVE_ADDR, cmd )
        status = self._checkAppStatusAndCommandDone(cmd=self.TMF8X0X_APP_CMD_STAT__cmd_rd_add_config, timeout=timeout)
        if ( status == self.Status.OK ):
            data = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [ self.TMF8X0X_APP_COM_CONTENT ], 7 )
            regAddr = self.TMF8X0X_APP_COM_CONTENT
            if ( data[ self.TMF8X0X_APP_COM_CONTENT - regAddr ] == self.TMF8X0X_APP_CMD_STAT__cmd_rd_add_config ):
                # this is a rd additional configuration record
                persistence = data[self.TMF8X0X_APP_COM_PERSISTENCE - regAddr ]
                low_threshold = data[self.TMF8X0X_APP_COM_LOW_THRESHOLD_LSB -regAddr] + (data[self.TMF8X0X_APP_COM_LOW_THRESHOLD_MSB -regAddr] << 8)
                high_threshold = data[self.TMF8X0X_APP_COM_HIGH_THRESHOLD_LSB -regAddr] + (data[self.TMF8X0X_APP_COM_HIGH_THRESHOLD_MSB -regAddr] << 8)
                msg = "Persistence={}, low threshold={}mm, high threshold={}mm".format(persistence, low_threshold, high_threshold)
                self._log(msg)
                return persistence, low_threshold, high_threshold
        else:
            return -1, -1, -1   # error

    def setGPIO(self, gpio0:int=0, gpio1:int=0,timeout:float=0.01)->Tmf8x0xDevice.Status:
        """Set the state of the GPIOs without starting a measurement. Please note: setting gpiox = 3 does not enable VCSEL pulse output.
           You need to use the GPIO control of the measurement command and set configuration.data.daxDelay100us to a value > 0 to do this:
           e.g.:

           configuration = tof.getDefaultConfiguration()
           configuration.data.gpio.gpio0 = 3 # 3 .. VCSEL pulse output
           configuration.data.gpio.gpio1 = 3 # 3 .. VCSEL pulse output
           configuration.data.daxDelay100us = 10 # set this to value >0 to enable VCSEL pulse output

        Args:
            gpio0 (int): GPIO0 state, 0 .. input, 1 .. input active LO stops measurements, 2 .. input active HI stops measurements, 3 .. VCSEL pulse output, 4 .. output LO, 5 .. output HI. Defaults to 0.
            gpio1 (int): GPIO0 state, 0 .. input, 1 .. input active LO stops measurements, 2 .. input active HI stops measurements, 3 .. VCSEL pulse output, 4 .. output LO, 5 .. output HI. Defaults to 0.
            timeout (float, optional): How long to wait until command is completed.. Defaults to 0.01.

        Returns:
            Tmf8x0xDevice.Status.OK: if ok, else an error has a different value.
        """
        gpio0 = gpio0 if ( gpio0 >= 0 and gpio0 <= 5 ) else 0
        gpio1 = gpio1 if ( gpio1 >= 0 and gpio1 <= 5 ) else 0
        gpio =  gpio0 | ( gpio1 << 4 )
        cmd = [ self.TMF8X0X_APP_CMD_DATA_0, gpio, self.TMF8X0X_APP_CMD_STAT__cmd_set_gpio ]
        self.com.i2cTx(self.I2C_SLAVE_ADDR, cmd )
        return self._checkAppStatusAndCommandDone(cmd=self.TMF8X0X_APP_CMD_STAT__cmd_set_gpio, timeout=timeout)

    def measure(self, config:tmf8806MeasureCmd, calibration:tmf8806FactoryCalibData = None, stateData:tmf8806StateData = None, timeout:float=1.0)->Tmf8x0xDevice.Status:
        """
        Start a measurement.
        Args:
            config (tmf8806MeasureCmd): configuration data
            calibration (tmf8806FactoryCalibData, optional): calibration data
            stateData (tmf8806StateData, optional): state data
            timeout (float, optional): How long to allow for a measurement to start in seconds. Defaults to 1.0 seconds
        Returns:
            Tmf8x0xDevice.Status.OK: if ok, else an error has a different value.
        """
        additional_data = bytearray()
        if calibration:
            config.data.data.factoryCal = 1 # Append factory calibration, then state data (order is the same as FW reads back).
            additional_data += bytearray(calibration)
        else:
            config.data.data.factoryCal = 0

        if stateData:
            config.data.data.algState = 1
            additional_data += bytearray(stateData)
        else:
            config.data.data.algState = 0
        if additional_data:
            self.com.i2cTx(self.I2C_SLAVE_ADDR, bytearray([self.TMF8X0X_APP_FACTORY_CALIBRATION_START]) + additional_data)


        self.com.i2cTx(self.I2C_SLAVE_ADDR, bytes([self.TMF8X0X_APP_CMD_DATA_9]) + bytes(config))
        return self._checkAppStatusAndCommandDone(cmd=config.data.command, timeout=timeout)

    def stop(self, timeout: float = 0.050) -> Tmf8x0xDevice.Status:
        """
        Issue a stop command and wait for completion
        Args:
            timeout (float, optional): How long to wait for the stop to be done. Defaults to 0.050 seconds.
        Returns:
            Tmf8x0xDevice.Status.OK: if ok, else an error has a different value.
        """
        cmd = [ self.TMF8X0X_APP_CMD_STAT, self.TMF8X0X_APP_CMD_STAT__cmd_stop ] # start in Register 0x10 and is only 1 value = 0x0a
        self.com.i2cTx(self.I2C_SLAVE_ADDR, cmd)
        status = self._checkAppStatusAndCommandDone(self.TMF8X0X_APP_CMD_STAT__cmd_stop, timeout=timeout)
        # Clear any results pending, so the next measurement
        self.clearIntStatus( self.TMF8X0X_APP_INTERRUPT_RESULTS | self.TMF8X0X_APP_INTERRUPT_DIAG )
        return status

    def readResultFrameInt(self,timeout:float=1.0)->tmf8806DistanceResultFrame:
        """
        Read a result frame if the interrupt is set and return it
        Args:
            timeout (float, optional): How long to wait for an interrupt to occur. Defaults to 1.0 seconds
            log (bool, optional): print info message or not. Defaults to False.
        Returns:
            tmf8806DistanceResultFrame: result frame or None
        """
        maxTime = time.time() + timeout
        while True:
            interrupt = self.readAndClearInt(self.TMF8X0X_APP_INTERRUPT_RESULTS)
            if ( interrupt == self.TMF8X0X_APP_INTERRUPT_RESULTS ):
                results = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_APP_COM_STATE], self.TMF8X0X_APP_RESULT_SIZE)
                if len(results) > 0:
                    return tmf8806DistanceResultFrame.from_buffer_copy(bytes(results[self.TMF8X0X_APP_RESULT_HEADER_SIZE:]))
                else:
                    return None

            if ( time.time() > maxTime ):
                msg = "TMF8x0x.readResultFrameInt: timeout"
                self._log(msg)
                self._setError(msg)

    def configureHistogramDumping(self, ec:bool=False, prox:bool=False, distance:bool=False, distance_puc:bool=False, summed:bool=False,  timeout:float=0.01)->Tmf8x0xDevice.Status:
        """
        Configure to dump histograms (if at least one of the bool parameters except log are True) or not dump any (all bool parameters except log must be False) )
        Args:
            ec (bool, optional): Configure device to dump electrical calibration histograms. Defaults to False.
            prox (bool, optional): Configure device to dump proximity histograms. Defaults to False.
            distance (bool, optional): Configure device to dump distance histograms. Defaults to False.
            optical (bool, optional): Configure device to dump optical calibration histograms. Defaults to False.
            distance_puc (bool, optional): Configure device to dump pile-up corrected distance histograms. Defaults to False.
            summed (bool, optional): Configure device to dump a pile-up corrected summed histogram. Defaults to False.
            timeout (float, optional): How long to wait for an command to complete. Defaults to 0.01.
            log (bool, optional): print info message or not. Defaults to False.
        Returns:
            Tmf8x0xDevice.Status.OK: if ok, else an error has a different value.
        """
        cmd_data3 = 0
        if ( ec ):          cmd_data3 = cmd_data3 | 0x02
        if ( prox ):        cmd_data3 = cmd_data3 | 0x10
        if ( distance ):    cmd_data3 = cmd_data3 | 0x80
        cmd_data2 = 0
        cmd_data1 = 0
        if ( distance_puc ): cmd_data1 = cmd_data1 | 0x1
        if ( summed ):       cmd_data1 = cmd_data1 | 0x2
        cmd_data0 = 0
        cmd = self.TMF8X0X_APP_CMD_STAT__cmd_histogram_readout
        reg_addr = self.TMF8X0X_APP_CMD_DATA_3
        command = [reg_addr, cmd_data3, cmd_data2, cmd_data1, cmd_data0, cmd ]
        self.com.i2cTx(self.I2C_SLAVE_ADDR, command )
        self._log("Diagnostics histogram readout enabled for Addr=0x{:02x} 0x{:02x} {:02x} {:02x} {:02x}".format(reg_addr,cmd_data3,cmd_data2,cmd_data1,cmd_data0))
        return self._checkAppStatusAndCommandDone(cmd=cmd, timeout=timeout)

    def continueAfterHistogram(self, timeout:float=0.01)->Tmf8x0xDevice.Status:
        """
        Command that needs to be issued after the devices has provided a complete histogram (e.g. all 5 channel for EC)
        Args:
            timeout (float, optional): How long to wait for an command to complete. Defaults to 0.01.
        Returns:
            Tmf8x0xDevice.Status.OK: if ok, else an error has a different value.
        """
        cmd = self.TMF8X0X_APP_CMD_STAT__cmd_continue
        command = [ self.TMF8X0X_APP_CMD_STAT, cmd ]
        self.com.i2cTx(self.I2C_SLAVE_ADDR, command )
        return self._checkAppStatusAndCommandDone(cmd=cmd, timeout = timeout)

    def _readSingleHistogram(self, id:int, timeout:float=1.0)->Tuple[Tmf8x0xDevice.Status,Histogram]:
        """
        Read in a single tdc histogram of 4 quadrants, each is 64 bins each bin 2 bytes wide
        Args:
            id (int): histogram quarter ID.
            timeout (float,optional): timeout value for histogram reading, defaults to 1.0s
        Returns:
            Tmf8x0xDevice.Status, Histogram: status and histogram object with histogram type and bin list
        """
        hist = Histogram()
        hist.bins = [0 for i in range(256)]
        out = time.time() + timeout
        for tid in range( 4 ):
            while True:                         # stay in this loop until the quarter is read
                if time.time() > out:
                    return self.Status.TIMEOUT_ERROR, hist
                regAddr = self.TMF8X0X_APP_COM_STATE
                header = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [regAddr], 4)
                if ( header[ 0 ] != self.TMF8X0X_APP_STATE_ERROR ):   # if the state machine is not in state error
                    hist.type = header[ 0 ]         # the state defines the histogram type
                    if hist.type == Histogram.HISTOGRAM_SUM and tid > 1:
                        return self.Status.OK, hist
                    if ( header[ 2 ] == id ):
                        self._log("Quarter histogram received 0x{:2x}".format(header[2]))
                        data = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_APP_COM_RESULT_NUMBER], 128 )
                        if ( data ):
                            for i in range(64):
                                hist.bins[64*tid+i] = data[2*i]+data[2*i+1]*256
                                self._log("Histogram 0x{:02x}".format( id ))
                                self._log(hist.bins)
                            id = id + 1
                            break # go on with next quarter
                else:
                    self._log("Error state during histogram reading")
                    return self.Status.APP_ERROR, hist

        return self.Status.OK, hist

    def readHistogramsUnscaled(self, timeout:float=1.0)->Tuple[Tmf8x0xDevice.Status,List[Histogram]]:
        """
        Function to read a complete histogram series of one type (i.e. 5 histograms each with 256 bins).
        Function does not scale bin values.

        Args:
            timeout (float, optional): time-out for status checking and histogram reads. Defaults to 0.1.
        Returns:
            Tmf8x0xDevice.Status, list: status and a list of 5 histograms (one for each TDC).
        """
        interrupt = self.readAndClearInt( self.TMF8X0X_APP_INTERRUPT_DIAG )
        EMPTY_HISTOGRAMS = [ None, None, None, None, None ]
        if ( interrupt ):
            cmd = self.TMF8X0X_APP_CMD_STAT__cmd_read_histogram
            command = [ self.TMF8X0X_APP_CMD_STAT, cmd ]
            self.com.i2cTx(self.I2C_SLAVE_ADDR, command )
            statusCheck = self._checkCmdDone(cmd=cmd, timeout=timeout)
            if (  statusCheck == self.Status.OK ):
                id  = cmd
                self._log( "TMF8x0x reading histogram at {:10.3f}".format( time.time() ) )

                hist0:Histogram = None
                hist1:Histogram = None
                hist2:Histogram = None
                hist3:Histogram = None
                hist4:Histogram = None

                status, hist0 = self._readSingleHistogram( id )
                if ( status != self.Status.OK ): return status, EMPTY_HISTOGRAMS

                if hist0.type != Histogram.HISTOGRAM_SUM:
                    status, hist1 = self._readSingleHistogram( id +  4, timeout=timeout )
                    if ( status != self.Status.OK ): return status, EMPTY_HISTOGRAMS
                    status, hist2 = self._readSingleHistogram( id +  8, timeout=timeout )
                    if ( status != self.Status.OK ): return status, EMPTY_HISTOGRAMS
                    status, hist3 = self._readSingleHistogram( id + 12, timeout=timeout )
                    if ( status != self.Status.OK ): return status, EMPTY_HISTOGRAMS
                    status, hist4 = self._readSingleHistogram( id + 16, timeout=timeout )
                    if ( status != self.Status.OK ): return status, EMPTY_HISTOGRAMS
                else:
                    # read diagnostic register to find out if we have a summed histogram 
                    # or a pileup-corrected histogram
                    header = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [self.TMF8806_COM_DIAG_INFO], 1)
                    htype = ( header[0] >> 1 ) & 0x1F
                    if ( htype == self.TMF8806_DIAG_HIST_ALG_PILEUP):
                        hist0.type = Histogram.HISTOGRAM_PUC

                status = self.continueAfterHistogram()
                if ( status != self.Status.OK ): return status, EMPTY_HISTOGRAMS

                return self.Status.OK, [ hist0, hist1, hist2, hist3, hist4 ]
            else:
                return statusCheck, EMPTY_HISTOGRAMS

    def _scaleBins(self,bins:List[int]):
        """Scale histograms with the scaling factors in bin[127] for channel 0 and bin[255] for channel 1

        Args:
            bins (List[int]): list of bin values

        Returns:
            List[int]: list of scaled bin values
        """
        if len(bins) <= self.UINT8_MAX:
            return bins
        else:
            return ([bin << bins[127] for bin in bins[0:127]]
                    + bins[127:128]
                    + [bin << bins[255] for bin in bins[128:255]]
                    + bins[255:])

    def readHistogramsAndResult(self,timeout:float=10.0)->Tuple[Tmf8x0xDevice.Status,HistogramsAndResult]:
        """Read all available histograms. Stop as soon as a result frame arrives.

        Args:
            timeout (float, optional): Maximum time to retrieve all histograms and a result frame. Defaults to 10.0.

        Returns:
            Tmf8x0xDevice.Status, HistogramsAndResult: status, histograms and result object
        """
        hr = HistogramsAndResult()
        out = time.time() + timeout
        while True:
            if time.time() > out:
                return self.Status.TIMEOUT_ERROR, hr

            interrupt = self.readIntStatus() # only read INT status here once

            if interrupt & self.TMF8X0X_APP_INTERRUPT_RESULTS:
                hr.result = self.readResultFrameInt(timeout=timeout)
                return self.Status.OK, hr
            if interrupt & self.TMF8X0X_APP_INTERRUPT_DIAG:
                status, histograms = self.readHistogramsUnscaled(timeout=timeout)
                if ( status != self.Status.OK ):
                    return self.Status.APP_ERROR, hr
                if histograms and histograms[0]:
                    if histograms[0].type == Histogram.HISTOGRAM_EC:
                        hr.histogramsEc = []
                        for histogram in histograms:
                            if histogram:
                                hr.histogramsEc.append(self._scaleBins(histogram.bins))
                    if histograms[0].type == Histogram.HISTOGRAM_OPTICAL:
                        hr.histogramsOc = []
                        for histogram in histograms:
                            if histogram:
                                hr.histogramsOc.append(self._scaleBins(histogram.bins))
                    if histograms[0].type == Histogram.HISTOGRAM_PROXIMITY:
                        hr.histogramsProx = []
                        for histogram in histograms:
                            if histogram:
                                hr.histogramsProx.append(self._scaleBins(histogram.bins))
                    if histograms[0].type == Histogram.HISTOGRAM_DISTANCE:
                        hr.histogramsDist = []
                        for histogram in histograms:
                            if histogram:
                                hr.histogramsDist.append(self._scaleBins(histogram.bins))
                    if histograms[0].type == Histogram.HISTOGRAM_SUM: 
                            hr.histogramSum = [ bin * 4 for bin in histograms[0].bins ]                # scale summed histogram with a factor of 4
                    if histograms[0].type == Histogram.HISTOGRAM_PUC:              
                        if len(hr.histogramsDistPuc) == 4:
                            hr.histogramsDistPuc = []
                        for histogram in histograms:   
                            if histogram:
                                hr.histogramsDistPuc.append( [ bin * 2 for bin in histogram.bins ] )   # scale PUC histograms with a factor of 4

    def isDiagnosticInterrupt(self)->bool:
        """
        Check if the diagnostic interrupt bit is set in the INT_STATUS register
        Returns:
            bool: True if the diagnostic interrupt has been triggered
        """
        return self.readIntStatus() & self.TMF8X0X_APP_INTERRUPT_DIAG

    def isResultInterrupt(self)->bool:
        """
        Check if the result interrupt bit is set in the INT_STATUS register
        Returns:
            bool: True if the result interrupt has been triggered
        """
        return self.readIntStatus() & self.TMF8X0X_APP_INTERRUPT_RESULTS


    def enableAndStart(self)->Tmf8x0xDevice.Status:
        """Convenience function that enables the device, optionally downloads a RAM (patch) application, and starts the application.

        Returns:
            Tmf8x0xDevice.Status: The status of the app start.
        """
        self.enable()
        if self.hex_file:
            #self.uploadInitForEncryptedDevices() # only for encrypted devices.
            self.downloadHexFile(self.hex_file)
            return self.startRamApp()
        else:
            return self.startRomApp()
    
    def readSerialNumber(self,timeout:float=0.5)->Tuple[Tmf8x0xDevice.Status,List[int]]:
        """retrieve the device serial number

        Args:
            timeout (float, optional): command execution timeout. Defaults to 0.5.

        Returns:
            Tuple[Tmf8x0xDevice.Status,List[int]]: command execution status and list of 4 bytes
        """
        INVALID_SERIAL_NUMBER = [ -1, -1, -1, -1 ]
        cmd = [ self.TMF8X0X_APP_CMD_STAT, self.TMF8X0X_APP_CMD_STAT__cmd_read_serial_number ]
        self.com.i2cTx(self.I2C_SLAVE_ADDR, cmd)
        status = self._checkAppStatusAndCommandDone(self.TMF8X0X_APP_CMD_STAT__cmd_read_serial_number, timeout=timeout)
        if status != self.Status.OK:
            return status, INVALID_SERIAL_NUMBER
        regs = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [ self.TMF8X0X_APP_COM_CONTENT ], 1 )
        if regs[0] != self.TMF8X0X_APP_CMD_STAT__cmd_read_serial_number:
            return self.Status.APP_ERROR, INVALID_SERIAL_NUMBER
        regs = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [ self.TMF8X0X_APP_COM_SERIAL_NUMBER_0 ], 4)
        self._log(f"Serial number {regs[0]:02X} {regs[1]:02X} {regs[2]:02X} {regs[3]:02X}")
        return self.Status.OK, [ regs[0], regs[1], regs[2], regs[3] ]

    def changeI2Caddress(self,address:int=Tmf8x0xDevice.I2C_SLAVE_ADDR,mask:int=0,value:int=0,timeout:float=0.5)->Tmf8x0xDevice.Status:
        """Change the I2C slave address of the TOF sensor. The I2C address change is executed only if
          (mask_gpio1 & GPIO1) << 1 + (mask_gpio0 & GPIO0) == value_gpio1 << 1 + value_gpio0
          where GPIO1 and GPIO0 is the current status on pin GPIO1 and pin GPIO0.
          If this conditional programming is not used, set mask and value to 0x00.

        Args:
            address (int, optional): new I2C slave address
            mask (int, optional): select GPIO mask. Defaults to 0.
            value (int, optional): select GPIO value. Defaults to 0.
            timeout (float, optional): command execution timeout. Defaults to 0.1.

        Returns:
            Tmf8x0xDevice.Status.OK: if ok, else an error has a different value.
        """
        unchanged_address = self.I2C_SLAVE_ADDR
        cmd_data0  =   abs(mask) & 0x3
        cmd_data0 += ( abs(value) & 0x3 ) << 2
        cmd_data1  = address if address > 1 else Tmf8x0xDevice.I2C_SLAVE_ADDR
        cmd = [ self.TMF8X0X_APP_CMD_DATA_1, cmd_data1 << 1, cmd_data0, self.TMF8X0X_APP_CMD_STAT__cmd_change_i2c_address ]
        self.com.i2cTx(self.I2C_SLAVE_ADDR, cmd )
        time.sleep(0.1)
        self.I2C_SLAVE_ADDR = cmd_data1
        status = self._checkAppStatusAndCommandDone(cmd=self.TMF8X0X_APP_CMD_STAT__cmd_change_i2c_address, timeout=timeout)
        if self.Status.OK != status:
            self.I2C_SLAVE_ADDR = unchanged_address
        return status

    @staticmethod
    def factoryCalibUnpackToDict(data: bytes) ->dict:
        """Convert a raw factory calibration to a dictionary.

        Args:
            data (bytearray): The raw factory calibration.

        Returns:
            dict: The dictionary with the parsed factory calibration .
        """
        raw = tmf8806FactoryCalibData.from_buffer(data)
        res = {}
        res["id"] = raw.id
        res["crosstalkIntensity"] = raw.crosstalkIntensity
        res["opticalOffsetQ3"] = raw.opticalOffsetQ3
        xtalk0 = (raw.crosstalkTdc1Ch0BinPosUQ6Msb << 8) | raw.crosstalkTdc1Ch0BinPosUQ6Lsb
        xtalk0 = xtalk0 * 2**-6 if (xtalk0 < 2**11) else ( xtalk0 - 2**12 )* 2**-6 # Q6.6
        delta_xtalks = [
            0,
            raw.crosstalkTdc1Ch1BinPosDeltaQ6,
            raw.crosstalkTdc2Ch0BinPosDeltaQ6,
            raw.crosstalkTdc2Ch1BinPosDeltaQ6,
            (raw.crosstalkTdc3Ch0BinPosDeltaQ6Msb << 1) | raw.crosstalkTdc3Ch0BinPosDeltaQ6Lsb,
            raw.crosstalkTdc3Ch1BinPosDeltaQ6,
            raw.crosstalkTdc4Ch0BinPosDeltaQ6,
            (raw.crosstalkTdc4Ch1BinPosDeltaQ6Msb << 6) | raw.crosstalkTdc4Ch1BinPosDeltaQ6Lsb,
        ]
        for i, delta_xtalk in enumerate(delta_xtalks):
            delta_xtalk = delta_xtalk*2**-6 if (delta_xtalk < 2**8) else (delta_xtalk - 2**9)*2**-6 # Q3.6
            delta_xtalks[i] = delta_xtalk + xtalk0
        res["crosstalkBinPos"] = delta_xtalks
        return res

    @staticmethod
    def factoryCalibPackFromDict(data: dict) ->tmf8806FactoryCalibData:
        """Convert a parsed factory calibration to raw factory calibration data.

        Args:
            data (dict): The parsed factory calibration

        Returns:
            tmf8806FactoryCalibData: The raw factory calibration data.
        """
        raw = tmf8806FactoryCalibData()
        raw.id = data["id"]
        raw.crosstalkIntensity = data["crosstalkIntensity"]
        raw.opticalOffsetQ3 = data["opticalOffsetQ3"]
        delta_xtalks = dict(data["crosstalkBinPos"]) # copy to manipulate in place.
        xtalk0 = delta_xtalks[0]
        delta_xtalks[0]  = round(xtalk0 * 2**6) if (xtalk0 >= 0) else round(2**12 + xtalk0*2**6) # Q6.6
        for delta_xtalk in delta_xtalks[1:]:
            delta_xtalk -= xtalk0
            delta_xtalk = round(delta_xtalk * 2**6) if (delta_xtalk >= 0) else round(2**9 + delta_xtalk*2**6) # Q3.6

        raw.crosstalkTdc1Ch0BinPosUQ6Lsb = delta_xtalks[0] & ((1<<8)-1) # 8 bit
        raw.crosstalkTdc1Ch0BinPosUQ6Msb = delta_xtalks[0] >> 8 # 4 bit
        raw.crosstalkTdc1Ch1BinPosDeltaQ6 = delta_xtalks[1]
        raw.crosstalkTdc2Ch0BinPosDeltaQ6 = delta_xtalks[2]
        raw.crosstalkTdc2Ch1BinPosDeltaQ6 = delta_xtalks[3]
        raw.crosstalkTdc3Ch0BinPosDeltaQ6Lsb = delta_xtalks[4] & ((1<<1)-1) #1 bit
        raw.crosstalkTdc3Ch0BinPosDeltaQ6Msb = delta_xtalks[5] >> 1  #8 bit
        raw.crosstalkTdc4Ch0BinPosDeltaQ6 = delta_xtalks[6]
        raw.crosstalkTdc4Ch1BinPosDeltaQ6Lsb = delta_xtalks[7] & ((1<<6)-1) #6 bit
        raw.crosstalkTdc4Ch1BinPosDeltaQ6Msb = delta_xtalks[7] >> 6 # 3 bit
        return raw

    #------------------------------------------ bootloader below ----------------------------------------------

    @staticmethod
    def _computeBootloaderChecksum(data: List[int]) -> int:
        """Compute the bootloader checksum over an array.

        Args:
            data (List[int]): The array to compute the checksum over
        Returns:
            int: the checksum
        """
        return ( 0xff ^ sum(data) ) & 0xff


    @staticmethod
    def _appendChecksumToFrame(frame: List[int]) -> None:
        """Append a checksum it to the I2C frame.

        Args:
            frame (List[int]): The I2C command frame.
        """
        #The frame checksum is computed over all but the register byte
        checksum = Tmf8x0xApp._computeBootloaderChecksum(frame[1:])
        frame.append(checksum)


    def _bootloaderSendCommand(self, cmd:int, payload:List[int] = [], response_payload_len: int = 0, timeout:float=0.02):
        """Send a command with payload, and read back response_payload_len bytes.
           Args:
                cmd : The bootloader command byte
                payload (List[int]): The payload data for the command. (not including length and checksum)
        """

        # The write frame consists of a command register address, command, payload len, payload, and crc
        write_frame = [self.TMF8X0X_COM_CMD_STAT, cmd, len(payload)] + payload
        # The read frame is the command register address
        read_frame = [self.TMF8X0X_COM_CMD_STAT]
        self._appendChecksumToFrame(write_frame)
        self.com.i2cTx(self.I2C_SLAVE_ADDR, write_frame)

        max_time = time.time() + timeout
        while True:
            # read back status + payload_len + payload + crc
            response = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, read_frame, 3 + response_payload_len)
            if len(response) != self.TMF8X0X_COM_CMD_STAT__bl_header + response_payload_len:
                self._setError("The application did not accept frame {}. Response is {}.".format(write_frame, response))
                return self.Status.APP_ERROR, []
            if response[0] != cmd:
                #response is ready, check if the frame is okay.
                cmd_status = response[0]
                actual_payload_len = response[1]
                payload = response[1:-1]
                checksum = response[-1]

                # Collect errors, and report at once.
                error = ""
                if cmd_status != self.TMF8X0X_COM_CMD_STAT__stat_ok:
                    error += "The bootloader returned cmd_status {}.".format(cmd_status)
                if actual_payload_len != response_payload_len:
                    error += "The bootloader payload response length should be {}, is {}.".format(actual_payload_len, response_payload_len)
                if self._computeBootloaderChecksum(payload) != checksum:
                    error += "The checksum {} does not match to the frame content.".format(checksum)

                if error:
                    self._setError("{}\n Write Frame: {}, Read Frame: {}, Response {}.".format(error, write_frame, read_frame, response))
                    return self.Status.APP_ERROR, bytearray()
                else:
                    #every check passed, return payload data.
                    return self.Status.OK, payload
            if ( time.time() > max_time):
                break
        #Timed out
        self._setError("The bootloader frame {} timed out after {}s.".format(write_frame, timeout))
        return self.Status.TIMEOUT_ERROR, []


    def _bootLoaderDownloadData(self, target_address: int, data: bytearray,  timeout: float = 0.02) -> Tmf8x0xDevice.Status:
        """Load a data chunk to the target at a specific address.

        Args:
            target_address (int): The address on the target.
            data (bytearray): The data to be written onto the target.
            timeout: abort if command is not executed successfully within this timeframe
        Returns:
            Status: The status code (OK = 0, error != 0).
        """
        # 16-bit RAM address in little endian format
        target_address_bytes = [target_address & 0xff, (target_address >> 8) & 0xff]
        #First, send the target RAM address (little endian)
        status, _ = self._bootloaderSendCommand(self.TMF8X0X_COM_CMD_STAT__bl_cmd_addr_ram, target_address_bytes, 0, timeout)
        if status != self.Status.OK:
            self._setError("Setting RAM address {} failed.".format(target_address))
            return status

        #Set the maximum chunk size that can be transferred at once.
        max_chunk_len = self.TMF8X0X_BL_MAX_DATA_SIZE
        # Split the big bytearray into smaller chunks that can be transferred with single I2C bulk writes.
        for data_idx in range(0,len(data), max_chunk_len):
            payload_data = data[data_idx: data_idx + max_chunk_len]
            self._log("Loading address 0x{:x} chunk with {} bytes.".format(target_address + data_idx, len(payload_data)))
            # Write the payload of one chunk
            status, _ = self._bootloaderSendCommand(self.TMF8X0X_COM_CMD_STAT__bl_cmd_w_ram, list(payload_data), 0, timeout)
            if status != self.Status.OK:
                self._setError("Writing RAM chunk {} failed.".format(payload_data))
                return status
        return self.Status.OK
    
    def uploadInitForEncryptedDevices( self, timeout:float = 0.020 ) ->Tmf8x0xDevice.Status:
        # Write the download init command, has a single parameter the Seed = 0x29
        status, _ = self._bootloaderSendCommand(self.TMF8X0X_COM_CMD_STAT__bl_cmd_upload_init,[0x29], 0, timeout)
        if status != self.Status.OK:
            self._setError("UploadInit failed.")
            return status
        return self.Status.OK
        
        
    def downloadHexFile(self, hex_file: str = DEFAULT_PATCH_FILE_UNENCRYPTED, timeout:float = 0.020) ->Tmf8x0xDevice.Status:
        """Download a application/patch hex file to the device.
           To run the application, call

        Args:
            hex_file (str): The firmware/patch to load. Defaults to the encrypted patch file.
            timeout (float, optional): The timeout for the device to respond on a command. Defaults to 20ms.

        Returns:
            Status: The status code (OK = 0, error != 0).
        """
        segments = []
        try:
            intel_hex = IntelHex()
            intel_hex.fromfile(hex_file, format='hex')
            # Load the segments.
            segments = intel_hex.segments()
            if len(segments) != 1:
                self._log("Warning - Expecting only 1 segment, but found {}".format(len(segments)))
        except Exception as e:
            self._setError("Error with hex file {}: {}".format(hex_file, str(e)))
            return self.Status.OTHER_ERROR

        for start_segment, end_segment in segments:
            self._log("Loading SYS image segment start: {:x}, end: {:x}".format(start_segment, end_segment))
            status = self._bootLoaderDownloadData(start_segment, intel_hex.tobinarray(start= start_segment, size= end_segment - start_segment), timeout=timeout)
            if status != self.Status.OK:
                return status

        return self.Status.OK


    def startRamApp(self, timeout: float = 20e-3) -> Tmf8x0xDevice.Status:
        """Start the RAM application from the bootloader.

        Args:
            timeout (float, optional): The communication timeout. Defaults to 20e-3.

        Returns:
            Status: The status code (OK = 0, error != 0).
        """
        ram_remap_cmd = [self.TMF8X0X_COM_CMD_STAT, self.TMF8X0X_COM_CMD_STAT__bl_cmd_remap_reset, 0x00]
        self._appendChecksumToFrame(ram_remap_cmd)
        self.com.i2cTx(self.I2C_SLAVE_ADDR, ram_remap_cmd)

        max_time = time.time() + timeout
        while True:
            if self.isAppRunning() == True:
                return self.Status.OK
            if time.time() > max_time:
                self._setError("The application did not start within {} seconds".format(timeout))
                return self.Status.TIMEOUT_ERROR

    def startRomApp(self, timeout= 20e-3) -> Tmf8x0xDevice.Status:
        """Start the ROM application from the bootloader.

        Args:
            timeout (float, optional): The communication timeout. Defaults to 20ms.

        Returns:
            Status: The status code (OK = 0, error != 0).
        """
        self.com.i2cTx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_COM_REQ_APP_ID, self.TMF8X0X_COM_APP_ID__application])
        max_time = time.time() + timeout
        while not self.isAppRunning():
            if time.time() > max_time: 
                self._setError("The application did not start within {} seconds".format(timeout))
                return self.Status.TIMEOUT_ERROR
        return self.Status.OK

if __name__ == "__main__":
    print("Only for inclusion in example programs. No example code here.")
    quit()

