
import viz
import vizact
import viztask
import steamvr

import vizinfo
import vizdlg
import vizinput

import os
import exp

import pandas as pd
from pyplr import jeti

# PC name: os.environ['COMPUTERNAME']
	
#____________
## INPUT
	
expInfo = { "repetitions": 1,
			"intensities": [.1, .3, .5, .7, .9,],
			"eye": "left"}			
#____________
## TASK

def runExperiment(expInfo):
	

	#___________
	## HARDWARE and MEDIA
	
	# disable mouse navigation 
	yield viz.mouse.setOverride(viz.ON)
	
	
	print("connecting to VR")
	# connect to VivePro
	[hmd,VivePro,eyeTracker] = exp.connectToVive()
	
	#___________
	# INITIAL SETUP
	
	yield viztask.waitTime(0.2)

	#___________
	# CREATE SCENES
	
	print("Connecting to JETI")
	# Jeti class
	spectrometer = jeti.Spectraval(port="COM5")
	
	# VR scene 
	print("setting up VR scene")
	expScene = exp.DichopticScene(sceneColour = viz.BLACK)
	yield viztask.waitTime(0.5)
	
	yield expScene.show()
	
	repetitions = []
	intensities = []
	spectra = []
	times = []
	
	#___________
	# MAIN LOOP
	print("starting measurements")
	
	for r in range(1,expInfo["repetitions"]+1):
		
		for i in expInfo["intensities"]:
			
			print(f"repetition {r}, intensity {i}")
			
			# set condition
			expScene.setEyeIntensity(eye=expInfo['eye'],
									intensity=i)
						
			yield viztask.waitTime(1)
			
			startTime = viz.tick()
			
			# take measurement
			
			spectrum = yield viztask.waitDirector(spectrometer.measurement)
			
			measurementTime = viz.tick() - startTime
			
			print(f"measurement ended: {measurementTime} seconds")
			
			# save info
			repetitions.append(r)
			intensities.append(i)
			times.append(measurementTime)
			spectra.append(spectrum.returnValue[0])
	

	yield expScene.setToBlack()
	
	# save to dataframe
	eyeList = [expInfo["eye"]] * len(times)
	pcList = [os.environ['COMPUTERNAME']] * len(times)

	df = pd.DataFrame(list(zip(pcList, eyeList, repetitions, intensities, times, spectra)),
			columns =['pc_name','eye', 'repetition','intensity','measurement_time','spectrum'])
	
	print(df)
	
	
	# save file
	fileName = fr"D:\BinIntMel-Illuminance\results\{os.environ['COMPUTERNAME']}_{expInfo['eye']}_{exp.getTimestamp()}.csv"
	df.to_csv(fileName, index = False)
	
	# END
	
	# wait
	yield viztask.waitTime(10)
	
	# close window
	yield viz.quit()

#___________

## RUN


##  Open window
viz.setMultiSample(8)
viz.go(viz.STEREO_HORZ | viz.NO_DEFAULT_KEY)

viztask.schedule(runExperiment(expInfo))