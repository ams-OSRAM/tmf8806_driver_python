# /*****************************************************************************
# * Copyright (c) [2024] ams-OSRAM AG                                          *
# * All rights are reserved.                                                   *
# *                                                                            *
# * FOR FULL LICENSE TEXT SEE LICENSE.TXT                                      *
# ******************************************************************************/
 

"""
TMF8x0x device support in python: Koloth, Dahar, Leica 
"""
import __init__
import enum
import time
from aos_com.ic_com import IcCom

class Tmf8x0xDevice:
    """The basic Koloth/Dahar/Leica communication class.
       It offers application/bootloader functionality to interact via a FTDI module.
    """
    
    VERSION = 1.1
    """Version log 
    - 1.0 First working version
    - 1.1 after review by M. Pelzmann
        #    """

    class Status(enum.IntEnum):
        """The status return code of a method. either OK (=0), or an error (<>0)"""
        OK = 0 
        """The function executed as expected."""
        DEV_ERROR = -1 
        """The tmf8x0x device had a protocol error (e.g. the device FLASH reported an error over I2C)."""
        APP_ERROR = -2 
        """The tmf8x0x device application had a protocol error (e.g. the device firmware reported an error over I2C)."""
        TIMEOUT_ERROR = -3
        """The tmf8x0x device did not respond in time (e.g. found no SPI device)."""
        UART_ERROR = -4
        """Something went wrong when opening or reading from UART."""
        OTHER_ERROR = -5
        """Something went wrong, but there's no specific error code."""

    I2C_SLAVE_ADDR = 0x41 
    """The default I2C address. Fixed for now, can be changed later. """

    class ExceptionLevel(enum.IntEnum):
        """The exception level that defines until where an error shall throw an exception. """
        OFF = 0
        """Do not throw exceptions."""
        FTDI = 1
        """Throw exceptions on FTDI level (e.g., I2C-TX failed)"""
        DEVICE = 2
        """Throw exceptions on device level (e.g., could not enable device, SPI device not found, UART RX timed out)"""
        APP = 3
        """Throw exceptions on application level (e.g., command timed out, application reported error)"""
    

    # some important registers    
    TMF8X0X_ENABLE = 0xe0
    TMF8X0X_ENABLE__cpu_reset__MASK = 1<<7          # CPU reset register 0x80
    TMF8X0X_ENABLE__cpu_ready__MASK = 1<<6          # CPU ready/busy bit is 0x40
    TMF8X0X_ENABLE__wakeup__MASK    = 1<<0          # is called PON bit on TMF8x0x
    TMF8X0X_ENABLE__app_ready__MASK = (TMF8X0X_ENABLE__cpu_ready__MASK | TMF8X0X_ENABLE__wakeup__MASK)
    
    TMF8X0X_INT_STATUS = 0xe1
    TMF8X0X_INT_ENAB = 0xe2

    def __init__(self, ic_com:IcCom, log = False, exception_level: ExceptionLevel=ExceptionLevel.DEVICE):
        """The default constructor. It initializes the FTDI driver.
        Args:
            log (bool, optional): Enable verbose driver outputs. False per default.
            exception_level (ExceptionLevel, optional): Set the exception level at which an error gets raised an exception. Defaults to ExceptionLevel.DEVICE
        """
        self.com = ic_com 
        self._exception_level = exception_level

    def _setError(self, message):
        """An error occurred - add it to the error list, which the host can later read out.

        Args:
            message (str): The errorr message
        """
        self.com.errors.append(message)
        if self._exception_level == self.ExceptionLevel.DEVICE:
            raise RuntimeError("TMF8x0x Error: ", message)

    def _log(self, message):
        """Log information"""
        self.com._log(message)

    def getAndResetErrors(self):
        """Get a list of all error status flags and messages, and erase the internal error list.

        Returns:
            list({'status':int, 'message':str}): A list of the status values and the corresponding error messages.
            list(): if no error occurred
        """
        errors = self.com.errors
        self.com.errors = list()
        return errors

    def open( self, i2c_speed:int = 1000000 ):
        """
        Open the communication.
        Args:
            i2c_speed (int, optional): Open I2C communication. Defaults to 1000000.
        Returns:
            Status: The status code (OK = 0, error != 0)..
        """
        status = self.com.i2cOpen(i2c_speed=i2c_speed)
        if status == self.com.I2C_OK:
            self.com.gpioSetDirection(self.com.enable_pin, 0)
        return status
    
    def close( self ):
        """
        Closes the communication.
        Args:
            i2c_speed (int, optional): Open I2C communication. Defaults to 1000000.
        Returns:
            Status: The status code (OK = 0, error != 0)..
        """
        return self.com.i2cClose()       

    def pon0(self,timeout:float=0.001) -> Status:
        """
        Move the device into the STANDBY or PON=0 state.
        Args:
            timeout (float, optional): DESCRIPTION. Defaults to 0.001.
        Returns:
            Status: Tmf8x0xDevice.Status.OK if everything is ok
        """
        self.com.i2cTx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_ENABLE, 0x0 ])
        time.sleep(timeout) 
        enable =  self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_ENABLE], 1 )
        if len(enable) < 1 or enable[0] & 0x1 :
            self._setError("The device didn't enter PON=0 (ENABLE register value is: 0x{:2X} expected: 0x00).".format(enable))
            return self.Status.DEV_ERROR
        return self.Status.OK
        
    def pon1(self,timeout:float=0.001) -> Status:
        """
        Move the device from STANDBY or PON=1 (WAKEUP) state.
        Args:
            timeout (float, optional): DESCRIPTION. Defaults to 0.001.
        Returns:
            Status: Tmf8x0xDevice.Status.OK if everything is ok
        """
        self.com.i2cTx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_ENABLE, self.TMF8X0X_ENABLE__wakeup__MASK])
        time.sleep(timeout) 
        _cnt = 2
        while _cnt > 0:
            enable =  self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_ENABLE], 1 )
            if len(enable) < 1 or enable[0] & self.TMF8X0X_ENABLE__app_ready__MASK != self.TMF8X0X_ENABLE__app_ready__MASK:
                if ( len(enable) < 1):
                    enable = [0]
                self._setError("The device didn't come up as expected (ENABLE register value is: 0x{:2X} expected: 0x{:2X}).".format(enable[0], self.TMF8X0X_ENABLE__app_ready__MASK))
                return self.Status.DEV_ERROR
            else:
                return self.Status.OK
            _cnt -= 1
        self._setError("Timeout The device didn't come up as expected (ENABLE register value is: 0x{:2X} expected: 0x{:2X}).".format(enable[0], self.TMF8X0X_ENABLE__app_ready__MASK))
        return self.Status.DEV_ERROR

    def enable(self,timeout:float=0.02) -> Status:
        """Enable the TMF8X0X.
        Args:
            timeout (float, optional): DESCRIPTION. Defaults to 0.02.

        Returns:
            Status: The status code (OK = 0, error != 0)..
        """
        self.com.gpioSet(self.com.enable_pin, self.com.enable_pin) #set Enable pin to output, and INT pin to input.       
        # HW needs to wake up        
        time.sleep(timeout) 
        # now set the PON=1 bit
        return self.pon1()
        
    def disable(self):
        """Disable the TMF8X0"""
        self.com.gpioSet(self.com.enable_pin, 0) 

    def isIntPinPulledLow(self):
        """Check if the interrupt is pending, ie. if the INT pin is pulled low.

        Returns:
            bool: True if an interrupt is pending, False if it isn't 
        """
        level = self.com.gpioGet(self.com.interrupt_pin)
        return level == 0 # Open drain INT pin -> 0 == pending

    def readIntStatus(self) -> int:
        """ read the interrupt status register of TMF8x0x """
        intreg = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_INT_STATUS], 1 )
        if ( len(intreg) ):
            return intreg[0]
        self._setError("Cannot read the INT_STATUS register")
        return 0
 
    def clearIntStatus(self,bitMaskToClear):
        """ clear the interrupt status register of TMF8x0x 
         Args:
            bitMaskToClear: all bits set in this 8-bit mask will be cleared in the interrupt register 
        """
        self.com.i2cTx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_INT_STATUS,bitMaskToClear] )

    def readIntEnable(self) -> int:
        """ read the interrupt enable register of TMF8x0x """
        enabreg = self.com.i2cTxRx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_INT_ENAB], 1 )
        if ( len(enabreg) ):
            return enabreg[0]
        self._setError("Cannot read the INT_STATUS register")
        return 0
    
    def enableInt(self,bitMaskToEnable):
        """ enable all the interrupts that have the bit set in the parameter, all other interrupts will be disabled 
         Args:
            bitMaskToEnable: all bits set in this 8-bit mask will be enabled, all others disabled 
        """
        self.com.i2cTx(self.I2C_SLAVE_ADDR, [self.TMF8X0X_INT_ENAB,bitMaskToEnable] )

    def clearAndEnableInt(self,bitMaskToEnable):
        """
        Clear and enable given interrupt bits
        Args:
            bitMaskToEnable : all bits set in this 8-bit mask will be cleared and enabled, all others disabled
        """
        self.clearIntStatus(bitMaskToEnable)    # first clear any old pending interrupt
        self.enableInt(bitMaskToEnable)         # now clear it
        
    def readAndClearInt(self,bitMaskToCheck):
        """
        Check if given interrupt bits are set, if they are, clear them and return them
        Args:
            bitMaskToCheck (TYPE): bit mask for interrupts to check for
        Returns:
            clr (TYPE): set interrupt bits that also have been cleared
        """
        clr = self.readIntStatus() & bitMaskToCheck
        if ( clr ):
            self.clearIntStatus( clr )
        return clr
    
