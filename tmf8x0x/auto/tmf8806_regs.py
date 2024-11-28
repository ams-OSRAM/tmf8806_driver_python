# generated by 'clang2py'
# flags '-c -v -k=cdefstum -t=arm_none_eabi .\host_interface\tmf8806_regs.h'
# /*****************************************************************************
# * Copyright (c) [2024] ams-OSRAM AG                                          *
# * All rights are reserved.                                                   *
# *                                                                            *
# * FOR FULL LICENSE TEXT SEE LICENSE.TXT                                      *
# ******************************************************************************/


import ctypes
from typing import List


class AsDictMixin:
    @classmethod
    def as_dict(cls, self):
        result = {}
        if not isinstance(self, AsDictMixin):
            # not a structure, assume it's already a python object
            return self
        if not hasattr(cls, "_fields_"):
            return result
        # sys.version_info >= (3, 5)
        # for (field, *_) in cls._fields_:  # noqa
        for field_tuple in cls._fields_:  # noqa
            field = field_tuple[0]
            if field.startswith('PADDING_'):
                continue
            value = getattr(self, field)
            type_ = type(value)
            if hasattr(value, "_length_") and hasattr(value, "_type_"):
                # array
                if not hasattr(type_, "as_dict"):
                    value = [v for v in value]
                else:
                    type_ = type_._type_
                    value = [type_.as_dict(v) for v in value]
            elif hasattr(value, "contents") and hasattr(value, "_type_"):
                # pointer
                try:
                    if not hasattr(type_, "as_dict"):
                        value = value.contents
                    else:
                        type_ = type_._type_
                        value = type_.as_dict(value.contents)
                except ValueError:
                    # nullptr
                    value = None
            elif isinstance(value, AsDictMixin):
                # other structure
                value = type_.as_dict(value)
            result[field] = value
        return result


class Structure(ctypes.Structure, AsDictMixin):

    def __init__(self, *args, **kwds):
        # We don't want to use positional arguments fill PADDING_* fields

        args = dict(zip(self.__class__._field_names_(), args))
        args.update(kwds)
        super(Structure, self).__init__(**args)

    @classmethod
    def _field_names_(cls):
        if hasattr(cls, '_fields_'):
            return (f[0] for f in cls._fields_ if not f[0].startswith('PADDING'))
        else:
            return ()

    @classmethod
    def get_type(cls, field):
        for f in cls._fields_:
            if f[0] == field:
                return f[1]
        return None

    @classmethod
    def bind(cls, bound_fields):
        fields = {}
        for name, type_ in cls._fields_:
            if hasattr(type_, "restype"):
                if name in bound_fields:
                    if bound_fields[name] is None:
                        fields[name] = type_()
                    else:
                        # use a closure to capture the callback from the loop scope
                        fields[name] = (
                            type_((lambda callback: lambda *args: callback(*args))(
                                bound_fields[name]))
                        )
                    del bound_fields[name]
                else:
                    # default callback implementation (does nothing)
                    try:
                        default_ = type_(0).restype().value
                    except TypeError:
                        default_ = None
                    fields[name] = type_((
                        lambda default_: lambda *args: default_)(default_))
            else:
                # not a callback function, use default initialization
                if name in bound_fields:
                    fields[name] = bound_fields[name]
                    del bound_fields[name]
                else:
                    fields[name] = type_()
        if len(bound_fields) != 0:
            raise ValueError(
                "Cannot bind the following unknown callback(s) {}.{}".format(
                    cls.__name__, bound_fields.keys()
            ))
        return cls(**fields)


class Union(ctypes.Union, AsDictMixin):
    pass





TMF8806_REGS_H = True # macro
TMF880X_APP_VERSION_MAJOR = 4 # macro
TMF880X_APP_VERSION_MINOR = 14 # macro
TMF880X_APP_VERSION_PATCH = 0 # macro
TMF8806_TEMP_INVALID = 127 # macro
# A Distance result frame.
class struct__tmf8806DistanceResultFrame(Structure):
    pass

