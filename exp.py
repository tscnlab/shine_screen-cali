
import viz
import vizact
import viztask

import vizinfo
import vizdlg
import vizinput
import steamvr

import pandas as pd
import numpy as np
import pickle
import os
import math
import csv
import datetime
import pathlib
import random
import json
import glob

import pyxid2
import winsound
import wavio




#___________________________________________________
# INITIAL SETUP
#___________________________________________________

def getTimestamp():
	
	return datetime.datetime.now().strftime("%Y%m%dT%H%M%S")


def getMessages(infoDict):
	
	Msg = {}
	
	blockStimulus = infoDict["blockStimulus"]
	blockDuration = infoDict["blockDuration"]
	
	Msg['sessionParams'] = 'Block configuration: ' + str(blockStimulus) + '\n \n' + \
							'Each block lasts:   ' + str(blockDuration) + ' minutes \n \n'
	
	Msg['ready'] = "Press OK when ready to start experiment."

	Msg['block'] = "Press OK when ready to start new block."
	
	return Msg
	
	
	
def loadSounds():
	
	viveHandle = getAudioHandle(keyword = 'vive')
	headphonesHandle = getAudioHandle(keyword = 'realtek')
	
	mainDir = os.getcwd()
	
	soundDict = {}
	
	# ADD HEADPHONES audio
	headphoneDict = {'beep': 'aPvtBeep.wav',
				'aPvtIns': 'instructions_aPVT.wav',
				'endTask': '98_task_completed_01.wav',
				'awakeQuestion': '99_awake_question.wav',
				'keepEyesOpen': 'keepEyesOpen.wav',
				'breakON': '05_break_on_long_08.wav',
				'breakOFF': '08_break_off_01.wav',
				'experimentON': '00_experiment_on_03.wav',
				'experimentOFF': '09_experiment_off_01.wav',
				'salivaON': '01_saliva_on_03.wav',
				'salivaTimer': '01_timer_on_03.wav',
				'salivaLong': '01_saliva_long_03.wav',
				'salivaOFF': '03_saliva_off_02.wav',
				'questionnaireON': '02_questionnaire_on_06.wav',
				'pvtON': '04_pvt_on_04.wav',
				'blockON': '06_block_on_02.wav',
				'vrON': '07_vr_on_05.wav',
				'buttonReminder': '99_button_loop_02.wav'
				}
	
	for key in headphoneDict:
		
		fullPath = os.path.join(mainDir,"resources","audio",headphoneDict[key])
	
		soundDict[key] = viz.addAudio(fullPath, device = headphonesHandle)
		

	# ADD VR AUDIO
	viveDict = {'visPvtIns': 'instructions_visPVT.mp3',
				'visPvtEnd': '98_task_completed_01.wav',
				'vrOFF': '07_vr_off.wav',
				'feedbackBeep': 'feedbackBeep.wav',
				'buttonReminderVR': '99_button_loop_02.wav'
				}
				
	for key in viveDict:
		
		fullPath = os.path.join(mainDir,"resources","audio",viveDict[key])
	
		soundDict[key] =  viz.addAudio(fullPath, device = viveHandle)
	
	
	return soundDict



def playSounds(keyList,soundDict,soundVol = .1, pauseSec=0.1):
	
	if not isinstance(keyList, list):
		keyList = [keyList]
		
	for key in keyList:
		
		soundToPlay = soundDict[key]
		
		soundToPlay.volume(soundVol)
		soundDuration = soundToPlay.getDuration()
		
		yield soundToPlay.play()
		yield viztask.waitTime(soundDuration)
		yield viztask.waitTime(pauseSec)


def soundLoop(soundToPlay, pauseSec=4, soundVol = .1):
	
	soundToPlay.volume(soundVol)
	soundDuration = soundToPlay.getDuration()
	
	while True:

		yield viztask.waitTime(soundDuration+pauseSec)
		yield soundToPlay.play()


def waitKeyReminder(sound, cedrusDevice):
	
	t = viztask.schedule(soundLoop(sound))
	
	yield viztask.waitDirector(waitCedrusKey,cedrusDevice)
	
	yield t.kill()
		
#____________________
# Input participant ID and session number

