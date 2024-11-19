
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
import datetime
import winsound

import viz
import viztask
import vizinput
import cali


##_______________________________

def runSpectralMeasurements():

    ##_______________________________
    # INPUT

    vrHeadsetId = "htc-pe-01"
    
    measurementType = "Radiance"

    eyes = ["left"] #,"left"] # which eyes/display of the vr headset to test

    colours = ["w","r","g","b"] # which colours to test (w - white, r - red, g - green, b - blue)

    steps = np.arange(0.1,1.1,0.1) # steps for the corresponding primaries

    reps = 2 # how many times to repeat each measure


    
    ##_______________________________

    # get RGB list
    [RGBs,colourList] = cali.getRGBs(colours,steps)

     # VR setup
    yield viztask.waitTime(2)
    
    yield viz.mouse.setOverride(viz.ON)
    
    # scene
    scene = cali.MonoScene()

    
    #__
    # for each eye
    for e in eyes:
        
        # WARNING change JETI to correct eye!
        message = '1) Point the JETI to the *' + e + '* eye \n' + \
            '2) Close dialog \n3) Turn monitor off \n4) Press SPACEBAR when ready'
        answer = False
        while answer==False:
            answer = yield vizinput.ask(message,title='Instructions')
            
        
        # Wait for spacebar after monitor turn off
        yield viztask.waitKeyDown(' ')
        
        #__
        # for each rep
        for r in range(0,reps):
            
            # to save results
            d_eye = []
            d_rep = []
            d_colour = []
            d_rgb = []
            d_startTime = []
            d_endTime = []
            d_outcome = []
            
                
            print("_____Repetition " + str(r+1) + "_____")
            
            #__
            # for each rgb value
            for i in range(0,len(colourList)):
                
                rgb = np.asarray(RGBs[i,:],dtype = float)
                
                
                # set scene to rgb
                print(rgb)
                scene.setColour(e, rgb)
                
                yield winsound.Beep(1000,1000)
                print('please take measurement')
                
                start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # wait a few secs
                yield viztask.waitTime(4)
                
                # wait for left or right key
                data = yield viztask.waitKeyDown((viz.KEY_RIGHT,viz.KEY_LEFT))
                
                
                # get results from 
                if data.key == viz.KEY_RIGHT:
                    outcome = 1
                elif data.key == viz.KEY_LEFT:
                    outcome = 0
                
                
                yield winsound.Beep(2000,500)
                yield scene.reset()
                
                # wait a few seconds to ensure clock synchrony
                yield viztask.waitTime(6)


                # save results
                d_eye.append(e)
                d_rep.append(r+1)
                d_colour.append(colourList[i])
                d_rgb.append(rgb)
                d_startTime.append(start_time)
                d_endTime.append(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                d_outcome.append(outcome)
                
                 # reset
                outcome = []
                start_time = []
                

            # export data for this eye & this rep
            df = pd.DataFrame({'Eye': d_eye,
                               'Repetition': d_rep,
                               'Colour': d_colour,
                               'RGB': d_rgb,
                               'Start': d_startTime,
                               'End': d_endTime,
                               'Outcome': d_outcome})
            
            # save
#            df.to_pickle(measurementType + "_" + vrHeadsetId + "_" + e + "Eye_" + 
#            "rep_" + str(r) + str(datetime.date.today()) + '.pkl')
            
            df.to_csv(measurementType + "_" + vrHeadsetId + "_" + e + "Eye_" + 
            "rep_" + str(r+1) + '_' + str(datetime.datetime.now().strftime("%Y-%m-%d_%H.%M")) + '.csv', index = False)
            
        yield winsound.Beep(800,5000)
            
    print('ALL DONE!!')
    
    yield viz.quit()
    
#____________
# RUN

viz.setMultiSample(8)
viz.go(viz.STEREO_HORZ)
[hmd,VivePro] = cali.connectToVive()

viztask.schedule(runSpectralMeasurements())