class struct__tmf8806DistanceResultFrame(Structure):
    """ A Distance result frame. """
    def __init__(self, *args):
        self.resultNum: ctypes.c_ubyte
        """ Result number, incremented every time there is a unique answer """
        self.reliability: ctypes.c_ubyte
        """ Reliability of object measurement """
        self.resultStatus: ctypes.c_ubyte
        """ algEnhancedResult == 1: Will indicate the status of the measurement. algEnhancedResult == 0: Will indicate the status of the GPIO interrupt. """
        self.distPeak: ctypes.c_uint16
        """ Distance to the peak of the object """
        self.sysClock: ctypes.c_uint32
        """ System clock/time stamp in units of 0.2us. """
        self.stateData: List[ctypes.c_ubyte]
        """ Packed state data. Host can store this during a sleep, and re-upload it for the next measurement. """
        self.temperature: ctypes.c_byte
        """ The measurement temperature in degree celsius. """
        self.referenceHits: ctypes.c_uint32
        """ Sum of the reference SPADs during the distance measurement. WARNING: Unaligned offset. """
        self.objectHits: ctypes.c_uint32
        """ Sum of the object SPADs during the distance measurement. WARNING: Unaligned offset. """
        self.xtalk: ctypes.c_uint16
        """ The crosstalk peak value. """
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('resultNum', ctypes.c_ubyte),
    ('reliability', ctypes.c_ubyte, 6),
    ('resultStatus', ctypes.c_ubyte, 2),
    ('distPeak', ctypes.c_uint16),
    ('sysClock', ctypes.c_uint32),
    ('stateData', ctypes.c_ubyte * 11),
    ('temperature', ctypes.c_byte),
    ('referenceHits', ctypes.c_uint32),
    ('objectHits', ctypes.c_uint32),
    ('xtalk', ctypes.c_uint16),
     ]

tmf8806DistanceResultFrame = struct__tmf8806DistanceResultFrame
# A result container frame header
class struct__tmf8806ContainerFrameHeader(Structure):
    pass

class struct__tmf8806ContainerFrameHeader(Structure):
    """ A result container frame header """
    def __init__(self, *args):
        self.distanceResultFrameOffset: ctypes.c_uint16
        self.distanceResultFrameSize: ctypes.c_uint16
        """ offset of distance result frame """
        self.electricalCalibrationHistogramOffset: ctypes.c_uint16
        """ size of distance result frame """
        self.electricalCalibrationHistogramSize: ctypes.c_uint16
        """ offset of electrical calibration histograms """
        self.proximityHistogramOffset: ctypes.c_uint16
        """ size of electrical calibration histograms """
        self.proximityHistogramSize: ctypes.c_uint16
        """ offset of proximity histograms """
        self.distanceHistogramOffset: ctypes.c_uint16
        """ size of proximity histograms """
        self.distanceHistogramSize: ctypes.c_uint16
        """ offset of distance histograms """
        self.distanceHistogramPUCOffset: ctypes.c_uint16
        """ size of distance histograms """
        self.distanceHistogramPUCSize: ctypes.c_uint16
        """ offset of distance histograms (pile-up corrected) """
        self.summedHistogramOffset: ctypes.c_uint16
        """ size of distance histograms (pile-up corrected) """
        self.summedHistogramSize: ctypes.c_uint16
        """ offset of summed histogram """
        self.reserved0: ctypes.c_uint32
        """ size of summed histograms """
        self.reserved1: ctypes.c_uint32
        """ reserved """
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('distanceResultFrameOffset', ctypes.c_uint16),
    ('distanceResultFrameSize', ctypes.c_uint16),
    ('electricalCalibrationHistogramOffset', ctypes.c_uint16),
    ('electricalCalibrationHistogramSize', ctypes.c_uint16),
    ('proximityHistogramOffset', ctypes.c_uint16),
    ('proximityHistogramSize', ctypes.c_uint16),
    ('distanceHistogramOffset', ctypes.c_uint16),
    ('distanceHistogramSize', ctypes.c_uint16),
    ('distanceHistogramPUCOffset', ctypes.c_uint16),
    ('distanceHistogramPUCSize', ctypes.c_uint16),
    ('summedHistogramOffset', ctypes.c_uint16),
    ('summedHistogramSize', ctypes.c_uint16),
    ('reserved0', ctypes.c_uint32),
    ('reserved1', ctypes.c_uint32),
     ]

tmf8806ContainerFrameHeader = struct__tmf8806ContainerFrameHeader
# The measure config and command.
class union__tmf8806MeasureCmd(Union):
    pass

class struct__tmf8806MeasureCmdRaw(Structure):
    pass