def provideInfo(inputInfo):
	
	mainDir = os.getcwd()
	
	completedDir =  os.path.join(mainDir,'completed sessions')
		
	
	# Input participant ID
	while not 'participantID' in locals() and not 'sessionNumber' in locals():
		
		participantIDtext = vizinput.input('Participant ID:', title='Please provide...')
		
		try:
			participantID = int(participantIDtext)
		except:
			pass
			
		if 'participantID' in locals():
			
			# non-existent participant ID
			if participantID < 100 or participantID > 325:
				del participantID

			# participant ID used for testing, select experimental condition
			elif participantID >= 100 and participantID < 115:
							
				sessionNumber = 0
				
			# find last session completed
			else:
				
				# get list of completed sessions
				foundSessions = []
				
				for file in os.listdir(completedDir):
					
					if file.endswith('.txt') and file.startswith(str(participantID)):
						
						foundSessions.append(int(file[4]))
						
						# get IDP
						#if IPD == 0:
							
							#with open(os.path.join(completedDir,file)) as f:
								#content = f.readlines()
							
							#try:
								#IPD = float(content[0])
								#print('IPD: ' + str(IPD))
								
							#except:
								#print('Could not read IPD. Contents of file: ' + str(content))
				
				
				# all sessions already completed
				if 4 in foundSessions:
					
					# warning
					vizinput.message("This participant has already completed 4 experimental sessions. " + \
					"Please select a different participant ID or delete the corresponding files in the completed sessions folder.",title='Error')
					
					del participantID
				
				else: 
				
					if not foundSessions:
					
						currentSession = 1
						
						answer = vizinput.ask('This participant has completed no sessions. ' + \
										   'Please confirm that the current session number is:      ' + str(currentSession), title = 'Session number')
						
					else:
						
						currentSession = max(foundSessions) + 1
						
						# confirm current session number
						answer = vizinput.ask('This participant has completed this number of sessions: ' + str(len(foundSessions)) + \
										   '\n Please confirm that the current session number is:      ' + str(currentSession), title = 'Session number')
						
						
					if answer == 0:
							
						sessionNumber = vizinput.choose('Then please choose the correct session number.', \
						[str(n) for n in range(1,5)],title='Session number')
							
						sessionNumber += 1
							
					elif answer == 1:
							
						sessionNumber = currentSession
					

	#_____________________	
	# Get condition code
	
	# database
	dBase = pd.read_csv(os.path.join(mainDir,'resources','ConditionsDatabase_v3.csv'))
	
	rowNumber = dBase.index[dBase['participantID']==participantID]
	
	
	if rowNumber.empty:
		
		testingID = 1
		
		conditionCode = vizinput.choose('This participant ID is for piloting only. Please select experimental condition...',\
		['A: dark','B: constant light','C: in-phase flicker',
		   'D: counter-phase flicker','E: monocular', 'F: monocular-flip'], 
		title='Select experimental condition')
		
		condition = ['dark','constant','in-phase','counter-phase','monocular','monocular-flip'][conditionCode]
		
		if condition in ['in-phase','counter-phase']:
			
			frequencies = list(set(dBase.flickerFrequency))
			freqsStrig = [str(x) + ' Hz' for x in frequencies]
			
			choice = vizinput.choose('Please select the frequency of flicker...', freqsStrig, title='For testing only!')
			
			flickerFrequency = frequencies[choice]
			
			
			waveTypes = list(set(dBase.flickerWaveType))
			choice2 = vizinput.choose('Please select the waveform...', waveTypes, title='For testing only!')
			
			flickerWaveform = waveTypes[choice2]
			
		else:
			flickerFrequency = 0
			flickerWaveform = ''
			
	else:
		
		if sessionNumber==1:
			condition = dBase.loc[rowNumber, 'session1condition'].iloc[0]
			
		elif sessionNumber==2:
			condition = dBase.loc[rowNumber, 'session2condition'].iloc[0]
			
		elif sessionNumber==3:
			condition = dBase.loc[rowNumber, 'session3condition'].iloc[0]
			
		elif sessionNumber==4:
			condition = dBase.loc[rowNumber, 'session4condition'].iloc[0]
				
		
		if condition in ['in-phase','counter-phase']:
			
			flickerFrequency = dBase.loc[rowNumber, 'flickerFrequency'].iloc[0]
			flickerWaveform = dBase.loc[rowNumber, 'flickerWaveType'].iloc[0]
			
		else:
			flickerFrequency = 0
			flickerWaveform = ''
			
	
	# add info to dict
	inputInfo['Participant ID'] = participantID
	inputInfo['Session number'] = sessionNumber
	inputInfo['Experimental condition'] = condition
	inputInfo['Flicker frequency'] = flickerFrequency
	inputInfo['Flicker waveform'] = flickerWaveform
	
	inputInfo["PC-ID"] = os.environ['COMPUTERNAME']
	inputInfo["aPVT-range"] = [1,9]
	inputInfo["visPVT-range"] = [1,10]
	
	
	return inputInfo 




def manageFolders(infoD):
	
	
	participantFolder = os.path.join(os.getcwd(), 'results', str(infoD['Participant ID']) )
	
	# participant folder
	if not os.path.exists(participantFolder):
		os.makedirs(participantFolder)
		
	
	# session folder
	sessionFolder = os.path.join(participantFolder, '{:02}'.format(infoD['Session number']))
	infoD['Results path'] = sessionFolder
	
	
	if not os.path.exists(sessionFolder):
		os.makedirs(sessionFolder)
		os.makedirs(os.path.join(sessionFolder,'aPVT'), exist_ok = True)
		os.makedirs(os.path.join(sessionFolder,'visPVT'), exist_ok = True)
		os.makedirs(os.path.join(sessionFolder,'eyetracking'), exist_ok = True)
		
		infoD['Session Exists'] = False
		
	else: # if folder already exists, check for log file
		metadataFiles = glob.glob(f"{sessionFolder}/00_metadata_*.pkl")
		logFiles = glob.glob(f"{sessionFolder}/00_expLog_*.log")
		
		if logFiles:
				
			with open(metadataFiles[0], 'rb') as f:
				infoD = pickle.load(f)
					
			infoD['Existing log'] = logFiles[0]
			infoD['Session Exists'] = True
			
		elif not logFiles:  # folder was created, but exp did not start
			infoD['Session Exists'] = False

	return infoD


#___________________________________________________
# DATA SAVING
#___________________________________________________



def completedSessionFile(infoD):
	
	fileName = str(infoD['Participant ID']) + '_' + str(infoD['Session number']) + '_' + getTimestamp() + '.txt'

	filePath = os.path.join(os.getcwd(),'completed sessions',fileName)
	
	with open(filePath, 'x') as f:
		f.write(str(infoD['IPD']))


		
