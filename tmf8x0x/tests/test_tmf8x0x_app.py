# /*****************************************************************************
# * Copyright (c) [2024] ams-OSRAM AG                                          *
# * All rights are reserved.                                                   *
# *                                                                            *
# * FOR FULL LICENSE TEXT SEE LICENSE.TXT                                      *
# ******************************************************************************/
 

import pytest
import sys
import time
import __init__

from aos_com.evm_ftdi import EvmFtdi as Ftdi
from tmf8x0x.tmf8x0x_app import Tmf8x0xApp
from tmf8x0x.tmf8x0x_app import Tmf8x0xApp
from aos_com.register_io import ctypes2Dict
from tmf8x0x.tmf8x0x_device import Tmf8x0xDevice
from tmf8x0x.auto.tmf8806_regs import tmf8806MeasureCmd,tmf8806FactoryCalibData, TMF880X_APP_VERSION_MAJOR, TMF880X_APP_VERSION_MINOR, TMF880X_APP_VERSION_PATCH
from pprint import pprint
from aos_com.register_io import ctypes2Dict

class TestTmf8x0xApplication:
    com: Ftdi
    tof: Tmf8x0xApp
    calibration: tmf8806FactoryCalibData
    REAL_DISTANCE    = 320 # real distance from sensor to target, MODIFY!
    MINIMUM_DISTANCE = int(REAL_DISTANCE * 0.95) # -5%
    MAXIMUM_DISTANCE = int(REAL_DISTANCE * 1.05) # +5%
    MINIMUM_CONFIDENCE = 5
    MINIMUM_CROSSTALK  = 400
    MAXIMUM_CROSSTALK  = 7000
    PERSISTENCE = 2

    def setup_class(self):
        self.com = Ftdi(log=False)
        self.tof = Tmf8x0xApp(ic_com=self.com,log=True, hex_file=pytest.hex_file)
        assert self.com.I2C_OK == self.tof.open(i2c_speed=1000000)
        self.tof.enableAndStart()
        # run factory calibration only once
        assert self.tof.Status.OK == self.tof.factoryCalibration()
        self.calibration = self.tof.readFactoryCalibration()
        self.tof.disable()

    def teardown_class(self):
        assert self.tof.Status.OK == self.tof.close()
    
    def setup_method(self, method):
        self.tof.enableAndStart()

    def teardown_method(self, method):
        self.tof.disable()
        time.sleep(0.5)

    def _wait_for_INT_pin_low(self,timeout:float=1.0) -> bool:
        
        maxTime = time.time() + timeout
        
        while True:
            if self.tof.isIntPinPulledLow():
                return True
            if ( time.time() > maxTime ):
                return False

    def _run_distance_measurement(self,configuration:tmf8806MeasureCmd,with_calibration:bool=False,number_of_results:int=0,check_INT_pin:bool=False):

        # enable INT0 -> will pull INT pin LOW
        if check_INT_pin:
            self.tof.enableInt(self.tof.TMF8X0X_APP_INTERRUPT_RESULTS)
        
        assert self.calibration is not None, "Factory calibration is None"
        assert self.calibration.id == 2
        
        if with_calibration:
            assert self.tof.Status.OK == self.tof.measure(config=configuration,calibration=self.calibration), "Measurement start failed"
        else:
            assert self.tof.Status.OK == self.tof.measure(config=configuration,calibration=None), "Measurement start failed"

        for _ in range(number_of_results):
            if check_INT_pin:
                assert self._wait_for_INT_pin_low() == True, "INT pin was never LO"
            resultFrame = self.tof.readResultFrameInt()
            assert resultFrame is not None, "Result frame is None"
            if resultFrame is not None:
                if configuration.data.algo.distanceEnabled == 0 and self.MINIMUM_DISTANCE > 200:
                    assert resultFrame.reliability == 0, "Should not see a target"
                    assert resultFrame.distPeak == 0, "Should not see a target"
                elif configuration.data.algo.distanceMode:
                    assert resultFrame.reliability > self.MINIMUM_CONFIDENCE
                    assert resultFrame.distPeak > self.MINIMUM_DISTANCE / 1.03 # extended mode is imprecise
                    assert resultFrame.distPeak < self.MAXIMUM_DISTANCE * 1.03 # extended mode is imprecise
                else:
                    assert resultFrame.reliability > self.MINIMUM_CONFIDENCE
                    assert resultFrame.distPeak > self.MINIMUM_DISTANCE
                    assert resultFrame.distPeak < self.MAXIMUM_DISTANCE
                assert resultFrame.temperature == pytest.approx(28, rel=0, abs = 10)

                xtalk_scaling = min(80, configuration.data.kIters) / 80 # Scale down the crosstalk if the prox histogram has less than 80kiters.
                if configuration.data.data.spadSelect == 1:
                    xtalk_scaling *= 0.4 # 40 best SPADs (out of 80)
                elif configuration.data.data.spadSelect == 2:
                    xtalk_scaling *= 0.20 # 20 best SPADs (out of 80)
                elif configuration.data.data.spadSelect == 3:
                    xtalk_scaling *= 0.01 # attenuated SPADs only (10x and 100x SPADs)
                assert resultFrame.xtalk >= xtalk_scaling *self.MINIMUM_CROSSTALK
                assert resultFrame.xtalk <= xtalk_scaling *self.MAXIMUM_CROSSTALK

                # only check if distance algorithm is enabled (2.5 m mode)
                if ( configuration.data.algo.distanceEnabled > 0 ) and (configuration.data.algo.distanceMode == 0):
                    assert resultFrame.referenceHits > 0
                    assert resultFrame.objectHits > 0    

        assert self.tof.Status.OK == self.tof.stop(), "Did not stop measurement correctly"

    # iterate over periodMs
    @pytest.mark.parametrize("number_of_results",  [1])
    @pytest.mark.parametrize("with_calibration",   [False,True])
    @pytest.mark.parametrize("iterationsK",        [1240])
    @pytest.mark.parametrize("periodMs",           [5, 17, 33, 66, 100, 150, 201 ])
    @pytest.mark.parametrize("vcselClkDiv2",       [0,1])
    @pytest.mark.parametrize("check_INT_pin",      [True,False])
    def test_distance_measurement_period(self,number_of_results:int,with_calibration:bool,iterationsK:int,periodMs:int,vcselClkDiv2:int,check_INT_pin:bool):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = iterationsK
        configuration.data.repetitionPeriodMs = periodMs
        configuration.data.algo.vcselClkDiv2 = vcselClkDiv2
        self._run_distance_measurement(configuration=configuration,with_calibration=with_calibration,number_of_results=number_of_results,check_INT_pin=check_INT_pin)

    @pytest.mark.parametrize("periodMs",           [ 17,33,100,201,0xFE,0xFF ])
    @pytest.mark.parametrize("vcselClkDiv2",       [0,1])
    @pytest.mark.parametrize("measurementTimeS",   [ 5 ])
    def test_distance_measurement_timings(self,periodMs:int,measurementTimeS:float,vcselClkDiv2:int):
        self.tof.enableInt(self.tof.TMF8X0X_APP_INTERRUPT_RESULTS)
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = 1240 if periodMs >= 100 else 80
        configuration.data.repetitionPeriodMs = periodMs
        configuration.data.algo.vcselClkDiv2 = vcselClkDiv2
        assert self.tof.Status.OK == self.tof.measure(config=configuration,calibration=self.calibration), "Measurement start failed"
        out = time.time() + measurementTimeS
        measurementIterations = 0
        while time.time() < out:
            assert self._wait_for_INT_pin_low(timeout=measurementTimeS) == True, "INT pin was never LO"
            resultFrame = self.tof.readResultFrameInt()
            assert resultFrame is not None, "Result frame is None"
            measurementIterations += 1
        if periodMs == 0xFE: # 1 Hz operation
            assert measurementIterations >= 5, "Not enough measurement iterations during measurement time"
            assert measurementIterations <= 6, "Too many measurement iterations during measurement time"
        elif periodMs == 0xFF: # 0.5 Hz operation
            assert measurementIterations >= 3, "Not enough measurement iterations during measurement time"
            assert measurementIterations <= 4, "Too many measurement iterations during measurement time"
        else:
            assert measurementIterations > (measurementTimeS * 1000 / periodMs)*0.9, "Not enough measurement iterations during measurement time"
            assert measurementIterations < (measurementTimeS * 1000 / periodMs)*1.1, "Too many measurement iterations during measurement time"

    # iterate over iterationsK, proximity and distance algorithm enabled
    @pytest.mark.parametrize("number_of_results",  [5])
    @pytest.mark.parametrize("with_calibration",   [False,True])
    @pytest.mark.parametrize("iterationsK",        [4000, 1240, 900, 550, 10])
    @pytest.mark.parametrize("periodMs",           [100])
    @pytest.mark.parametrize("vcselClkDiv2",       [0,1])
    def test_distance_measurement_iterations(self,number_of_results:int,with_calibration:bool,iterationsK:int,periodMs:int,vcselClkDiv2:int):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = iterationsK
        configuration.data.repetitionPeriodMs = periodMs
        configuration.data.algo.vcselClkDiv2 = vcselClkDiv2
        self._run_distance_measurement(configuration=configuration,with_calibration=with_calibration,number_of_results=number_of_results)

    @pytest.mark.parametrize("number_of_results",  [5])
    @pytest.mark.parametrize("with_calibration",   [False,True])
    @pytest.mark.parametrize("iterationsK",        [4000, 1240, 900, 550, 10])
    @pytest.mark.parametrize("periodMs",           [100])
    @pytest.mark.parametrize("algKeepReady",       [0,1])
    def test_distance_measurement_alg_keep_ready(self,number_of_results:int,with_calibration:bool,iterationsK:int,periodMs:int,algKeepReady:int):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = iterationsK
        configuration.data.repetitionPeriodMs = periodMs
        configuration.data.algo.algKeepReady = algKeepReady
        self._run_distance_measurement(configuration=configuration,with_calibration=with_calibration,number_of_results=number_of_results)

    @pytest.mark.parametrize("iterationsK", [ "550,80", "900,550", "1240,900", "4000,1240" ])
    def test_iterations_reference_hits(self,iterationsK:int):
        iterList = iterationsK.split(",")                
        iterationsMeasure = int(iterList[0])
        iterationsRef = int(iterList[1])
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = iterationsRef
        configuration.data.repetitionPeriodMs = 0
        assert self.tof.measure(config=configuration,calibration=None) == self.tof.Status.OK, "Measurement start failed"
        resultFrame = self.tof.readResultFrameInt()
        assert self.tof.stop() == self.tof.Status.OK, "Could not stop measurement"
        compReferenceHits = resultFrame.referenceHits
        configuration.data.kIters = iterationsMeasure
        assert self.tof.measure(config=configuration,calibration=None) == self.tof.Status.OK, "Measurement start failed"
        resultFrame = self.tof.readResultFrameInt()
        assert self.tof.stop() == self.tof.Status.OK, "Could not stop measurement"
        assert resultFrame.referenceHits > compReferenceHits, "Reference hits did not increase with iterations"
    
    def test_20MHz_measurement_timing(self):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = 900
        configuration.data.repetitionPeriodMs = 150
        assert self.tof.measure(config=configuration,calibration=None) == self.tof.Status.OK, "Measurement start failed"
        resultFrame1 = self.tof.readResultFrameInt()
        resultFrame2 = self.tof.readResultFrameInt()
        assert self.tof.stop() == self.tof.Status.OK, "Could not stop measurement"
        assert resultFrame1.sysClock > 0
        assert resultFrame2.sysClock > 0
        timeDifferenceRef = resultFrame2.sysClock - resultFrame1.sysClock
        timeDifferenceRef = timeDifferenceRef if timeDifferenceRef > 0 else timeDifferenceRef + (1 << 24)
        assert self.tof.stop() == self.tof.Status.OK, "Could not stop measurement"
        configuration.data.algo.vcselClkDiv2 = 1
        assert self.tof.measure(config=configuration,calibration=None) == self.tof.Status.OK, "Measurement start failed"
        resultFrame3 = self.tof.readResultFrameInt()
        resultFrame4 = self.tof.readResultFrameInt()
        assert self.tof.stop() == self.tof.Status.OK, "Could not stop measurement"
        assert resultFrame3.sysClock > 0
        assert resultFrame4.sysClock > 0
        timeDifferenceAct = resultFrame4.sysClock - resultFrame3.sysClock
        timeDifferenceAct = timeDifferenceAct if timeDifferenceAct > 0 else timeDifferenceAct + (1 << 24)
        assert timeDifferenceAct > timeDifferenceRef
    
    # set vcselClkDiv2 = 1 to allow VCSEL clock jittering
    @pytest.mark.parametrize("number_of_results",   [5])
    @pytest.mark.parametrize("with_calibration",    [False,True])
    @pytest.mark.parametrize("iterationsK",         [900])
    @pytest.mark.parametrize("periodMs",            [100])
    @pytest.mark.parametrize("vcselClkDiv2",        [1])
    @pytest.mark.parametrize("vcselClkSsAmplitude", [0,1,2,3])
    def test_distance_measurement_20MHz_spread_spectrum(self,number_of_results:int,with_calibration:bool,iterationsK:int,periodMs:int,vcselClkDiv2:int,vcselClkSsAmplitude:int):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = iterationsK
        configuration.data.repetitionPeriodMs = periodMs
        configuration.data.algo.vcselClkDiv2 = vcselClkDiv2
        configuration.data.snr.vcselClkSpreadSpecAmplitude = vcselClkSsAmplitude
        self._run_distance_measurement(configuration=configuration,with_calibration=with_calibration,number_of_results=number_of_results)

    # iterate over spad selection options
    @pytest.mark.parametrize("number_of_results", [5])
    @pytest.mark.parametrize("with_calibration",  [False,True])
    @pytest.mark.parametrize("iterationsK",       [4000, 550, 900])
    @pytest.mark.parametrize("periodMs",          [100])
    @pytest.mark.parametrize("spadSelect",        [0,1,2,3])
    def test_distance_measurement_spad_options(self,number_of_results:int,with_calibration:bool,iterationsK:int,periodMs:int,spadSelect:int):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = iterationsK
        configuration.data.repetitionPeriodMs = periodMs
        configuration.data.data.spadSelect = spadSelect
        self._run_distance_measurement(configuration=configuration,with_calibration=with_calibration,number_of_results=number_of_results)
    
    @pytest.mark.skip("Short range algorithm does not provide object hits. SPAD options for short range algorithms. OBSOLETE")
    def test_SPAD_number_object_hits(self):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = 80
        configuration.data.repetitionPeriodMs = 0
        configuration.data.data.spadSelect = 0 # all SPADs
        assert self.tof.measure(config=configuration,calibration=None) == self.tof.Status.OK, "Measurement start failed"
        resultFrame = self.tof.readResultFrameInt()
        assert self.tof.stop() == self.tof.Status.OK, "Could not stop measurement"
        compObjectHits = resultFrame.objectHits
        configuration.data.data.spadSelect = 2 # 20best SPADs
        assert self.tof.measure(config=configuration,calibration=None) == self.tof.Status.OK, "Measurement start failed"
        resultFrame = self.tof.readResultFrameInt()
        assert self.tof.stop() == self.tof.Status.OK, "Could not stop measurement"
        assert resultFrame.objectHits < compObjectHits, "Object hits did not decrease with number of SPADs"

    # iterate over iterationsK, only proximity algorithm enabled 
    @pytest.mark.parametrize("number_of_results",  [5])
    @pytest.mark.parametrize("with_calibration",   [False,True])
    @pytest.mark.parametrize("iterationsK",        [5,10,80,81,100])
    @pytest.mark.parametrize("periodMs",           [100])
    def test_distance_only_short_range(self,number_of_results:int,with_calibration:bool,iterationsK:int,periodMs:int):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = iterationsK
        configuration.data.repetitionPeriodMs = periodMs
        configuration.data.algo.distanceEnabled = 0
        self._run_distance_measurement(configuration=configuration,with_calibration=with_calibration,number_of_results=number_of_results)

    # iterate over iterationsK, enable 4m mode
    @pytest.mark.parametrize("number_of_results",  [5])
    @pytest.mark.parametrize("with_calibration",   [False,True])
    @pytest.mark.parametrize("iterationsK",        [4000, 550, 900])
    @pytest.mark.parametrize("periodMs",           [100])
    @pytest.mark.parametrize("vcselClkDiv2",       [1])
    def test_distance_measurement_4m_mode(self,number_of_results:int,with_calibration:bool,iterationsK:int,periodMs:int,vcselClkDiv2:int):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = iterationsK
        configuration.data.repetitionPeriodMs = periodMs
        configuration.data.algo.vcselClkDiv2 = vcselClkDiv2
        configuration.data.algo.distanceMode = 1
        self._run_distance_measurement(configuration=configuration,with_calibration=with_calibration,number_of_results=number_of_results)

    # iterate over iterationsK, enable 10m mode
    @pytest.mark.parametrize("number_of_results",  [5])
    @pytest.mark.parametrize("with_calibration",   [False,True])
    @pytest.mark.parametrize("iterationsK",        [4000, 550, 900])
    @pytest.mark.parametrize("periodMs",           [100])
    @pytest.mark.parametrize("vcselClkDiv2",       [1])
    def test_distance_measurement_10m_mode(self,number_of_results:int,with_calibration:bool,iterationsK:int,periodMs:int,vcselClkDiv2:int):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = iterationsK
        configuration.data.repetitionPeriodMs = periodMs
        configuration.data.algo.vcselClkDiv2 = vcselClkDiv2
        configuration.data.algo.reserved = 2   # 10m mode selected
        self._run_distance_measurement(configuration=configuration,with_calibration=with_calibration,number_of_results=number_of_results)

    def test_4m_mode_reference_peak_location(self):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = 550
        configuration.data.repetitionPeriodMs = 0
        assert self.tof.configureHistogramDumping(distance=True) == self.tof.Status.OK
        assert self.tof.measure(config=configuration,calibration=None) == self.tof.Status.OK, "Measurement start failed"
        status, hr1 = self.tof.readHistogramsAndResult()
        assert status == self.tof.Status.OK
        assert self.tof.stop() == self.tof.Status.OK, "Could not stop measurement"
        configuration.data.algo.vcselClkDiv2 = 1
        configuration.data.algo.distanceMode = 1
        assert self.tof.measure(config=configuration,calibration=None) == self.tof.Status.OK, "Measurement start failed"
        status, hr2 = self.tof.readHistogramsAndResult()
        assert status == self.tof.Status.OK
        assert self.tof.stop() == self.tof.Status.OK, "Could not stop measurement"        
        refHistogram1 = hr1.histogramsDist[0][0:127] # check channel 0
        refPeakPosition1 = refHistogram1.index(max(refHistogram1))
        refHistogram2 = hr2.histogramsDist[0][0:127] # check channel 0
        refPeakPosition2 = refHistogram2.index(max(refHistogram2))
        assert refPeakPosition1 > refPeakPosition2
    
    # iterate over SPAD dead time
    @pytest.mark.parametrize("number_of_results",  [5])
    @pytest.mark.parametrize("with_calibration",   [False,True])
    @pytest.mark.parametrize("iterationsK",        [4000, 550, 900])
    @pytest.mark.parametrize("periodMs",           [100])
    @pytest.mark.parametrize("spadDeadTime",       [0,1,2,3,4,5,6,7])
    def test_distance_measurement_SPAD_dead_time(self,number_of_results:int,with_calibration:bool,iterationsK:int,periodMs:int,spadDeadTime:int):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = iterationsK
        configuration.data.repetitionPeriodMs = periodMs
        configuration.data.data.spadDeadTime = spadDeadTime
        self._run_distance_measurement(configuration=configuration,with_calibration=with_calibration,number_of_results=number_of_results)

    @pytest.mark.skip("No stable test found yet.")
    def test_SPAD_dead_time_object_hits(self):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.kIters = 4000
        configuration.data.repetitionPeriodMs = 0
        configuration.data.data.spadDeadTime = 0
        assert self.tof.measure(config=configuration,calibration=None) == self.tof.Status.OK, "Measurement start failed"
        resultFrame = self.tof.readResultFrameInt()
        assert self.tof.stop() == self.tof.Status.OK, "Could not stop measurement"
        compObjectHits = resultFrame.objectHits
        configuration.data.data.spadDeadTime = 7
        assert self.tof.measure(config=configuration,calibration=None) == self.tof.Status.OK, "Measurement start failed"
        resultFrame = self.tof.readResultFrameInt()
        assert self.tof.stop() == self.tof.Status.OK, "Could not stop measurement"
        assert resultFrame.objectHits > compObjectHits
    
    @pytest.mark.parametrize("persistence",        [0,1,2,3,4,128,255])
    @pytest.mark.parametrize("low_threshold",      [0,250,10000,65535])
    @pytest.mark.parametrize("high_threshold",     [0,250,10000,65535])
    def test_thresholds(self,persistence:int,low_threshold:int,high_threshold:int):
        assert self.tof.Status.OK == self.tof.setThresholds(persistence=persistence,low_threshold=low_threshold,high_threshold=high_threshold), "Could not set thresholds"
        self._check_information()
        pers, low, high = self.tof.getThresholds()
        self._check_information()
        assert pers == persistence, "Persistence does not match"
        assert low == low_threshold, "Lower threshold does not match"
        assert high == high_threshold, "Higher threshold does not match"        

    @pytest.mark.parametrize("number_of_results", [1])
    def test_thresholds_measure(self, number_of_results:int):
        # positive test, expect sensor to deliver result, target within thresholds
        configuration = self.tof.getDefaultConfiguration()
        assert self.tof.Status.OK == self.tof.setThresholds(persistence=self.PERSISTENCE,low_threshold=self.MINIMUM_DISTANCE,high_threshold=self.MAXIMUM_DISTANCE), "Could not set thresholds"
        self._run_distance_measurement(configuration=configuration,with_calibration=True,number_of_results=number_of_results)
        # negative test, expect sensor to not deliver results, target not within thresholds
        self.tof.enableInt(self.tof.TMF8X0X_APP_INTERRUPT_RESULTS)
        assert self.tof.Status.OK == self.tof.setThresholds(persistence=self.PERSISTENCE,low_threshold=self.MAXIMUM_DISTANCE*2,high_threshold=self.MAXIMUM_DISTANCE*3), "Could not set thresholds"
        assert self.tof.Status.OK == self.tof.measure(config=configuration,calibration=self.calibration), "Could not start measurement"
        assert False == self._wait_for_INT_pin_low(), "Unexpected interrupt occured"
        assert self.tof.Status.OK == self.tof.stop(), "Could not stop measurements"

    @pytest.mark.parametrize("ec", [False,True])
    @pytest.mark.parametrize("prox", [False,True])
    @pytest.mark.parametrize("distance", [False,True])
    @pytest.mark.parametrize("distance_puc", [False,True])
    @pytest.mark.parametrize("summed", [False,True])
    def test_histogram_retrieval(self,ec:bool, prox:bool, distance:bool, distance_puc:bool, summed:bool):
        # def configureHistogramDumping(self, ec:bool=False, prox:bool=False, distance:bool=False, optical:bool=False, distance_puc:bool=False, summed:bool=False,  timeout:float=0.01)->Tmf8x0xDevice.Status:
        configuration = self.tof.getDefaultConfiguration()
        assert self.tof.Status.OK == self.tof.configureHistogramDumping(ec=ec,prox=prox,distance=distance,distance_puc=distance_puc,summed=summed), "Could not configure histogram dumping"
        self._check_information()
        assert self.tof.Status.OK == self.tof.measure(config=configuration), "Could not start measurements"
        status, hr = self.tof.readHistogramsAndResult()
        self._check_information()
        assert self.tof.Status.OK == status, "Could not retrieve histograms and result"
        if ec:
            assert len(hr.histogramsEc) == 5, "Could not retrieve electrical calibration histograms"
        if prox:
            assert len(hr.histogramsProx) == 5, "Could not retrieve proximity histograms"
        if distance:
            assert len(hr.histogramsDist) == 5, "Could not retrieve distance histograms"
        if distance_puc:
            assert len(hr.histogramsDistPuc) == 4, "Could not retrieve distance histograms (PUC)"
        if summed:
            assert len(hr.histogramSum) > 0, "Could not retrieve summed histogram"
        assert self.tof.Status.OK == self.tof.stop()

    def test_read_serial_number(self):
        status, serial_number = self.tof.readSerialNumber()
        assert self.tof.Status.OK == status, "Could not read serial number"
        assert serial_number[0] >= 0, "Serial number 0 not correct"
        assert serial_number[1] >= 0, "Serial number 1 not correct"
        assert serial_number[2] >= 0, "Identification 0 number not correct"
        assert serial_number[3] >= 0, "Identification 1 number not correct"
        self._check_information()

    @pytest.mark.parametrize("number_of_results",   [1])
    @pytest.mark.parametrize("config",    [0,1,2])
    @pytest.mark.parametrize("amplitude",  [0,1,15])
    def test_distance_measurement_charge_pump_spread_spectrum(self,number_of_results:int,config:int,amplitude:int):
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.spreadSpecSpadChp.config = config
        configuration.data.spreadSpecVcselChp.config = config
        configuration.data.spreadSpecSpadChp.amplitude = amplitude
        configuration.data.spreadSpecVcselChp.amplitude = amplitude
        self._run_distance_measurement(configuration=configuration,with_calibration=False,number_of_results=number_of_results)

    @pytest.mark.parametrize("number_of_results",   [5])
    @pytest.mark.parametrize("periodMs",           [100])
    def test_cpu_ready(self, number_of_results:int, periodMs:int):
        status, serial_number = self.tof.readSerialNumber()
        assert self.tof.Status.OK == status, "Could not read serial number"
        assert serial_number[0] >= 0, "Serial number 0 not correct"
        assert serial_number[1] >= 0, "Serial number 1 not correct"
        assert serial_number[2] >= 0, "Identification 0 number not correct"
        assert serial_number[3] >= 0, "Identification 1 number not correct"

        reg = self.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [ self.tof.TMF8X0X_ENABLE ], 1 )
        assert reg[0] == 0x41, " cpu_ready not set"

        self.tof.pon0()
        time.sleep( 0.1 )
        reg = self.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [ self.tof.TMF8X0X_ENABLE ], 1 )
        assert reg[0] == 0x00, " cpu_ready set"

        self.tof.pon1()
        time.sleep( 0.1 )
        reg = self.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [ self.tof.TMF8X0X_ENABLE ], 1 )
        assert reg[0] == 0x41, " cpu_ready not set"
 
        configuration = self.tof.getDefaultConfiguration()
        configuration.data.repetitionPeriodMs = periodMs
        self.tof.enableInt(self.tof.TMF8X0X_APP_INTERRUPT_RESULTS)

        assert self.tof.Status.OK == self.tof.measure(config=configuration), "Measurement start failed"
        for _ in range(number_of_results):
            reg = self.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [ self.tof.TMF8X0X_ENABLE ], 1 )
            assert reg[0] == 0x41, " cpu_ready not set"
            assert self._wait_for_INT_pin_low() == True, "INT pin was never LO"
            resultFrame = self.tof.readResultFrameInt()
            reg = self.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [ self.tof.TMF8X0X_ENABLE ], 1 )
            assert reg[0] == 0x41, " cpu_ready not set"
            assert resultFrame is not None, "Result frame is None"

        assert self.tof.Status.OK == self.tof.stop(), "Did not stop measurement correctly"
        reg = self.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [ self.tof.TMF8X0X_ENABLE ], 1 )
        assert reg[0] == 0x41, " cpu_ready not set"

    def _check_information(self,mode:int=0):
        regs = self.tof.com.i2cTxRx( self.tof.I2C_SLAVE_ADDR, [ 0x00 ], 0x20 )
        assert regs[0x00] == 0xC0 # OL_APPID_OFFSET          
        assert regs[0x01] == TMF880X_APP_VERSION_MAJOR # OL_APPREV_MAJOR_OFFSET
        assert regs[0x12] == TMF880X_APP_VERSION_MINOR # OL_APPREV_MINOR_OFFSET
        # if self.tof.hex_file: # patched
        #    assert regs[0x13] > 0 # OL_APPREV_PATCH_OFFSET
        # else: # ROM code
        #    assert regs[0x13] == 0 # OL_APPREV_PATCH_OFFSET

    
    @pytest.mark.parametrize("with_calibration",   [False,True])
    def test_measure_stop_measure(self, with_calibration: bool):
        config = self.tof.getDefaultConfiguration()
        config.data.repetitionPeriodMs = 1 # as fast as possible
        number_repetitions = 20
        sleep_step_size = 1e-3 # 1ms sleep steps.
        calib = self.calibration if with_calibration else None

        for i in range(number_repetitions):
            self.tof.measure(config, calibration=calib)
            time.sleep(sleep_step_size * i)
            self.tof.stop()
            time.sleep(sleep_step_size * i)
            self.tof.measure(config, calibration=calib)
            
            resultFrame = self.tof.readResultFrameInt()
            assert resultFrame.reliability > self.MINIMUM_CONFIDENCE
            assert resultFrame.distPeak > self.MINIMUM_DISTANCE
            assert resultFrame.distPeak < self.MAXIMUM_DISTANCE
            self.tof.stop()


    def test_app0_information(self):
        # check after start
        self._check_information()
        # check after measurement start
        self.tof.measure(self.tof.getDefaultConfiguration())
        time.sleep(1.0)
        self._check_information()
        # check after STOP
        self.tof.stop()
        self._check_information()
        # check after PON0
        self.tof.pon0()
        time.sleep(1.0)
        self._check_information()
        # check after PON1
        self.tof.pon1()
        time.sleep(1.0)
        self._check_information()
        # check after factory calibration
        self.tof.factoryCalibration()
        self._check_information()

    def test_missingFactoryCalibError(self):
        """Check that the device reports an error if no factory calibration is set."""
        self.tof.measure(self.tof.getDefaultConfiguration(), calibration=None)
        time.sleep(0.5)
        assert self.tof.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [self.tof.TMF8X0X_APP_COM_STATUS], 1)[0] == 0x27
        self.tof.stop()
        time.sleep(0.5)
        assert self.tof.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [self.tof.TMF8X0X_APP_COM_STATUS], 1)[0] == 0x27
        self.tof.stop()
        self.tof.measure(self.tof.getDefaultConfiguration(), calibration=self.calibration)
        time.sleep(0.5)
        assert self.tof.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [self.tof.TMF8X0X_APP_COM_STATUS], 1)[0] != 0x27

    def test_factoryCalibGetsStuck(self):
        """Check that the factory calibration does not get stuck."""
        for i in range(10):
            # Run a short factory calibration enough to check nothing gets stuck.
            assert self.tof.factoryCalibration(kilo_iters=1024) == self.tof.Status.OK
            assert self.tof.readFactoryCalibration()
            self.tof.disable()
            self.tof.enableAndStart()

    def _read_configuration(self)->bytearray:
        return self.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [self.tof.TMF8X0X_APP_CMD_DATA_9], self.tof.TMF8X0X_APP_CMD_STAT - self.tof.TMF8X0X_APP_CMD_DATA_9)

    def test_read_back_configuration(self):
        self.tof.measure(self.tof.getDefaultConfiguration())
        referenceConfig = bytes(self.tof.getDefaultConfiguration())[0:-1]
        numberOfResults = 10
        while numberOfResults > 0:
            if ( self.tof.readAndClearInt(self.tof.TMF8X0X_APP_INTERRUPT_RESULTS) == self.tof.TMF8X0X_APP_INTERRUPT_RESULTS ):
                actualConfig = self._read_configuration()
                assert referenceConfig == actualConfig
                numberOfResults -= 1

    def _goto_sleep_and_wakeup(self):
        self.tof.pon0()
        time.sleep(0.5)
        self.tof.pon1()
        time.sleep(0.5)

    def test_i2c_address_change(self):
        """This test assumes that GPIO0 and GPIO1 have pull-up resistors, like on the TMF8x0x daughter card."""
        defaultAddress = self.tof.I2C_SLAVE_ADDR

        assert self.tof.Status.OK == self.tof.changeI2Caddress(address=defaultAddress+1)        
        self._goto_sleep_and_wakeup()
        assert self.tof.Status.OK == self.tof.changeI2Caddress(address=defaultAddress)
        self._goto_sleep_and_wakeup()
        assert self.tof.Status.OK == self.tof.changeI2Caddress(address=defaultAddress+1,mask=0x3,value=0x3)
        self._goto_sleep_and_wakeup()
        assert self.tof.Status.OK == self.tof.changeI2Caddress(address=defaultAddress)
        self._goto_sleep_and_wakeup()
        assert self.tof.Status.OK == self.tof.changeI2Caddress(address=defaultAddress+1,mask=0x1,value=0x1)
        self._goto_sleep_and_wakeup()
        assert self.tof.Status.OK == self.tof.changeI2Caddress(address=defaultAddress)
        self._goto_sleep_and_wakeup()
        assert self.tof.Status.OK == self.tof.changeI2Caddress(address=defaultAddress+1,mask=0x1,value=0x1)
        self._goto_sleep_and_wakeup()
        assert self.tof.Status.OK == self.tof.changeI2Caddress(address=defaultAddress)
        self._goto_sleep_and_wakeup()

        self.tof._exception_level = self.tof.ExceptionLevel.OFF
        assert self.tof.Status.APP_ERROR == self.tof.changeI2Caddress(address=defaultAddress+1,mask=0x1,value=0x2)
        assert self.tof.Status.APP_ERROR == self.tof.changeI2Caddress(address=defaultAddress+1,mask=0x2,value=0x1)
        assert self.tof.Status.APP_ERROR == self.tof.changeI2Caddress(address=defaultAddress+1,mask=0x3,value=0x1)
        assert self.tof.Status.APP_ERROR == self.tof.changeI2Caddress(address=defaultAddress+1,mask=0x0,value=0x1)

    def test_clock_correction_factor(self):
        """Check target clock by calculation clock correction factors"""
        SAMPLES = 100 # number of clock trim samples
        DISTANCE = 5  # distance between two samples used for clock correction factor calculation

        self.tof.measure(config=self.tof.getDefaultConfiguration())

        tofclocks = []
        hostclocks = []
        factors = []

        for _ in range(SAMPLES):
            tofclocks.append(self.tof.readResultFrameInt().sysClock)
            hostclocks.append(time.time())

        self.tof.stop()

        for sample in range(SAMPLES-DISTANCE):
            # calculate distance correction factor from difference between time base of host and target
            hostTicks   = (hostclocks[sample+DISTANCE] - hostclocks[sample]) * 4_700_000 # The nominal sys-tick clock is 4.7Mhz.
            targetTicks = (tofclocks[sample+DISTANCE] - tofclocks[sample])
            distanceCorrectionFactor = hostTicks / targetTicks
            factors.append(distanceCorrectionFactor)
            assert distanceCorrectionFactor > 0.98
            assert distanceCorrectionFactor < 1.02

        # check correction factor median
        factors.sort()
        assert factors[len(factors)//2] > 0.99
        assert factors[len(factors)//2] < 1.01

    def _get_single_clock_correction_factor(self,wait_time:float=5.0):
        self.tof.measure(config=self.tof.getDefaultConfiguration())
        retries = 3
        for i in range(retries):
            target1 = self.tof.readResultFrameInt().sysClock
            host1 = time.time()
            time.sleep(wait_time)
            target2 = self.tof.readResultFrameInt().sysClock
            host2 = time.time()
            if ((target1 & 0x1) == 0) or ((target2 & 0x1) == 0):
                continue  # one timestamp wasn't valid, retry   
            self.tof.stop()       
            hostTicks   = (host2 - host1) * 4_700_000 # The nominal sys-tick clock is 4.7Mhz.
            targetTicks = (target2 - target1)
            distanceCorrectionFactor = hostTicks / targetTicks
            return distanceCorrectionFactor
        
        assert False, "Didn't get a valid timestamp after 3 retries."

    def _start_retrimming(self):
        REG6 = 0x06
        PASSWD = 0x29

        # write the software password for clock trimming
        self.tof.com.i2cTx(self.tof.I2C_SLAVE_ADDR,[ REG6, PASSWD ])
        # shut down target, open fuses
        assert self.tof.pon0() == self.tof.Status.OK
        time.sleep(0.1)        

    def test_clock_trimming(self):

        FUSE3 = 0x03
        TRIM_STEP = 4
        trim_step_signed = 4

        self.tof.disable()
        self.tof.enableAndStart()

        factorUntrimmed = self._get_single_clock_correction_factor()
        assert factorUntrimmed > 0.98
        assert factorUntrimmed < 1.02

        self._start_retrimming()
        fuse3 = self.tof.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [FUSE3], 1 )[0]

        # check that the trim value will not change sign (int8_t)
        if fuse3 < 0x80:
            trim_step_signed = +TRIM_STEP
        else:
            trim_step_signed = -TRIM_STEP
        assert ((fuse3 + trim_step_signed ) & 0x80 ) == (fuse3 & 0x80 )

        # trim to higher frequency 
        fuse3trimmed = fuse3 + trim_step_signed
        self.tof.com.i2cTx(self.tof.I2C_SLAVE_ADDR,[FUSE3,fuse3trimmed])
        
        # wake up device
        assert self.tof.pon1() == self.tof.Status.OK

        self._start_retrimming()
        fuse3 = self.tof.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [FUSE3], 1 )[0]
        assert fuse3 == fuse3trimmed

        # wake up device
        assert self.tof.pon1() == self.tof.Status.OK

        factorTrimmed = self._get_single_clock_correction_factor()
        if trim_step_signed > 0:
            assert factorUntrimmed > factorTrimmed
        else:
            assert factorUntrimmed < factorTrimmed


    def test_application_switch(self):
        # check if APP0 is running
        appid = self.tof.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [0x00], 1 )[0]
        assert appid == self.tof.TMF8X0X_COM_APP_ID__application
        
        # reset the CPU to re-enter the bootloader
        self.com.i2cTx(self.tof.I2C_SLAVE_ADDR,[self.tof.TMF8X0X_ENABLE, self.tof.TMF8X0X_ENABLE__cpu_reset__MASK])
        time.sleep(0.1)
        
        # check if bootloader is running
        appid = self.tof.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [0x00], 1 )[0]
        assert appid == self.tof.TMF8X0X_COM_APP_ID__bootloader

        # request an application change to App0
        self.com.i2cTx(self.tof.I2C_SLAVE_ADDR,[0x02,0xC0])
        time.sleep(0.3)

        # check if APP0 is running
        appid = self.tof.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [0x00], 1 )[0]
        assert appid == self.tof.TMF8X0X_COM_APP_ID__application

    def test_GpioHighLow(self):
        """Test if a GPIO pin can be low/high/open/drain."""
        config=self.tof.getDefaultConfiguration()
        config.data.kIters = 80 # short iteration
        config.data.repetitionPeriodMs = 0 # single shot
        GPIO0 = 1 << 2
        GPIO1 = 1 << 3
        
        config.data.gpio.gpio0 = 4 # Low
        config.data.gpio.gpio1 = 5 # High
        self.tof.measure(config)
        time.sleep(0.05) # 50ms should be more than enough
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO1
        
        config.data.gpio.gpio0 = 5 # Low
        config.data.gpio.gpio1 = 4 # High
        self.tof.measure(config)
        time.sleep(0.05)
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO0
        
        config.data.gpio.gpio0 = 5 # High
        config.data.gpio.gpio1 = 5 # High
        self.tof.measure(config)
        time.sleep(0.05)
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == (GPIO0 | GPIO1)
        
        config.data.gpio.gpio0 = 4 # Low
        config.data.gpio.gpio1= 4 # Low
        self.tof.measure(config)
        time.sleep(0.05)
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == 0
        
        config.data.gpio.gpio0 = 0 # DISABLED = OPEN
        config.data.gpio.gpio1 = 4 # Low = DRAIN
        self.tof.measure(config)
        time.sleep(0.05)
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO0
        
        config.data.gpio.gpio0 = 4 # Low = DRAIN
        config.data.gpio.gpio1 = 0 # DISABLED = OPEN
        self.tof.measure(config)
        time.sleep(0.05)
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO1

    def test_GpioCommand(self):
        """Test if a GPIO pin can be low/high/open/drain via the GPIO command. 
           NOTE. GPIO0 and GPIO1 have pull-ups -> open = high output"""
        GPIO0 = 1 << 2
        GPIO1 = 1 << 3
        OPEN = 0
        LOW = 4
        HIGH = 5
        assert self.tof.setGPIO(HIGH, LOW) == self.tof.Status.OK
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO0
        assert self.tof.setGPIO(LOW, HIGH) == self.tof.Status.OK
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO1
        assert self.tof.setGPIO(LOW, OPEN) == self.tof.Status.OK
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO1
        assert self.tof.setGPIO(OPEN, LOW) == self.tof.Status.OK
        assert self.tof.com.gpioGet( GPIO1 | GPIO0 ) == GPIO0
        assert self.tof.setGPIO(HIGH, HIGH) == self.tof.Status.OK
        assert self.tof.com.gpioGet( GPIO1 | GPIO0 ) == GPIO0 | GPIO1
        assert self.tof.setGPIO(LOW, LOW) == self.tof.Status.OK
        assert self.tof.com.gpioGet( GPIO1 | GPIO0 ) == 0
        assert self.tof.setGPIO(OPEN, OPEN) == self.tof.Status.OK
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO0 | GPIO1

    def test_GpioObjectPresent(self):
        """Test if a GPIOS are correctly set if an object is present."""
        if not self.tof.hex_file:
            pytest.skip("MAX-134 Only works with ROmv1-Patch")
        config=self.tof.getDefaultConfiguration()
        config.data.kIters = 80 # short iteration
        config.data.repetitionPeriodMs = 1 # As fast as possible
        GPIO0 = 1 << 2
        GPIO1 = 1 << 3
        
        config.data.gpio.gpio0 = 7 # Low
        config.data.gpio.gpio1 = 6 # High
        self.tof.measure(config)
        time.sleep(0.05) # 50ms should be more than enough
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO1
        self.tof.stop()
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO0 # off -> not target
        self.tof.measure(config)
        time.sleep(0.05) # 50ms should be more than enough
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO1
        self.tof.stop()
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO0 # off -> not target

        
        config.data.gpio.gpio0 = 6 # High
        config.data.gpio.gpio1 = 7 # Low
        self.tof.measure(config)
        time.sleep(0.05)
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO0
        self.tof.stop()
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO1
        
        config.data.gpio.gpio0 = 8 # open (with pull-up)
        config.data.gpio.gpio1 = 9 # drain
        self.tof.measure(config)
        time.sleep(0.05)
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == (GPIO0)
        self.tof.stop()
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == (GPIO1)
        

    def test_GpioObjectThreshold(self):
        """Test if a GPIOS are correctly set if an object is present with persistence thresholds."""
        if not self.tof.hex_file:
            pytest.skip("MAX-134 Only works with ROmv1-Patch")
        config=self.tof.getDefaultConfiguration()
        config.data.kIters = 80 # short iteration
        config.data.repetitionPeriodMs = 1 # As fast as possible
        GPIO0 = 1 << 2
        GPIO1 = 1 << 3
        
        config.data.gpio.gpio0 = 7 # Low
        config.data.gpio.gpio1 = 6 # High
        self.tof.setThresholds(1, self.MINIMUM_DISTANCE, self.MAXIMUM_DISTANCE) # in range
        self.tof.measure(config)
        time.sleep(0.05) # 50ms should be more than enough
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO1 # Object found
        time.sleep(0.05) # 50ms should be more than enough
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO1 # Object still found
        self.tof.stop()
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO0 # off
        self.tof.setThresholds(1, self.MAXIMUM_DISTANCE+1, self.MAXIMUM_DISTANCE+100) # Too close
        self.tof.measure(config)
        time.sleep(0.05) 
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO0 # Object too close
        self.tof.stop()
        self.tof.setThresholds(1, self.MINIMUM_DISTANCE-10, self.MINIMUM_DISTANCE-1) # Too far away
        self.tof.measure(config)
        time.sleep(0.05) 
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO0 # Object too far away
        time.sleep(0.05) # 50ms should be more than enough
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO0 # Object still too far away
        self.tof.stop()
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO0 # off 
        self.tof.setThresholds(1, self.MINIMUM_DISTANCE, self.MAXIMUM_DISTANCE) # in range
        self.tof.measure(config)
        time.sleep(0.05) # 50ms should be more than enough
        assert self.tof.com.gpioGet( GPIO0 | GPIO1 ) == GPIO1 # Object found

    def test_application_switch_via_request_register(self):
        """Test for ticket MAX-147, check if the retention bit is correctly reset when switching to the bootloader from APP0"""
        if not self.tof.hex_file:
            pytest.skip("MAX-147 Only works with ROmv1-Patch")
        self.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [ self.tof.TMF8X0X_COM_REQ_APP_ID, self.tof.TMF8X0X_COM_APP_ID__bootloader ], 0 ) # request switch to bootloader
        time.sleep(0.05) # wait 50 milliseconds
        reg = self.com.i2cTxRx(self.tof.I2C_SLAVE_ADDR, [ self.tof.TMF8X0X_COM_APP_ID ], 1 )
        assert reg[0] == self.tof.TMF8X0X_COM_APP_ID__bootloader
        assert self.tof.Status.OK == self.tof.startRamApp()


if __name__ == "__main__":
    # Call pytest here, so we can call it directly.
    sys.exit(pytest.main(["-sv", __file__]))