class struct__tmf8806MeasureCmdRaw(Structure):
    def __init__(self, *args):
        self.cmdData9: ctypes.c_ubyte
        """ **NEW** Command Data 9. """
        self.cmdData8: ctypes.c_ubyte
        """ **NEW** Command Data 8. """
        self.cmdData7: ctypes.c_ubyte
        """ Command Data 7. """
        self.cmdData6: ctypes.c_ubyte
        """ Command Data 6. """
        self.cmdData5: ctypes.c_ubyte
        """ Command Data 5. """
        self.cmdData4: ctypes.c_ubyte
        """ Command Data 4. """
        self.cmdData3: ctypes.c_ubyte
        """ Command Data 3. """
        self.cmdData2: ctypes.c_ubyte
        """ Command Data 2. """
        self.cmdData1: ctypes.c_ubyte
        """ Command Data 1. """
        self.cmdData0: ctypes.c_ubyte
        """ Command Data 0. """
        self.command: ctypes.c_ubyte
        """ The command code. """
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('cmdData9', ctypes.c_ubyte),
    ('cmdData8', ctypes.c_ubyte),
    ('cmdData7', ctypes.c_ubyte),
    ('cmdData6', ctypes.c_ubyte),
    ('cmdData5', ctypes.c_ubyte),
    ('cmdData4', ctypes.c_ubyte),
    ('cmdData3', ctypes.c_ubyte),
    ('cmdData2', ctypes.c_ubyte),
    ('cmdData1', ctypes.c_ubyte),
    ('cmdData0', ctypes.c_ubyte),
    ('command', ctypes.c_ubyte),
     ]

class struct__tmf8806MeasureCmdConfig(Structure):
    pass

# **NEW** Spread spectrum (jitter) of the High Voltage (SPAD) charge pump clock
class struct__tmf8806MeasureCmdSpreadSpectrumSpadChargePump(Structure):
    pass

class struct__tmf8806MeasureCmdSpreadSpectrumSpadChargePump(Structure):
    """ **NEW** Spread spectrum (jitter) of the High Voltage (SPAD) charge pump clock """
    def __init__(self, *args):
        self.amplitude: ctypes.c_ubyte
        """ Amplitude of spread spectrum mode of SPAD high voltage charge pump. 0=disabled, 1..15=amplitude of the jitter (100ps per step). """
        self.config: ctypes.c_ubyte
        """ Configuration of spread spectrum mode of SPAD high voltage charge pump. 0=two-frequency mode, 1=fully random mode, 2=random walk mode, 3=re-use VCSEL charge pump clock (divided by 2). """
        self.reserved: ctypes.c_ubyte
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('amplitude', ctypes.c_ubyte, 4),
    ('config', ctypes.c_ubyte, 2),
    ('reserved', ctypes.c_ubyte, 2),
     ]

# **NEW** Spread spectrum (jitter) of the VCSEL charge pump clock
class struct__tmf8806MeasureCmdSpreadSpectrumVcselChargePump(Structure):
    pass

class struct__tmf8806MeasureCmdSpreadSpectrumVcselChargePump(Structure):
    """ **NEW** Spread spectrum (jitter) of the VCSEL charge pump clock """
    def __init__(self, *args):
        self.amplitude: ctypes.c_ubyte
        """ Amplitude of spread spectrum mode of VCSEL high voltage charge pump. 0=disabled, 1..15=amplitude of the jitter (100ps per step). """
        self.config: ctypes.c_ubyte
        """ Configuration of spread spectrum mode of VCSEL high voltage charge pump. 0=two-frequency mode, 1=fully random mode, 2=random walk mode, 3=reserved. """
        self.singleEdgeMode: ctypes.c_ubyte
        """ If set only randomize the VCSEL charge-pump clock at positive clock edge. """
        self.reserved: ctypes.c_ubyte
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('amplitude', ctypes.c_ubyte, 4),
    ('config', ctypes.c_ubyte, 2),
    ('singleEdgeMode', ctypes.c_ubyte, 1),
    ('reserved', ctypes.c_ubyte, 1),
     ]

class struct__tmf8806MeasureCmdDataSettings(Structure):
    pass

class struct__tmf8806MeasureCmdDataSettings(Structure):
    def __init__(self, *args):
        self.factoryCal: ctypes.c_ubyte
        """ When 1 the data includes factory calibration. """
        self.algState: ctypes.c_ubyte
        """ When 1 the data includes algorithm state """
        self.reserved: ctypes.c_ubyte
        """ **NEW** Deprecated feature. This value must be 0. """
        self.spadDeadTime: ctypes.c_ubyte
        """ **NEW** The SPAD dead time setting. 0=longest, 7=shortest dead time. """
        self.spadSelect: ctypes.c_ubyte
        """ **NEW** Which SPADs to use (less SPADs are better for high crosstalk peak, but worse for SNR). 0=all, 1=40best, 2=20best, 3=attenuated. """
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('factoryCal', ctypes.c_ubyte, 1),
    ('algState', ctypes.c_ubyte, 1),
    ('reserved', ctypes.c_ubyte, 1),
    ('spadDeadTime', ctypes.c_ubyte, 3),
    ('spadSelect', ctypes.c_ubyte, 2),
     ]