def saveMetadata(infoD):
	
	fileName = '00_metadata_' + getTimestamp() + '.pkl'
	filePath = os.path.join( infoD['Results path'], fileName )
	
	with open(filePath, 'wb') as f:
		pickle.dump(infoD, f)
	

class ExpLogger:
	
	def __init__(self, infoD, existingFile = ''):
		
		self.resultsPath = infoD['Results path']
		
		if not existingFile:
			self.filePath = os.path.join(self.resultsPath, 
										'00_expLog_' + getTimestamp() + '.log' )
			
			with open(self.filePath,'x') as f:
				f.write('BlockNumber,StartTime,TestsDone,RunningMin,BlockCompleted,EndTime\n')
			
		else:
			self.filePath = os.path.join(self.resultsPath, existingFile )
		
			# 0 _ block number
			# 1 _ start time of block [timestamp]
			# 2 _ tests completed [0,1]
			# 3 _ running time in minutes [int] 
			# 4 _ block completed [0,1]
			# 5 _ end time [timestamp]
	
	def newBlock(self, blockNumber):
		
		with open(self.filePath,'a') as f: # add new line
			f.write(str(blockNumber) + ',' + getTimestamp() + ',' + '0,0,0,None\n')
	
		
	def testsCompleted(self):
		
		self.modifyLastLine(newValue = '1', valueIndex = 2)
	
	
	def blockCompleted(self):
		
		self.modifyLastLine(newValue = '1', valueIndex = 4)
		self.modifyLastLine(newValue = getTimestamp() + '\n', valueIndex = 5)
	
	
	
	def runningBlock(self, totalDuration, state):
		
		startMinute = state["minutesPassed"]
		
		def runBlockTask(totalDuration):
			
			currentMinute = startMinute
			endTime = viz.tick() + totalDuration
			
			while viz.tick() < endTime:
				
				yield viztask.waitTime(59)
				
				# update log				
				currentMinute += 1
				self.modifyLastLine(newValue = str(currentMinute), valueIndex = 3)
				
				# update current state file
				state["minutesPassed"] = currentMinute
				updateState(state,self.resultsPath)
		
		viztask.schedule(runBlockTask(totalDuration))
		
	
			
	def modifyLastLine(self,newValue,valueIndex):
		
		with open(self.filePath,'r') as f:
			
			# read all lines
			allLines = f.readlines()
			
			# get last
			lastLine = allLines[-1]
			
			# get line values
			lineValues = lastLine.split(',')
						
			# modify value
			lineValues[valueIndex] = str(newValue) 
			
			newLastLine = ','.join(lineValues)
			allLines[-1] = newLastLine
			
			allLines = ''.join(allLines)
			
			#print(allLines)
			
		with open(self.filePath,'w') as f:
			
			# write to file						
			f.write(allLines)


# Function to continously save current state
def updateState(stateDict,resultsDir):
		
	filename = f"{resultsDir}/current_state.json"
	
	with open(filename, "w") as file:
		json.dump(stateDict, file, indent=4)
		

# Function to restore already started session
def restoreSession(infoD):
	
	resultsPath = infoD['Results path']
	
	currentStatusFile = glob.glob(f"{resultsPath}/current_state.json")

	if currentStatusFile:
		with open(currentStatusFile[0], "r") as f:
			state = json.load(f)
			
		print("State restored:", state)
		
	else:
		print("Existing state file not found, starting from the beginning")
		state = {"currentBlock": 0,
				 "salivaDone": False,
				 "apvtDone": False,
				 "minutesPassed": 0}
		
	return state
	
# 	logPath = os.path.join(infoD['Results path'],infoD['Existing log'])
# 	
# 	with open(logPath,'r') as f:
# 		
# 		# get last line
# 		allLines = f.readlines()
# 		lastLine = allLines[-1]
# 		lineValues = lastLine.split(',')
# 		
# 		# get last block
# 		try:
# 			lastBlock = int(lineValues[0])
# 		
# 			# completed?
# 			blockComplete = int(lineValues[4])
# 			
# 			# determine last block
# 			if blockComplete == 1: # continue with next block
# 				
# 				startBlock = lastBlock + 1
# 				testsCompleted = False
# 				minutesPassed = 0
# 				
# 			elif blockComplete == 0:# restore previous block
# 				
# 				startBlock = lastBlock
# 				
# 				# tests completed?
# 				testsCompleted = bool(int(lineValues[2]))
# 				
# 				# get running time
# 				minutesPassed = int(lineValues[3])
# 		
# 		
# 		except: # file created but no info in it
# 			startBlock = 0
# 			testsCompleted = False
# 			minutesPassed = 0
# 			
# 		# 0 _ block number
# 		# 1 _ start time of block [timestamp]
# 		# 2 _ tests completed [0,1]
# 		# 3 _ running time in minutes [int] 
# 		# 4 _ block completed [0,1]
# 		# 5 _ end time [timestamp]
# 	
# 	
# 	return startBlock, testsCompleted, minutesPassed
		
#___________________________________________________
# HDM & EYE-TRACKER
#___________________________________________________


#____________________
# connect to Vive Pro
def connectToVive():
	
	# connect to HMD
	hmd = steamvr.HMD()
	
	if not hmd.getSensor():
		raise ConnectionError('SteamVR HMD not detected')

	# Connect to eye tracker
	VivePro = viz.add('VivePro.dle')
	eyeTracker = VivePro.addEyeTracker()
	
	if not eyeTracker:
		raise ConnectionError('Eye tracker not detected')

	return [hmd,VivePro,eyeTracker]


