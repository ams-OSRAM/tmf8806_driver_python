# /*****************************************************************************
# * Copyright (c) [2024] ams-OSRAM AG                                          *
# * All rights are reserved.                                                   *
# *                                                                            *
# * FOR FULL LICENSE TEXT SEE LICENSE.TXT                                      *
# ******************************************************************************/
 

''' Simple examples for the TMF8806 Basic communication.
Example 0: Start ROM Application and read App ID + Serial Number.
Example 1: Measure single-shot without factory calibration
Example 2: Perform Factory Calibration with default configuration
Example 3: Run a 30ms-periodic measurement with calibration data
Example 4: Ultra low power - Turn off the device between measurements
Example 5: Diagnostic - Read out a TDC histogram
'''

# Setup
import time
import __init__
from aos_com.evm_ftdi import EvmFtdi as Ftdi

com = Ftdi(log=False)

try:
    com.i2cOpen()
    com.gpioSetDirection(com.enable_pin, 0)
except:
    print("Could not FTDI connection. Exiting.")
    print("Is the FTDI controller attached?")
    quit()

#  Wrapper functions for the FTDI FT232H I2C&GPIO.
enableHigh = lambda: com.gpioSet(com.enable_pin, com.enable_pin)
enableLow = lambda: com.gpioSet(com.enable_pin, 0)
isIntPinLow = lambda: com.gpioGet(com.interrupt_pin) == 0
i2cTx = lambda a,d: com.i2cTx(a,d)
i2cTxRx = lambda a,d,r: list(com.i2cTxRx(a,d,r))
waitMs = lambda ms: time.sleep(ms * 1e-3)


# Examples
waitMs(100)
print("----------------------------------------------------------------------")
print("Example 0: Start ROM Application and read App ID + Serial Number")
print("----------------------------------------------------------------------")
enableHigh() # Supply the device, and set pin EN=high
waitMs(1.6) # Wait until I2C is ready
while i2cTxRx(0x41, [0xE0], 1) != [0x00]: continue # Wait for bootloader sleep
i2cTx(0x41, [0xE0, 0x01]) # Set PON=1
while i2cTxRx(0x41, [0xE0], 1) != [0x41]: continue # Wait for bootloader ready
i2cTx(0x41, [0x02, 0xC0]) # Start the ROM application
while i2cTxRx(0x41, [0x00], 1) != [0xC0]: continue # Wait for the application
# Read application IDs 
appId = i2cTxRx(0x41, [0x00], 1)
major = i2cTxRx(0x41, [0x01], 1)
minor = i2cTxRx(0x41, [0x12], 1)
patch = i2cTxRx(0x41, [0x13], 1)
# Request the TMF8806 fuse values
i2cTx(0x41, [0x10, 0x47])
while i2cTxRx(0x41, [0x10], 2) != [0x00, 0x47]: continue # Wait for command
serial = i2cTxRx(0x41, [0x28], 4)
print("appid=", appId, "major=", major, "minor=", minor, "patch=", patch)
print("serial=", serial)
enableLow() # Disable the device

waitMs(100)
print("----------------------------------------------------------------------")
print("Example 1: Measure single-shot without factory calibration")
print("----------------------------------------------------------------------")
enableHigh() # Supply the device, and set pin EN=high
waitMs(1.6) # Wait until I2C is ready
while i2cTxRx(0x41, [0xE0], 1) != [0x00]: continue # Wait for bootloader sleep
i2cTx(0x41, [0xE0, 0x01]) # Set PON=1
while i2cTxRx(0x41, [0xE0], 1) != [0x41]: continue # Wait for bootloader ready
i2cTx(0x41, [0x02, 0xC0]) # Start the ROM application
while i2cTxRx(0x41, [0x00], 1) != [0xC0]: continue # Wait for the application
# Start a single shot measurement without factory calibration data
i2cTx(0x41, [0x06, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x06, 0x00, 0x84, 0x03, 0x02])
while i2cTxRx(0x41, [0xE1], 1) != [0x01]: continue # Poll for the interrupt flag
i2cTx(0x41, [0xE1, 0x01]) # Clear the interrupt flag
resultDistance = i2cTxRx(0x41, [0x22], 2) # read the distance
print("The result distance is: ", resultDistance[1] * 256 + resultDistance[0], "mm")
enableLow() # Disable the device

waitMs(100)

print("----------------------------------------------------------------------")
print("Example 2: Perform Factory Calibration with default configuration")
print("----------------------------------------------------------------------")
enableHigh() # Supply the device, and set pin EN=high
waitMs(1.6) # Wait until I2C is ready
while i2cTxRx(0x41, [0xE0], 1) != [0x00]: continue # Wait for bootloader sleep
i2cTx(0x41, [0xE0, 0x01]) # Set PON=1
while i2cTxRx(0x41, [0xE0], 1) != [0x41]: continue # Wait for bootloader ready
i2cTx(0x41, [0x02, 0xC0]) # Start the ROM application
while i2cTxRx(0x41, [0x00], 1) != [0xC0]: continue # Wait for the application
# Start a factory calibration with default settings and 40 Mega iterations
# Ensure no object is close by
i2cTx(0x41, [0x06, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x06, 0x00, 0x00, 0xA0, 0x0A])
while i2cTxRx(0x41, [0xE1], 1) != [0x01]: continue # Poll for the interrupt flag
i2cTx(0x41, [0xE1, 0x01]) # Clear the interrupt flag
frame = i2cTxRx(0x41, [0x1C], 18) # read the factory calibration data
calibData = frame[4:]
print("The factory calibration data is: ", calibData)
print("Store this calibration data on the host non-volatile memory")
enableLow() # Disable the device