class struct__tmf8806MeasureCmdGpioSettings(Structure):
    pass

class struct__tmf8806MeasureCmdGpioSettings(Structure):
    def __init__(self, *args):
        self.gpio0: ctypes.c_ubyte
        """ GPIO0 settings: 0=disable, 1=input low halts measurement, 2=input high halts measurement, 3=output DAX sync, 4= low, 5=high, 6=high while object detected , 7=low while object detected, 8=open while object detected, 9=drain while object detected """
        self.gpio1: ctypes.c_ubyte
        """ GPIO1 settings: 0=disable, 1=input low halts measurement, 2=input high halts measurement, 3=output DAX sync, 4= low, 5=high, 6=high while object detected , 7=low while object detected, 8=open while object detected, 9=drain while object detected """
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('gpio0', ctypes.c_ubyte, 4),
    ('gpio1', ctypes.c_ubyte, 4),
     ]

class struct__tmf8806MeasureCmdAlgoSettings(Structure):
    pass

class struct__tmf8806MeasureCmdAlgoSettings(Structure):
    def __init__(self, *args):
        self.reserved0: ctypes.c_ubyte
        self.distanceEnabled: ctypes.c_ubyte
        """ When 1 distance+prox algorithm are executed (short + long range). When 0, only prox algorithm is executed (short range only). """
        self.vcselClkDiv2: ctypes.c_ubyte
        """ When 1 operates the VCSEL clock at half frequency. 0=37.6MHz, 1=18.8MHz. """
        self.distanceMode: ctypes.c_ubyte
        """ **NEW** When 0 measure up to 2.5m. When 1 measure up to 4m. 4m mode is only activated if the VCSEL clock is configured for 20MHz. Fall back to 2.5m mode if VCSEL clock is 40 MHz. """
        self.immediateInterrupt: ctypes.c_ubyte
        """ When 1 target distance measurement will immediately report to the host an interrupt of the capturing caused by a GPIO event. When 0, will only report to the host when target distance measurement was finished. """
        self.reserved: ctypes.c_ubyte
        """ Was legacy result structure selector. Ignored. """
        self.algKeepReady: ctypes.c_ubyte
        """ When 1 do not go to standby between measurements, and keep charge pump and histogram RAM between measurements """
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('reserved0', ctypes.c_ubyte, 1),
    ('distanceEnabled', ctypes.c_ubyte, 1),
    ('vcselClkDiv2', ctypes.c_ubyte, 1),
    ('distanceMode', ctypes.c_ubyte, 1),
    ('immediateInterrupt', ctypes.c_ubyte, 1),
    ('reserved', ctypes.c_ubyte, 2),
    ('algKeepReady', ctypes.c_ubyte, 1),
     ]

class struct__tmf8806MeasureCmdSnrVcselSpreadSpecSettings(Structure):
    pass

class struct__tmf8806MeasureCmdSnrVcselSpreadSpecSettings(Structure):
    def __init__(self, *args):
        self.threshold: ctypes.c_ubyte
        """ The peak histogram signal-to-noise ratio. If set to 0, use default value (6). """
        self.vcselClkSpreadSpecAmplitude: ctypes.c_ubyte
        """ The VCSEL clock spread spectrum. 0=off, 1..3=Clock jitter settings. Only works if vcselClkDiv2=1. """
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('threshold', ctypes.c_ubyte, 6),
    ('vcselClkSpreadSpecAmplitude', ctypes.c_ubyte, 2),
     ]