if __name__ == "__main__":
    ''' Example: Open the communication, enable the device, and start the ROM application.'''
    use_evm =True
    use_ftdi = False
    use_aardvark = False

    if use_evm:
        from aos_com.evm_ftdi import EvmFtdi as Ftdi
        com = Ftdi(log=False, exception_on_error=True)
        i2c_speed = 1000000
    
    if use_ftdi:
        from aos_com.ft2232_ftdi import Ft2232Ftdi
        com = Ft2232Ftdi(log=False)
        i2c_speed = 1000000

    tof = Tmf8x0xDevice(ic_com=com,log=True,exception_level=0)

    print("Open ftdi communication channels")
    tof.open(i2c_speed=i2c_speed)

    print("Connect to TMF8x0x")
    tof.disable()
    time.sleep(0.1) # wait until the device is turned off for sure
    # Toggle the enable pin to ensure the device is rebooted
    print("Enable the device.")
    tof.enable()
    data = tof.com.i2cTxRx(tof.I2C_SLAVE_ADDR, [0x0], 0x10)
    print("Reading 16 registers: {}".format(list(map(hex, data))))

    tof.pon0()
    tof.pon1()
    
    interrupt = tof.readIntStatus()
    tof.clearIntStatus(0x01)    # clear lsb of interrupts
    tof.enableInt(0x0F)         # enable all 4 interrupts
    enabled= tof.readIntEnable() 
    print( "Enabled INTERRUPTS=0x{:x}".format(enabled))
    if ( enabled != 0x0f):
        print("ERROR, not all 4 interrupts are enabled")
    tof.enableInt(0)            # disable all 4 interrupts
    enabled= tof.readIntEnable() 
    print( "Enabled INTERRUPTS=0x{:x}".format(enabled))
    if ( enabled != 0x0):
        print("ERROR, not all 4 interrupts are disabled")

    tof.disable()
    tof.close()
    print( "Good bye")
        