#____________________
# set IPD
def setIPD(hmd,targetIPD):
	
	pass
	
	currentIPD = hmd.getIPD()
	
	while currentIPD != targetIPD:
		
		
		vizinput.message()
		
		currentIPD = hmd.getIPD()
		

#____________________
# eye-tracker logger

#def eyetrackerLogger(eyetracker, resultsPath, runDuration_sec, eyeTrackerFrequency = 90):
#	
#	# get eyetracker timing
#	timeToWait = math.floor(1/eyeTrackerFrequency * 1000) / 1000
#	
#	
#	# create file if it doesn't exist
#	if not os.path.exists(resultsPath):
#		
#		with open(resultsPath, 'w', newline = '') as f:
#			
#			writer = csv.writer(f)
#			writer.writerow(['Timestamp',
#							'Left eye open', 'Right eye open',
#							'Left pupil diam', 'Right pupil diam',
#							'Gaze point','Raw gaze'])
#	
#	
#	# start saving data
#	with open(resultsPath, 'a', newline = '') as f:
#		
#		writer = csv.writer(f)
#		
#		end_time = viz.tick() + runDuration_sec
#		
#		
#		while viz.tick() < end_time:
#			
#			# get data
#			timestamp = getTimestamp()
#			
#			left_eyeOpen = eyetracker.getEyeOpen(eye = viz.LEFT_EYE)
#			right_eyeOpen = eyetracker.getEyeOpen(eye = viz.RIGHT_EYE)
#			
#			left_pupilDiam = eyetracker.getPupilDiameter(eye = viz.LEFT_EYE)
#			right_pupilDiam= eyetracker.getPupilDiameter(eye = viz.RIGHT_EYE)
#			
#			# get raw gaze
#			gazeMat = eyetracker.getMatrix()
#			rawGaze = gazeMat
#			
#			# intersect with world
#			gazeMat.postMult(viz.MainView.getMatrix())			
#			line = gazeMat.getLineForward(1000)			
#			info = viz.intersect(line.begin, line.end)
#			infoPoint = info.point
#			
#			
#			writer.writerow([timestamp, 
#						left_eyeOpen, right_eyeOpen, 
#						left_pupilDiam, right_pupilDiam,
#						infoPoint,rawGaze])
#			
#			
#			# wait for next datapoint
#			yield viztask.waitTime(timeToWait)


#____________________
# VERSION 2!! eye-tracker logger --> using Pandas

def eyetrackerLogger2(eyetrackerObj, resultsPath, runDuration_sec, eyeTrackerFrequency, 
						sceneObj, 
						eyesClosedDetection, eyesClosedSound , eyesClosedInterval = 60):
	
	print('Starting eye-tracking')
	
	# get eyetracker timing
	timeToWait = math.floor(1/eyeTrackerFrequency * 1000) / 1000
	
	# to save results
	d_timeStamps = []
	d_leftEyeOpen = []
	d_rightEyeOpen = []
	d_leftPupilDiam = []
	d_rightPupilDiam = []
	d_gazePoint = []
	d_leftScreenIntensity = []
	d_rightScreenIntensity = []
	
	# for eyes closed detection
	countLimit = round(eyesClosedInterval/timeToWait)
	
	counter = 0
	
	# START		
	end_time = viz.tick() + runDuration_sec
	
	while viz.tick() < end_time:
			
		# get data
		timestamp = getTimestamp()
		
		# screen intensity
		[left_screen,right_screen] = sceneObj.getIntensity()
			
		left_eyeOpen = eyetrackerObj.getEyeOpen(eye = viz.LEFT_EYE)
		right_eyeOpen = eyetrackerObj.getEyeOpen(eye = viz.RIGHT_EYE)
		
		left_pupilDiam = eyetrackerObj.getPupilDiameter(eye = viz.LEFT_EYE)
		right_pupilDiam= eyetrackerObj.getPupilDiameter(eye = viz.RIGHT_EYE)
		
		# get raw gaze
		gazeMat = eyetrackerObj.getMatrix()
					
		# intersect with world
		gazeMat.postMult(viz.MainView.getMatrix())			
		line = gazeMat.getLineForward(1000)			
		info = viz.intersect(line.begin, line.end)
		infoPoint = info.point
		
		# append
		d_timeStamps.append(timestamp)
		d_leftEyeOpen.append(left_eyeOpen)
		d_rightEyeOpen.append(right_eyeOpen)
		d_leftPupilDiam.append(left_pupilDiam)
		d_rightPupilDiam.append(right_pupilDiam)
		d_gazePoint.append(infoPoint)
		d_leftScreenIntensity.append(left_screen)
		d_rightScreenIntensity.append(right_screen)
		
		# counter
		counter +=1
		
		if counter >= countLimit:
			
			# check last few measurements
			left_data = d_leftEyeOpen[-countLimit:]
			right_data = d_leftEyeOpen[-countLimit:]
			
			if checkEyesClosed(left_data) and checkEyesClosed(right_data):
				eyesClosedSound.play()
				print('Eyes Closed detected!')
			
			# reset counter
			counter = 0
		
		
		# wait for next datapoint
		yield viztask.waitTime(timeToWait)
	
	
	print('Finished eye-tracking')
	
	
	# save data
	df = pd.DataFrame({'Timestamp': d_timeStamps, 
						'Left eye open': d_leftEyeOpen,
						'Right eye open': d_rightEyeOpen,
						'Left pupil diam': d_leftPupilDiam, 
						'Right pupil diam': d_rightPupilDiam,
						'Left screen intensity': d_leftScreenIntensity,
						'Right screen intensity': d_rightScreenIntensity,
						'Gaze coordinates': d_gazePoint})
	#print(df)
	
	df.to_csv(resultsPath, index = False)


