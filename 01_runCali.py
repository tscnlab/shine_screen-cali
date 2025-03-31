import viz
import viztask
import steamvr

import os
import exp

import pandas as pd
import numpy as np
from pyplr import jeti
import luxpy as lx

# PC name: os.environ['COMPUTERNAME']

# ____________
## INPUT

expInfo = {"vr_number": 5,
    "eye": "left",
    "repetitions": 5,
    "intensities": [
        0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1,
    ],
    "gamma_corrected": True,
    "com_port": "COM4"
}

# ____________
## TASK


def runExperiment(expInfo):

    # ___________
    ## HARDWARE and MEDIA

    # disable mouse navigation
    yield viz.mouse.setOverride(viz.ON)

    print("connecting to VR")
    # connect to VivePro
    [hmd, VivePro, eyeTracker] = exp.connectToVive()

    # ___________
    # INITIAL SETUP

    yield viztask.waitTime(0.2)

    # ___________
    # CREATE SCENES

    # VR scene
    print("setting up VR scene")
    expScene = exp.DichopticScene(sceneColour=viz.BLACK)
    yield viztask.waitTime(0.5)

    yield expScene.show()

    # to save data
    data = {
        "repetition": [],
        "input_intensity": [],
        "measurement_time": [],
        "illuminance_lux": [],
        "X": [],
        "Z": [],
        "a_opic_iprgc": [],
        "a_opic_l_cone": [],
        "a_m_cone": [],
        "a_s_cone": [],
        "a_opic_rods": [],
        "spectrum": [],
    }

    # ___________
    # JETI PARAMETERS

    wavelengths = np.arange(380, 781, 1)
    

    # Jeti class
    print("Connecting to JETI")
    spectrometer = jeti.Spectraval(port=expInfo["com_port"])

    # ___________
    # MAIN LOOP
    print("Starting measurements")

    for r in range(1, expInfo["repetitions"] + 1):

        for i in expInfo["intensities"]:

            print(f"repetition {r}, intensity {i}")

            # ___________
            # set condition
            if expInfo["gamma_corrected"]:
                screen_intensity = i ** (1 / 2.225)
            else:
                screen_intensity = i

            expScene.setEyeIntensity(
                eye=expInfo["eye"], intensity=screen_intensity
            )

            yield viztask.waitTime(1)

            # ___________
            # take measurement
            print("Taking measurement...")
            startTime = viz.tick()

            # take measurement
            data_out = yield viztask.waitDirector(spectrometer.measurement)
            spectrum = data_out.returnValue[0]

            measurement_time = viz.tick() - startTime

            print(f"measurement taken in {measurement_time} seconds")

            # ___________
            # spectral calculations
            print("Starting spectral calculations")
            
            # combine with wavelength data
            combined = np.vstack((wavelengths, spectrum))

            # calculate XYZ
            xyz_values = lx.spd_to_xyz(data=combined, relative=False)
            
            print(f"Illuminance is {xyz_values[0][1]} lux")
            
            # calculate alpha-opic
            alpha_opic_EDI = lx.photbiochem.spd_to_aopicEDI(
                sid=combined, sid_units="W/m2"
            )  # 0 = l-cone, 1 = m-cone, 2 = s-cone, 3 = rod, 4 = iprgc
            
            print(f"melanopic EDI: {alpha_opic_EDI[0][4]}")
            
            # ___________
            # save data
            data["repetition"].append(r)
            data["input_intensity"].append(i)
            data["measurement_time"].append(measurement_time)
            data["illuminance_lux"].append(xyz_values[0][1])
            data["X"].append(xyz_values[0][0])
            data["Z"].append(xyz_values[0][2])
            data["a_opic_iprgc"].append(alpha_opic_EDI[0][4])
            data["a_opic_l_cone"].append(alpha_opic_EDI[0][0])
            data["a_m_cone"].append(alpha_opic_EDI[0][1])
            data["a_s_cone"].append(alpha_opic_EDI[0][2])
            data["a_opic_rods"].append(alpha_opic_EDI[0][3])
            data["spectrum"].append(spectrum)
    
    print("Finished measurements")
    
    yield expScene.setToBlack()

    # save to dataframe
    df = pd.DataFrame(data)

    # insert general info
    df.insert(0, "PC_name", os.environ["COMPUTERNAME"])
    df.insert(1, "VR_number", expInfo["vr_number"])
    df.insert(2, "eye", expInfo["eye"])
    df.insert(3, "gamma_correction", expInfo["gamma_corrected"])

    print(df)

    # save file
    dirname = os.path.dirname(__file__)
    fileName = rf"{dirname}/results/illum_{os.environ['COMPUTERNAME']}_{expInfo['vr_number']}_{expInfo['eye']}_{exp.getTimestamp()}"
    df.to_csv(fileName + ".csv", index=False)
    df.to_pickle(fileName + ".pkl")

    # END
    print("File saved")

    # wait
    yield viztask.waitTime(10)

    # close window
    yield viz.quit()


# ___________

##  Open window
viz.setMultiSample(8)
viz.go(viz.STEREO_HORZ | viz.NO_DEFAULT_KEY)

viztask.schedule(runExperiment(expInfo))
