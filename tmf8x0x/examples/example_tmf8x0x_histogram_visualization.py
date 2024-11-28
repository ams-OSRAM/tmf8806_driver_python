# /*****************************************************************************
# * Copyright (c) [2024] ams-OSRAM AG                                          *
# * All rights are reserved.                                                   *
# *                                                                            *
# * FOR FULL LICENSE TEXT SEE LICENSE.TXT                                      *
# ******************************************************************************/
 

''' Example interaction with a TMF8x0x application
- Open the communication
- Enable the device
- Start a measurement
- Get histograms and measurement data
- Stop a measurement
- Disable+close the device
'''

USE_EVM:bool=True

import __init__
if USE_EVM:
    from aos_com.evm_ftdi import EvmFtdi as Ftdi
else:
    from aos_com.ft2232_ftdi import Ft2232Ftdi as Ftdi
from tmf8x0x.tmf8x0x_app import Tmf8x0xApp,HistogramsAndResult
from matplotlib import pyplot as plt

if __name__ == "__main__":
    tof = Tmf8x0xApp(Ftdi(log=False))

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

    plot_name = ["prox"]

    print( "Configure sensor" )
    tof.factoryCalibration()
    calib = tof.readFactoryCalibration()
    tof.disable()
    tof.enableAndStart()
    # warning: EC histograms and optical histograms only come when this is the initial measurement!
    tof.configureHistogramDumping(prox=("prox" in plot_name), distance=("dist" in plot_name), distance_puc=("dist_puc" in plot_name), ec=("ec" in plot_name))

    print("Setup matplotlib")
    plt.ion()
    fig = plt.figure()
    axes= {}
    lines = {}
    info = None
    for i, name in enumerate(plot_name):
        ax = fig.add_subplot(len(plot_name),1,i+1)
        ax.set_title(name, y=0.75, )
        ax.set_xlabel("bins")
        ax.set_ylabel("hits")
        lines[name] = []
        for chIdx in range(5):
            line, = ax.step(range(256), [0]*256, label = "CH#{}".format(chIdx), where = "mid")
            lines[name].append(line)
        ax.set_ylim(0,2**16, auto=True)
        ax.legend()
        axes[name] = ax

    info = fig.text(0.001, 0.01, "[]    0m,  0snr,  0°C", fontsize=14, family='monospace')

    # When the host closes the window, stop the measurement
    stop_measuring = False
    def stopMeasuring(evt):
        global stop_measuring
        stop_measuring = True
        fig.canvas.mpl_connect("close_event", stopMeasuring)

    print( "Start measurements" )
    config = tof.getDefaultConfiguration()
    config.data.algo.distanceMode=0
    config.data.kIters=900
    calib = None
    tof.measure(config= config, calibration= calib)
    while not stop_measuring:
        # read all available histograms and one result frame
        _, hr = tof.readHistogramsAndResult()
        info.set_text("[{:3d}] {:4d}mm, {:2d}snr, {:2d}°C".format(hr.result.resultNum, hr.result.distPeak, hr.result.reliability, hr.result.temperature))
        if hr.histogramsProx:
            for i, hist in enumerate(hr.histogramsProx):
                lines["prox"][i].set_ydata(hist)
                if i == 1:
                    axes["prox"].set_ylim(0, round(max(hist)*1.1, 1000)) # Scale with the reference channel
        if hr.histogramsDist:
            for i, hist in enumerate(hr.histogramsDist):
                lines["dist"][i].set_ydata(hist)
                if i == 1:
                    axes["dist"].set_ylim(0, round(max(hist)*1.1, 1000)) # Scale with the reference channel
        if hr.histogramsDistPuc:
            for i, hist in enumerate(hr.histogramsDistPuc):
                lines["dist_puc"][i].set_ydata(hist[:254])
                if i == 1: 
                    axes["dist_puc"].set_ylim(0, round(max(hist)*1.1, 1000)) # Scale with the reference channel
        if hr.histogramsEc:
            for i, hist in enumerate(hr.histogramsEc):
                lines["ec"][i].set_ydata(hist[:254])
                if i == 1: 
                    axes["ec"].set_ylim(0, round(max(hist)*1.1, 1000)) # Scale with the reference channel
        fig.canvas.draw()
        fig.canvas.flush_events()

    print( "Stop measurements" )
    tof.stop()
    tof.disable()
    tof.close()
    print("End")
