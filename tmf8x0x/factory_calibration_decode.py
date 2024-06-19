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
Factory calibration is 14 Bytes:

Byte[0], Byte[1], ... Byte[13]

Revision:               4 bits = Byte[0](3..0)                                  integer
IntensityCrosstalk:     20 bits = Byte[2](7..0) Byte[1](7..0) Byte[0](7..4)     UQ20.0 = integer

Channel0PeakOffset:    12 bits = Byte[4](3..0) Byte[3](7..0)                   UQ6.6 = [ 0 .. 2**6 - 2**(-6) ) == Range is 0 .. 63.9375, step is 2**(-6) = 0.015625

DeltaTdc1Ch1:           9 bits = Byte[5](4..0)  Byte[4](7..4)                   Q3.6 = [ -2**2 .. 2**2 - 2**(-6)] == Range is -4 .. 3.984375 step is 2**(-6) = 0.015625 
DeltaTdc2Ch0:           9 bits = Byte[6](5..0)  Byte[5](7..5) 
DeltaTdc2Ch1:           9 bits = Byte[7](6..0)  Byte[6](7..6) 
DeltaTdc3Ch0:           9 bits = Byte[8](7..0)  Byte[7](7) 
DeltaTdc3Ch1:           9 bits = Byte[10](0)    Byte[9](7..0) 
DeltaTdc4Ch0:           9 bits = Byte[11](1..0) Byte[10](7..1) 
DeltaTdc1Ch1:           9 bits = Byte[12](2..0) Byte[11](7..2) 
SystemOpticalOffset:    8 bits = Byte[13](7..0)                                 

total: 4+20+12+7*9+ 5 (unused) + 8= 112 Bits

"""

def UQnm2Float(value : int, m : int) -> float:
    """Function to convert a UQn.m (unsigned Qn.m) into a float. 
    Number of digits before the decimal point, is don't care.
    Args:
        value: the Qn.m value
        m: number of digits after the decimal point 
    Returns:
        float
    """
    denominator = 1<<m
    f = value / denominator
    return f

def Qnm2Float(value : int, n : int, m : int) -> float:
    """Function to convert a Qn.m into a float
    Args:
        value: the Qn.m value
        n: number of digits before the decimal point, this parameter is needed to find the sign bit
        m: number of digits after the decimal point 
    Returns:
        float
    """
    sign_bit = 1<<(n+m-1)                 # position of sign depends on n and m
    is_negative = bool(value & sign_bit )
    if is_negative:
        mask = sign_bit - 1
        value = ~value 
        value = value & mask
        value += 1                          # 2's complement need to add a 1 after the invert
    f = UQnm2Float(value,m)
    if is_negative:
        f = -f
    return f

def extractData(data : list, bit_index : int, size : int) -> int:
    """Extract from an array of bytes the given number of bits in little endian format
    Args:
        data: list of bytes to decode from
        bit_index: start decoding at this bit-index (constructed of byte-offset*8 + offset into byte
        size: number of bits to decode
    Returns:
        int the decoded value 
    """
    assert [((0<=d and d<256) or (128<=d and d<128)) for d in data], "Error: one or more input values out of range" 
    byte_index = bit_index // 8
    bit_offset = bit_index % 8
    value = 0
    value_offset = 0
    bit_index_end = bit_index + size
    while size:
        assert byte_index < len(data), "Error: not enough bytes in data to decode"
        if size > 8-bit_offset:
            s = 8-bit_offset
        else:
            s = size
        mask = (1<<s)-1
        v = (data[byte_index] >> bit_offset) & mask
        value += (v<<value_offset)
        size -= s
        value_offset += s
        bit_offset += s
        assert bit_offset <=8, "Error: more than 8bit decoded, program error"
        if size and (bit_offset == 8):             # need next byte 
            bit_offset = 0
            byte_index += 1
    return value, bit_index_end 

def factoryCalibrationDecode(data:list):
    """Decode a factory calibration into human readable format 
    Args:
        data: list of integers that represent the 14 bytes factory calibration
    Returns:
        revision, intensity_crosstalk, reference_peak_position, list_of_tdc_peak_positions, system_optical_offset
    """
    assert len(data) >= 14, "Error: need at least 14 bytes for factory calibration decoding"
    data = [int(x) for x in data]       # convert to integer
    index = 0
    revision, index = extractData(data,index,4)
    intensity_crosstalk, index = extractData(data,index,20)
    ref_peak, index = extractData(data,index,12)
    ref_peak_decoded = Qnm2Float(ref_peak,6,6)
    tdc = [ 0 for _ in range(7)]
    tdc_decoded = [ 0 for _ in range(7)]
    for tdc_ch in range(7):
        tdc[tdc_ch], index = extractData(data,index,9)
        tdc_decoded[tdc_ch] = ref_peak_decoded + Qnm2Float(tdc[tdc_ch],3,6)
    _unused, index = extractData(data,index,5)
    system_optical_offset, index = extractData(data,index,4)

    print( "Decoded data {}".format(" ".join(str(x) for x in data)) )
    print( "Revision={}".format(revision))
    print( "IntensityCrosstalk={}".format(intensity_crosstalk))
    print( "TDC-channel{} Absolute pos={} in Q6.6, Absolute position {:f}".format(0, ref_peak, ref_peak_decoded))
    for tdc_ch in range(7):
        print( "TDC-channel{} delta={}, Absolute pos={} in Q3.6, Absolute pos={:f} ".format(1+tdc_ch, tdc[tdc_ch], ref_peak+tdc[tdc_ch], tdc_decoded[tdc_ch]))
    print( "SystemOffset={}".format(system_optical_offset))

    return revision, intensity_crosstalk, ref_peak_decoded, tdc_decoded, system_optical_offset


if __name__ == "__main__":
    i = input("Enter the 14 calibration bytes as decimal seperated with a blank\n")
    data = i.split()
    if len(data) < 14:
        print( "Wrong number of calibration bytes ({} instead of 14). Example:".format(len(data)))
        print( "193 247 0 245 100 192 3 136 9 26 66 164 0 4" )
    else:    
        factoryCalibrationDecode(data)