waitMs(100)

print("----------------------------------------------------------------------")
print("Example 3: Run a 30ms-periodic measurement with calibration data")
print("----------------------------------------------------------------------")
enableHigh() # Supply the device, and set pin EN=high
waitMs(1.6) # Wait until I2C is ready
while i2cTxRx(0x41, [0xE0], 1) != [0x00]: continue # Wait for bootloader sleep
i2cTx(0x41, [0xE0, 0x01]) # Set PON=1
while i2cTxRx(0x41, [0xE0], 1) != [0x41]: continue # Wait for bootloader ready
i2cTx(0x41, [0x02, 0xC0]) # Start the ROM application
while i2cTxRx(0x41, [0x00], 1) != [0xC0]: continue # Wait for the application
# Enable the INT pin for results
i2cTx(0x41, [0xE2, 0x01])
# Load the factory calibration stored
i2cTx(0x41, [0x20] + calibData)
# Start the continuous measurement with calibration data
i2cTx(0x41, [0x06, 0x00, 0x00, 0x01, 0x02, 0x00, 0x00, 0x06, 0x1e, 0x84, 0x03, 0x02])

# Wait for the next result
while not isIntPinLow(): continue
# Bulk-read the result including state data
result = i2cTxRx(0x41, [0x1C], 34)
print("The result #", result[4], "distance is: ", result[7] * 256 + result[6], "mm")
i2cTx(0x41, [0xE1, 0x01]) # Clear the interrupt flag

# Wait for the next result
while not isIntPinLow(): continue
# Bulk-read the result including state data
result = i2cTxRx(0x41, [0x1C], 34)
print("The result #", result[4], "distance is: ", result[7] * 256 + result[6], "mm")
i2cTx(0x41, [0xE1, 0x01]) # Clear the interrupt flag

# Wait for the next result
while not isIntPinLow(): continue
# Bulk-read the result including state data
result = i2cTxRx(0x41, [0x1C], 34)
print("The result #", result[4], "distance is: ", result[7] * 256 + result[6], "mm")
i2cTx(0x41, [0xE1, 0x01]) # Clear the interrupt flag
# Stop the periodic measurement
i2cTx(0x41, [0x10, 0xFF])
while i2cTxRx(0x41, [0x10], 2) != [0x00, 0xFF]: continue # Wait for command
i2cTx(0x41, [0xE1, 0x01]) # Clear a pending interrupt flag
enableLow() # Disable the device

waitMs(100)

print("----------------------------------------------------------------------")
print("Example 4: Ultra low power - Turn off the device between measurements")
print("----------------------------------------------------------------------")
enableHigh() # Supply the device, and set pin EN=high
waitMs(1.6) # Wait until I2C is ready
while i2cTxRx(0x41, [0xE0], 1) != [0x00]: continue # Wait for bootloader sleep
i2cTx(0x41, [0xE0, 0x01]) # Set PON=1
while i2cTxRx(0x41, [0xE0], 1) != [0x41]: continue # Wait for bootloader ready
i2cTx(0x41, [0x02, 0xC0]) # Start the ROM application
while i2cTxRx(0x41, [0x00], 1) != [0xC0]: continue # Wait for the application
# Enable the INT pin for results
i2cTx(0x41, [0xE2, 0x01])
# Load the factory calibration stored on the host side.
i2cTx(0x41, [0x20] + calibData)
# Start a single shot measurement with 80 kilo iterations + calibration data
i2cTx(0x41, [0x06, 0x00, 0x00, 0x01, 0x02, 0x00, 0x00, 0x06, 0x00, 0x50, 0x00, 0x02])
# Wait for the next result
while not isIntPinLow(): continue
result = i2cTxRx(0x41, [0x1C], 34) # Bulk-read the result including state data
print("The result #0 distance is: ", result[7] * 256 + result[6], "mm")
stateData = result[0x0C:0x18] # Store the 11 Bytes state data on the host
enableLow() # Disable the device

waitMs(500) # The host controller waits on the next measurement