class struct__tmf8806MeasureCmdConfig(Structure):
    def __init__(self, *args):
        self.spreadSpecSpadChp: struct__tmf8806MeasureCmdSpreadSpectrumSpadChargePump
        self.spreadSpecVcselChp: struct__tmf8806MeasureCmdSpreadSpectrumVcselChargePump
        self.data: struct__tmf8806MeasureCmdDataSettings
        self.algo: struct__tmf8806MeasureCmdAlgoSettings
        self.gpio: struct__tmf8806MeasureCmdGpioSettings
        self.daxDelay100us: ctypes.c_ubyte
        """ DAX delay, 0 for no delay/signal, otherwise in units of 100uS """
        self.snr: struct__tmf8806MeasureCmdSnrVcselSpreadSpecSettings
        self.repetitionPeriodMs: ctypes.c_ubyte
        """ Measurement period in ms, use 0 for single shot. NOTE: valid values are 0, 5 - 201 """
        self.kIters: ctypes.c_uint16
        """ Integration iteration *1000. If this value is 0xffff, the default number of iterations (1600*1000) is used. """
        self.command: ctypes.c_ubyte
        """ The command code. """
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('spreadSpecSpadChp', struct__tmf8806MeasureCmdSpreadSpectrumSpadChargePump),
    ('spreadSpecVcselChp', struct__tmf8806MeasureCmdSpreadSpectrumVcselChargePump),
    ('data', struct__tmf8806MeasureCmdDataSettings),
    ('algo', struct__tmf8806MeasureCmdAlgoSettings),
    ('gpio', struct__tmf8806MeasureCmdGpioSettings),
    ('daxDelay100us', ctypes.c_ubyte),
    ('snr', struct__tmf8806MeasureCmdSnrVcselSpreadSpecSettings),
    ('repetitionPeriodMs', ctypes.c_ubyte),
    ('kIters', ctypes.c_uint16),
    ('command', ctypes.c_ubyte),
     ]

class union__tmf8806MeasureCmd(Union):
    """ The measure config and command. """
    def __init__(self, *args):
        self.packed: struct__tmf8806MeasureCmdRaw
        self.data: struct__tmf8806MeasureCmdConfig
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('packed', struct__tmf8806MeasureCmdRaw),
    ('data', struct__tmf8806MeasureCmdConfig),
     ]

tmf8806MeasureCmd = union__tmf8806MeasureCmd
# The new state data.
class struct__tmf8806StateData(Structure):
    pass

class struct__tmf8806StateData(Structure):
    """ The new state data. """
    def __init__(self, *args):
        self.id: ctypes.c_ubyte
        """ The state data ID. Must be 0x2, or the state data will be discarded. """
        self.reserved0: ctypes.c_ubyte
        self.breakDownVoltage: ctypes.c_ubyte
        """ The last selected breakdown voltage value. """
        self.avgRefBinPosUQ9: ctypes.c_uint16
        """ The average optical reference bin position in bins (UQ7.9). """
        self.calTemp: ctypes.c_byte
        """ The last BDV calibration temperature in degree C (calibTemp-3 <= currTemp <= calibTemp+3). """
        self.force20MhzVcselTemp: ctypes.c_byte
        """ The temperature at which the measurement needs to run with 20MHz due to a weak VCSEL driver. """
        self.tdcBinCalibrationQ9: List[ctypes.c_byte]
        """ The TDC bin width electrical calibration value in Q9. `binWidth = normWidth * (1 + calibValue)`. -128..75%, 0..0%, 127..24.6%. """
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('id', ctypes.c_ubyte, 4),
    ('reserved0', ctypes.c_ubyte, 4),
    ('breakDownVoltage', ctypes.c_ubyte),
    ('avgRefBinPosUQ9', ctypes.c_uint16),
    ('calTemp', ctypes.c_byte),
    ('force20MhzVcselTemp', ctypes.c_byte),
    ('tdcBinCalibrationQ9', ctypes.c_byte * 5),
     ]

tmf8806StateData = struct__tmf8806StateData
# The factory calibration data for the optical crosstalk.
class struct__tmf8806FactoryCalibData(Structure):
    pass