def checkEyesClosed(eyeData, maxPercentage = 0.25, threshold = 0.5):
	
	closedCount = sum(1 for element in eyeData if element < threshold)
	
	closedPercentage = closedCount/len(eyeData)
	
	return closedPercentage >= maxPercentage

#___________________________________________________
# CEDRUS RESPONSE PAD
#___________________________________________________
	
#_____________________
## connect to Cedrus device
def connectToCedrus():

	# get a list of all attached XID devices
	devices = pyxid2.get_xid_devices()
	
	if not devices:
		raise ConnectionError("Cedrus response pad not detected. Please close Vizard, connect the device and reopen the program.")

	dev = devices[0] # get the first device to use	
	
	dev.reset_timer() # make sure that this works
	
	return dev
	

#_____________________
## get Cedrus responses

def waitCedrusResponse(dev, timeout_sec, feedbackSound, playSound = False,keyList = [0,1,2,3,4]):
		
	keysPressed = []
	responseTimes = []
	
	dev.flush_serial_buffer()
	dev.clear_response_queue()
	
	dev.reset_timer() # restart timer
	
	endTime = viz.tick() + timeout_sec
	
	while viz.tick() <= endTime:
		
		dev.poll_for_response()
		
		if dev.has_response():
			
			response = dev.get_next_response()
			 
			if response['pressed'] and response['key'] in keyList:
				responseTimes.append(response['time'])
				keysPressed.append(response['key'])
				
				if playSound:
					feedbackSound.play()
	
	return responseTimes, keysPressed


def waitCedrusKey(dev, timeout = 60*60, keyList = [0,1,2,3,4]):
	
	dev.flush_serial_buffer()
	dev.clear_response_queue()
	
	waitingKey = True
	
	endTime = viz.tick() + timeout
	
	while waitingKey and viz.tick() < endTime:
			
		dev.poll_for_response()
		
		if dev.has_response():
				
			response = dev.get_next_response()
			if response['pressed'] and response['key'] in keyList:
					waitingKey = False
	


#___________________________________________________
# EXPERIMENT CLASSES
#___________________________________________________

#____________________
## EXP SCENE

class DichopticScene:
	
	def __init__(self, sceneColour = viz.GRAY, window = viz.MainWindow):

		self.sceneObj = viz.addScene()
		self.sceneColour = sceneColour
		
		self.left_field = self.addVisualField(self.sceneObj,self.sceneColour, viz.LEFT_EYE)
		self.right_field = self.addVisualField(self.sceneObj,self.sceneColour, viz.RIGHT_EYE)
		
		# add to window
		viz.MainWindow.setScene(self.sceneObj)
		
		self.show()
		
		self.rightEyeUsed = random.choice([True,False])
		
	@staticmethod
	def addVisualField(sceneObj,sceneColour,eye):
		visualField = viz.addCustomNode('skydome.dlc', scene = sceneObj)
		visualField.color(sceneColour)
		visualField.renderToEye(eye)
		return visualField
		
	def show(self):
		self.left_field.visible(viz.ON)
		self.right_field.visible(viz.ON)
		
	def setToBlack(self):
		self.left_field.color([0,0,0])
		self.right_field.color([0,0,0])
		
	def reset(self):
		self.left_field = self.addVisualField(self.sceneObj,self.sceneColour, viz.LEFT_EYE)
		self.right_field = self.addVisualField(self.sceneObj,self.sceneColour, viz.RIGHT_EYE)	

	def getIntensity(self):
		leftColour = self.left_field.getColor()[0]
		rightColour = self.right_field.getColor()[0]
		
		return leftColour,rightColour
	
	def setEyeIntensity(self, eye, intensity: float):
		
		if eye == "left":
			self.left_field.color([intensity]*3)
			self.right_field.color([0,0,0])
			
		if eye == "right":
			self.left_field.color([0,0,0])
			self.right_field.color([intensity]*3)
		
	def setCondition(self, condition, freq = 0, waveform = '', duration = 20 * 60, crest = 1):
		
		if condition == 'dark': # dark
			self.left_field.color([0,0,0])
			self.right_field.color([0,0,0])

		elif condition == 'constant': # constant half-brightness
			
			halfBright = [0.5**(1/2.22)] *3 # gamma correction
			
			self.left_field.color(halfBright)
			self.right_field.color(halfBright)
		
		elif condition == 'monocular' or condition == 'monocular-flip':
			
			if condition == 'monocular-flip':
				self.rightEyeUsed = not self.rightEyeUsed    
			
			if self.rightEyeUsed:
				self.right_field.color([1,1,1])
				self.left_field.color([0,0,0])
				
			elif not self.rightEyeUsed:
				self.right_field.color([0,0,0])
				self.left_field.color([1,1,1])
					
		elif condition=='in-phase' or condition=='counter-phase': # FLICKER
			
			half_period = 0.5/freq
			
			# calculate total number of cycles
			totalCycles = duration * freq
			
			if isinstance(totalCycles,float):
				totalCycles = math.ceil(totalCycles)
			
			
			# Type of flicker
			if waveform == 'sin':
				
				# create flicker sequence
				lumMax = vizact.fadeTo([crest]*3, time=half_period, interpolate = vizact.easeOutSine())
				lumMin = vizact.fadeTo([1-crest]*3, time=half_period, interpolate = vizact.easeInSine())
			
				flicker = vizact.sequence(lumMin,lumMax, totalCycles)
				
				if condition=='in-phase': # in-phase flicker
				
					vizact.parallel(self.left_field.add(flicker),self.right_field.add(flicker))
				
				elif condition=='counter-phase': # counter-phase flicker
					
					counter_flicker = vizact.sequence(lumMax,lumMin, totalCycles)
				
					vizact.parallel(self.left_field.add(flicker),self.right_field.add(counter_flicker))
			
			
			elif waveform == 'square':
				
				waitHalfPeriod = vizact.waittime(half_period)
				
				lumOn_left = vizact.call(self.left_field.color,[1,1,1]) 
				lumOff_left = vizact.call(self.left_field.color,[0,0,0])
				
				lumOn_right = vizact.call(self.right_field.color,[1,1,1]) 
				lumOff_right = vizact.call(self.right_field.color,[0,0,0])
				
				
				flicker_left = vizact.sequence(lumOff_left,waitHalfPeriod,lumOn_left,waitHalfPeriod, totalCycles) 
				
				
				if condition=='in-phase': # in-phase flicker
					
					flicker_right = vizact.sequence(lumOff_right,waitHalfPeriod,lumOn_right,waitHalfPeriod, totalCycles) 
					
					vizact.parallel(self.left_field.add(flicker_left),self.right_field.add(flicker_right))
				
				elif condition=='counter-phase': # counter-phase flicker
					
					counter_flicker_right = vizact.sequence(lumOn_right,waitHalfPeriod,lumOff_right,waitHalfPeriod, totalCycles) 
				
					vizact.parallel(self.left_field.add(flicker_left),self.right_field.add(counter_flicker_right))
			
			
			
		else:
			raise ValueError("Invalid condition code provided")
			
			