enableHigh() # Supply the device, and set pin EN=high
waitMs(1.6) # Wait until I2C is ready
while i2cTxRx(0x41, [0xE0], 1) != [0x00]: continue # Wait for bootloader sleep
i2cTx(0x41, [0xE0, 0x01]) # Set PON=1
while i2cTxRx(0x41, [0xE0], 1) != [0x41]: continue # Wait for bootloader ready
i2cTx(0x41, [0x02, 0xC0]) # Start the ROM application
while i2cTxRx(0x41, [0x00], 1) != [0xC0]: continue # Wait for the application
# Enable the INT pin for results
i2cTx(0x41, [0xE2, 0x01])
# Load the factory calibration + previous state data
i2cTx(0x41, [0x20] + calibData + stateData)
# Start a single shot measurement with 80 kilo iterations + calibration data
i2cTx(0x41, [0x06, 0x00, 0x00, 0x03, 0x02, 0x00, 0x00, 0x06, 0x00, 0x50, 0x00, 0x02])
# Wait for the next result
while not isIntPinLow(): continue
result = i2cTxRx(0x41, [0x1C], 34) # Bulk-read the result including state data
print("The result #1 distance is: ", result[7] * 256 + result[6], "mm")
stateData = result[0x0C:0x18] # Store the 11 Bytes state data on the host
enableLow() # Disable the device


waitMs(500) # The host controller waits on the next measurement

enableHigh() # Supply the device, and set pin EN=high
waitMs(1.6) # Wait until I2C is ready
while i2cTxRx(0x41, [0xE0], 1) != [0x00]: continue # Wait for bootloader sleep
i2cTx(0x41, [0xE0, 0x01]) # Set PON=1
while i2cTxRx(0x41, [0xE0], 1) != [0x41]: continue # Wait for bootloader ready
i2cTx(0x41, [0x02, 0xC0]) # Start the ROM application
while i2cTxRx(0x41, [0x00], 1) != [0xC0]: continue # Wait for the application
# Enable the INT pin for results
i2cTx(0x41, [0xE2, 0x01])
# Load the factory calibration + previous state data
i2cTx(0x41, [0x20] + calibData + stateData)
# Start a single shot measurement with 80 kilo iterations + calibration data
i2cTx(0x41, [0x06, 0x00, 0x00, 0x03, 0x02, 0x00, 0x00, 0x06, 0x00, 0x50, 0x00, 0x02])
# Wait for the next result
while not isIntPinLow(): continue
result = i2cTxRx(0x41, [0x1C], 34) # Bulk-read the result including state data
print("The result #2 distance is: ", result[7] * 256 + result[6], "mm")
stateData = result[0x0C:0x18] # Store the 11 Bytes state data on the host
enableLow() # Disable the device

waitMs(100)

print("----------------------------------------------------------------------")
print("Example 5: Diagnostic - Read out a TDC histogram")
print("----------------------------------------------------------------------")
enableHigh() # Supply the device, and set pin EN=high
waitMs(1.6) # Wait until I2C is ready
while i2cTxRx(0x41, [0xE0], 1) != [0x00]: continue # Wait for bootloader sleep
i2cTx(0x41, [0xE0, 0x01]) # Set PON=1
while i2cTxRx(0x41, [0xE0], 1) != [0x41]: continue # Wait for bootloader ready
i2cTx(0x41, [0x02, 0xC0]) # Start the ROM application
while i2cTxRx(0x41, [0x00], 1) != [0xC0]: continue # Wait for the application
# Enable the INT pin for results + histograms
i2cTx(0x41, [0xE2, 0x03])
# Configure to dump summed histograms
i2cTx(0x41, [0x0C, 0x00, 0x00, 0x02, 0x00, 0x30])
while i2cTxRx(0x41, [0x10], 2) != [0x00, 0x30]: continue # Wait for command
# Start the continuous measurement without calibration data
i2cTx(0x41, [0x06, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x06, 0x1e, 0x84, 0x03, 0x02])
while i2cTxRx(0x41, [0xE1], 1) != [0x02]: continue # Poll until a histogram is ready
i2cTx(0x41, [0xE1, 0x2]) # Clear the interrupt flag
i2cTx(0x41, [0x10, 0x80]) # Request to read the histogram
while i2cTxRx(0x41, [0x10], 2) != [0x00, 0x80]: continue # Wait for command

# Read the summed histogram parts
histFrame0 = i2cTxRx(0x41, [0x1C],  132) # read the histogram
histFrame1 = i2cTxRx(0x41, [0x1C],  132) # read the histogram

i2cTx(0x41, [0x10, 0x32]) # Continue once the histograms are read
while i2cTxRx(0x41, [0x10], 2) != [0x00, 0x32]: continue # Wait for command

while i2cTxRx(0x41, [0xE1], 1) != [0x01]: continue # Poll until a result is ready
result = i2cTxRx(0x41, [0x1C], 34) # Bulk-read the result including state data
print("The result #0 distance is: ", result[7] * 256 + result[6], "mm")
i2cTx(0x41, [0xE1, 0x1]) # Clear the interrupt flag

rawHistogram = histFrame0[4:] + histFrame1[4:]
scalingFactor = 4 # The scaling factor for summed histograms
histogram = [0]*128
for i in range(128):
    histogram[i] = (rawHistogram[2*i] + rawHistogram[2*i+1]*256)*scalingFactor
print("The histogram is ", histogram)
enableLow() # Disable the device

print("----------------------------------------------------------------------")
print("End")
print("----------------------------------------------------------------------")