class struct__tmf8806FactoryCalibData(Structure):
    """ The factory calibration data for the optical crosstalk. """
    def __init__(self, *args):
        self.id: ctypes.c_uint32
        """ The factory data ID. Must be 0x2, or the state data will be discarded. """
        self.crosstalkIntensity: ctypes.c_uint32
        """ The crosstalk intensity value. """
        self.crosstalkTdc1Ch0BinPosUQ6Lsb: ctypes.c_uint32
        """ The first crosstalk bin position as UQ6.6 (lower 8 bits). """
        self.crosstalkTdc1Ch0BinPosUQ6Msb: ctypes.c_uint32
        """ The first crosstalk bin position as UQ6.6 (upper 4 bits). """
        self.crosstalkTdc1Ch1BinPosDeltaQ6: ctypes.c_uint32
        """ The crosstalk bin position delta to bin pos 0 as Q2.6. """
        self.crosstalkTdc2Ch0BinPosDeltaQ6: ctypes.c_uint32
        """ The crosstalk bin position delta to bin pos 0 as Q2.6. """
        self.crosstalkTdc2Ch1BinPosDeltaQ6: ctypes.c_uint32
        """ The crosstalk bin position delta to bin pos 0 as Q2.6. """
        self.crosstalkTdc3Ch0BinPosDeltaQ6Lsb: ctypes.c_uint32
        """ The crosstalk bin position delta to bin pos 0 as Q2.6 (lower 1 bits). """
        self.crosstalkTdc3Ch0BinPosDeltaQ6Msb: ctypes.c_uint32
        """ The crosstalk bin position delta to bin pos 0 as Q2.6 (upper 8 bits). """
        self.crosstalkTdc3Ch1BinPosDeltaQ6: ctypes.c_uint32
        """ The crosstalk bin position delta to bin pos 0 as Q2.6. """
        self.crosstalkTdc4Ch0BinPosDeltaQ6: ctypes.c_uint32
        """ The crosstalk bin position delta to bin pos 0 as Q2.6. """
        self.crosstalkTdc4Ch1BinPosDeltaQ6Lsb: ctypes.c_uint32
        """ The crosstalk bin position delta to bin pos 0 as Q2.6 (lower 6 bits). """
        self.crosstalkTdc4Ch1BinPosDeltaQ6Msb: ctypes.c_ubyte
        """ The crosstalk bin position delta to bin pos 0 as Q2.6 (upper 3 bits). """
        self.reserved: ctypes.c_ubyte
        """ Reserved for future use. """
        self.opticalOffsetQ3: ctypes.c_ubyte
        """ The optical system offset. """
        super().__init__(*args)
    _pack_ = 1
    _fields_ = [
    ('id', ctypes.c_uint32, 4),
    ('crosstalkIntensity', ctypes.c_uint32, 20),
    ('crosstalkTdc1Ch0BinPosUQ6Lsb', ctypes.c_uint32, 8),
    ('crosstalkTdc1Ch0BinPosUQ6Msb', ctypes.c_uint32, 4),
    ('crosstalkTdc1Ch1BinPosDeltaQ6', ctypes.c_uint32, 9),
    ('crosstalkTdc2Ch0BinPosDeltaQ6', ctypes.c_uint32, 9),
    ('crosstalkTdc2Ch1BinPosDeltaQ6', ctypes.c_uint32, 9),
    ('crosstalkTdc3Ch0BinPosDeltaQ6Lsb', ctypes.c_uint32, 1),
    ('crosstalkTdc3Ch0BinPosDeltaQ6Msb', ctypes.c_uint32, 8),
    ('crosstalkTdc3Ch1BinPosDeltaQ6', ctypes.c_uint32, 9),
    ('crosstalkTdc4Ch0BinPosDeltaQ6', ctypes.c_uint32, 9),
    ('crosstalkTdc4Ch1BinPosDeltaQ6Lsb', ctypes.c_uint32, 6),
    ('crosstalkTdc4Ch1BinPosDeltaQ6Msb', ctypes.c_ubyte, 3),
    ('reserved', ctypes.c_ubyte, 5),
    ('opticalOffsetQ3', ctypes.c_ubyte),
     ]

tmf8806FactoryCalibData = struct__tmf8806FactoryCalibData
__all__ = \
    ['TMF8806_REGS_H', 'TMF8806_TEMP_INVALID',
    'TMF880X_APP_VERSION_MAJOR', 'TMF880X_APP_VERSION_MINOR',
    'TMF880X_APP_VERSION_PATCH',
    'struct__tmf8806ContainerFrameHeader',
    'struct__tmf8806DistanceResultFrame',
    'struct__tmf8806FactoryCalibData',
    'struct__tmf8806MeasureCmdAlgoSettings',
    'struct__tmf8806MeasureCmdConfig',
    'struct__tmf8806MeasureCmdDataSettings',
    'struct__tmf8806MeasureCmdGpioSettings',
    'struct__tmf8806MeasureCmdRaw',
    'struct__tmf8806MeasureCmdSnrVcselSpreadSpecSettings',
    'struct__tmf8806MeasureCmdSpreadSpectrumSpadChargePump',
    'struct__tmf8806MeasureCmdSpreadSpectrumVcselChargePump',
    'struct__tmf8806StateData', 'tmf8806ContainerFrameHeader',
    'tmf8806DistanceResultFrame', 'tmf8806FactoryCalibData',
    'tmf8806MeasureCmd', 'tmf8806StateData',
    'union__tmf8806MeasureCmd']