#____________________
## FIXATION CROSS
class FixationCross():

	def __init__(self, sceneObject, expCondition, crossText = '•',fontSize = 0.15):
		
		# add fixation cross
		self.fixationCross = viz.addText(crossText, scene = sceneObject)
		self.fixationCross.fontSize(fontSize)
		self.fixationCross.color(newColourGenerator(viz.BLUE,expCondition))
		
		# position
		self.fixationCross.alignment(viz.ALIGN_CENTER_CENTER)
		self.fixationCross.setPosition([0, 1.8 , 2])
		
		# other
		self.fixationCross.resolution(1)
		self.fixationCross.disable(viz.LIGHTING)
		
		# add border		
		self.border = viz.addText(crossText, scene = sceneObject)
		self.border.alignment(viz.ALIGN_CENTER_CENTER)
		self.border.setPosition([0, 1.8 , 2.01])
		self.border.resolution(1)
		self.border.fontSize(fontSize*2)
		
		if expCondition ==1: # dark
			self.border.color(viz.BLACK)
			
		else:
			self.border.color(viz.GRAY)
		
		# hide
		self.fixationCross.visible(viz.OFF)
		self.border.visible(viz.OFF)
		
	def show(self):
		self.fixationCross.visible(viz.ON)
		self.border.visible(viz.ON)
		
	def hide(self):
		self.fixationCross.visible(viz.OFF)
		self.border.visible(viz.OFF)
		
	def changeColour(self, newColour):
		self.fixationCross.color(newColour)
		
	def getColour(self):
		currentColour = self.fixationCross.getColor()
		currentColour = tuple(currentColour)
		
		return currentColour



#___________________
## INFO SCENE

class InfoPanelScene:
	
	def __init__(self, expInfo, sceneColour = viz.BLACK, fontSize = 12):
		
		self.window = viz.addWindow() 
		self.window.clearcolor(sceneColour)
		self.window.setPosition([0,1])
		self.window.setSize([1,1])
		
		self.scene = viz.addScene()
		self.window.setScene(self.scene)
		
		# add text
		self.panel = vizinfo.InfoPanel('', title = 'Session Information', icon = False, 
										align = viz.ALIGN_LEFT_TOP,
										margin = (0,0),
										window = self.window)
										
		self.panel.addLabelItem('Participant ID: ', viz.addText(str(expInfo.get('Participant ID'))))
		self.panel.addLabelItem('Session number: ', viz.addText(str(expInfo.get('Session number'))))

		
		# STATUS
		self.panel.addSeparator(padding=(5,5))
		
		self.currentStatus = self.panel.addLabelItem('Current status: ', 
										viz.addText("Waiting _____________________________________________________________"))
		
		
		# BLOCKS
		self.panel.addSeparator(padding=(5,5))
		
		self.allBlocks = expInfo.get('blockStimulus')
		self.pupilDilation = expInfo.get('pupilDilation')
		
		self.remainingBlocks =  self.panel.addLabelItem('Remaining blocks: ', viz.addText(str(self.allBlocks)))
		self.remainingPupil = self.panel.addLabelItem('Pupil dilation: ', viz.addText(str(self.pupilDilation)))
				
		# remaining time
		self.timerText = viz.addText(value = "00:00:00", scene = self.scene, pos =[0,1,4])
		self.timerText.color(viz.RED)
		self.timerText.alignment(viz.ALIGN_CENTER_BOTTOM)
		self.timerText.setScale([0.9,0.9,1])
		self.timerText.resolution(1)
		
	
		#_________________
		#  BUTTONS
		self.panel.addSeparator(padding=(5,5))
		
		row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_BOTTOM,background=False,border=False)
		
		awakeButton = row.addItem(viz.addButtonLabel('Are you awake?'))
		eyesOpenButton = row.addItem(viz.addButtonLabel('Keep eyes open'))
		
		self.panel.addLabelItem('Play sounds: ', row)
		
		# add actions to buttons
		vizact.onbuttondown(awakeButton,playWarning,'awake')
		vizact.onbuttondown(eyesOpenButton,playWarning,'eyes')
		
				
		
	def logEvent(self,logText):
		with open(self.filePath,'a') as f:
			f.write(getTimestamp() + ',' + logText + '\n')
	
	
	def logOther(self):
		
		otherLogText = vizinput.input('Text to Log:', title='Log other events...')
		
		if otherLogText:
			self.logEvent(otherLogText)
			
	def showMessage (self, messageText = "", textColor = viz.RED):
		
		self.timerText.color(textColor)
		self.timerText.message(messageText)
	
	def timeCounter(self,textColor = viz.BLUE):
		
		self.timerText.color(textColor)
		startTime = viz.tick()
		
		def counterTask(startT):
			currentTime = datetime.timedelta(seconds = round(viz.tick()-startT))
			self.timerText.message(str(currentTime))
			yield viztask.waitTime(0.25)
		
		viztask.schedule(counterTask(startTime))

	def updateStatus(self, newStatus = "None"):
		
		self.currentStatus.message(newStatus)
		
	
	def newBlock(self, newBlock, totalDuration_sec, condition):
		
		if condition == 1:
			stimMessage = " - with stimulus"
		elif condition == 0:
			stimMessage = " - no stimulus"
			
		self.updateStatus(newStatus = 'Running block ' + (str(newBlock+1)) + stimMessage)
		
		# start timer
		self.runTimer(totalDuration_sec,viz.GRAY,'...')
		
		# update remaining blocks		
		self.remainingBlocks.message(str(self.allBlocks[newBlock:]))
		self.remainingPupil.message(str(self.pupilDilation[newBlock:]))
	
	
	def runTimer(self,totalDuration, textColor = viz.RED, finalMessage = 'Done!'):
		
		def timerTask(duration):
			
			endTime =  viz.tick() + duration
				
			while viz.tick() < endTime:
						
				remainingTime = datetime.timedelta(seconds= round(endTime - viz.tick()))
						
				self.timerText.message(str(remainingTime))
						
				yield viztask.waitTime(0.25)
			
			
			self.timerText.message(finalMessage)
		
		# set color
		self.timerText.color(textColor)
		
		viztask.schedule(timerTask(totalDuration))
		


def playWarning(warnType):
	
	viveHandle = getAudioHandle(keyword = 'vive')
	headphonesHandle = getAudioHandle(keyword = 'realtek')
	
	if warnType == 'awake':
		fileName = "99_awake_question.wav"
		
	elif warnType == 'eyes':
		fileName = "keepEyesOpen.wav"
	
	
	fullPath = os.path.join("resources","audio",fileName)

	soundVive = viz.addAudio(fullPath, device = viveHandle)
	soundVive.volume(0.5)
	
	soundHeadphone = viz.addAudio(fullPath, device = headphonesHandle)
	soundHeadphone.volume(0.5) 
	
	soundVive.play()
	soundHeadphone.play()
	
#___________________________________________________
# EXPERIMENT FUNCTIONS
#___________________________________________________

#_____________________
## different colour generator
def newColourGenerator(currentColour, expCondition):
	
	if expCondition == 1:
		
		colourList =[(.2, 0, 0),  # red
					(0, 0, .2), # blue
					(0, .2, 0), # green
					(.2, .2, 0)]  # yellow
	else:
		colourList =[(1, 0, 0),  # red
					(0, 0, 1), # blue
					(0, 1, 0), # green
					(1, 1, 0)]  # yellow
	
	newColour = ( round(currentColour[0],1),
				  round(currentColour[1],1),
				  round(currentColour[2],1) )

	currentColour = newColour
		
	while newColour == currentColour:
		
		randChoice = np.random.randint(0,len(colourList))
		newColour = colourList[randChoice]
	

	return newColour
	

#_____________________
## FIXATION CROSS TEST
def changeAudioDevice(keyword = 'realtek'):
	
	# choose audio device
	audioDeviceHandle = None
	
	# go through list of devices and find keyword
	for deviceFound in viz.getAudioDeviceList():
		
		#print(deviceFound) 
		
		if keyword.lower() in deviceFound.name.lower():
			
			audioDeviceHandle = deviceFound
			
			yield viz.setDefaultAudioDevice(audioDeviceHandle)
			
			return
			#print('Found audio device: ', audioDeviceHandle.name)
	
	# otherwise assign first device
	if not audioDeviceHandle:
		
		audioDeviceHandle =  viz.getAudioDeviceList()[0]
		
		print('Keyword ', keyword, ' not found...')
		print('Using default device instead: ', audioDeviceHandle.name)
		
		yield viz.setDefaultAudioDevice(audioDeviceHandle)
			
		return
	# set as default audio device for vizard
	
	
	
	
def getAudioHandle(keyword = 'realtek'):
	
	# choose audio device
	audioDeviceHandle = None
	
	# go through list of devices and find keyword
	for deviceFound in viz.getAudioDeviceList():
		
		#print(deviceFound) 
		
		if keyword.lower() in deviceFound.name.lower():
			
			audioDeviceHandle = deviceFound
			return audioDeviceHandle
			
			#print('Found audio device: ', audioDeviceHandle.name)
	
	# otherwise assign first device
	if not audioDeviceHandle:
		
		audioDeviceHandle =  viz.getAudioDeviceList()[0]
		
		print('Keyword ', keyword, ' not found...')
		print('Using default device instead: ', audioDeviceHandle.name)
	
		return audioDeviceHandle
	
	


def fixationCrossTest(fixCross, cedrusDevice, totalDuration, resultsPath,
						soundDict, expCondition,
						minPresentation = 1, maxPresentation = 10,
						keyList = [0,1,2,3,4]):

		
	# get sounds
	instrSound = soundDict['visPvtIns'] 
	endSound = soundDict['visPvtEnd']
	beepFeedback = soundDict['feedbackBeep']

	instrSound.volume(0.2)
	endSound.volume(0.2)
	beepFeedback.volume(0.1)
	
	
	
	# default audio device
	yield changeAudioDevice(keyword = 'vive')
	
	
	# create file
	with open(resultsPath, 'w', newline = '') as f:
			
		writer = csv.writer(f)
		writer.writerow(['Timestamp',
						'Colour presented',
						'Presentation time',
						'Keys pressed',
						'Response Times' ])
	
	
	with open(resultsPath, 'a', newline = '') as f:
		
		writer = csv.writer(f)
		
		# RUN
		endTime = viz.tick() + totalDuration

		# play audio instructions
		instrSound.play()
		
		yield viztask.waitDirector(waitCedrusKey,cedrusDevice,16)
		
		instrSound.stop()
		
		while viz.tick() < endTime:
		
		
			# get new colour
			currentColour = fixCross.getColour()
			newColour = newColourGenerator(currentColour,expCondition)
			
			
			# random duration
			presentationTime = round(np.random.uniform(minPresentation,maxPresentation),2)

			
			# change fixation cross colour
			yield fixCross.changeColour(newColour)
			tStamp = getTimestamp()
			
			
			# capture all responses during presentation time in parallel
			dataOut = yield viztask.waitDirector(waitCedrusResponse,
													cedrusDevice, 
													presentationTime,
													beepFeedback,
													True,
													keyList)
			
			
			responseTimes = dataOut.returnValue[0]
			keysPressed = dataOut.returnValue[1]
			
			#print(responseTimes,keysPressed)
		
			writer.writerow([tStamp, 
							newColour, 
							presentationTime, 
							responseTimes, 
							keysPressed])
	
	# task finished
	endSound.play()
	yield viztask.waitTime(2)
	

	
#_____________________
## auditory PVT

def createPVTSound(fileName, frequency = 1000, soundDuration_ms = 475):
	
	# parameters
	rate = 50000 # samples per sec
	T = soundDuration_ms / 1000 # duration_secs
	f = frequency # frequency Hz
	
	# compute waveform
	t = np.linspace(0, T, int(T*rate), endpoint = False)
	x = np.sin(2* np.pi * f * t)
	
	# write samples to file
	wavio.write(fileName, x, rate, sampwidth = 3)






def aPVT(cedrusDevice, totalDuration, resultsPath, soundDict, 
		minInterval = 1, maxInterval = 9, soundVolume = 0.09,
		keyList = [0,1,2,3,4]):
	
	
	# to save results
	d_Timestamps = []
	d_IntervalTime = []
	d_RTs = []
	d_Keys = []
	
		
	# get sounds
	beepSound = soundDict['beep'] 
	instrSound = soundDict['aPvtIns'] 
	endSound = soundDict['endTask']
	
	# adjust volume
	beepSound.volume(soundVolume)	
	instrSound.volume(0.3)
	endSound.volume(0.3)
	
	# default audio device
	changeAudioDevice(keyword = 'realtek')

	# Play INSTRUCTIONS
	instrSound.play()
	yield waitCedrusKey(cedrusDevice, timeout = 12)
	instrSound.stop()
	
	# RUN
	endTime = viz.tick() + totalDuration
	yield viztask.waitTime(1)
	
	while viz.tick() < endTime:
		
		# random time interval
		randomInterval = round(np.random.uniform(minInterval,maxInterval),2)
			
		# play sound
		beepSound.play()
		tStamp = getTimestamp()
		
		
		# capture all responses during interval --> in parallel
		dataOut = yield viztask.waitDirector(waitCedrusResponse,
												cedrusDevice, 
												randomInterval,
												[],
												False,
												keyList)
												
		responseTimes = dataOut.returnValue[0]
		keysPressed = dataOut.returnValue[1]
		
		#print(responseTimes,keysPressed) # TEMPORARY
		
		# save results
		d_Timestamps.append(tStamp)
		d_IntervalTime.append(randomInterval)
		d_RTs.append(responseTimes)
		d_Keys.append(keysPressed) 
		
	
	# play task completed
	yield endSound.play()
	yield viztask.waitTime(2)
	
	# export results
	df = pd.DataFrame({'Timestamps': d_Timestamps, 
						'Interval to next sound_s': d_IntervalTime,
						'Keys pressed': d_Keys,
						'Response Times': d_RTs})
	
	# export as csv
	df.to_csv(resultsPath, index = False)
	
