
import viz
import vizact
#import viztask

#import vizinfo
#import vizdlg
#import vizinput
import steamvr

import serial
#import warnings

#import pandas as pd
import numpy as np
#import pickle
import os



#___________________________________________________
# FOR SPECTRAL MEASUREMENTS
#___________________________________________________

class Spectraval:
    
    def __init__(self, 
               port='/dev/ttyUSB2', 
               baudrate=921600, 
               bytesize=8, 
               stopbits=1, 
               parity='N', 
               timeout=240):
        
        # open serial connection
        self.ser = serial.Serial(
            port = port,
            baudrate = baudrate, 
            bytesize = bytesize, 
            stopbits = stopbits, 
            parity = parity,
            timeout = timeout)
        
    def turnDisplayOff(self):
        self.ser.write(b'*CONF:DISPEN 0\r')
        
    def measurement(self, integration_time=None, setting={}):
        
        # Perform reference measurement
        self.ser.write(b'*MEAS:REF 0 1 0\r')
        ack = self.ser.read(1)
        while ack != b'\x07':
            ack = self.ser.read(1)
            
        # Calculate spectral radiance and retrieve byte array
        # as 32-bit float. Note that the first two bytes are
        # not part of the spectrum.
        self.ser.write(b'*CALC:SPRAD\r')
        data = self.ser.read(1606)
        spec = np.frombuffer(data[2:], dtype=np.float32)

        
        return spec


def getRGBs(colours,steps):
    
    RGBs = np.zeros((len(colours)*len(steps)+1,3)) #+1
    
    outColours = []
    outColours.append("none")
    
    row = 1 # 1
    
    for c in colours:
                
        # get column index according to colour
        if c == "w":
            column = [0,1,2]
        elif c=="r":
            column = 0
        elif c=="g":
            column = 1
        elif c=="b":
            column = 2
        else:
            raise ValueError("The colour '" + c + "' is not recognised")
    
        # append each step to the correct column index
        for s in steps:
            
            RGBs[row,column] = s
            outColours.append(c)
            
            row += 1

    return RGBs, outColours


# monocular scene
class MonoScene:
    
    def __init__(self, window = viz.MainWindow):

        self.sceneObj = viz.addScene()
        self.sceneColour = viz.BLACK
        
        self.left_field = self.addVisualField(self.sceneObj,self.sceneColour, viz.LEFT_EYE)
        self.right_field = self.addVisualField(self.sceneObj,self.sceneColour, viz.RIGHT_EYE)
        viz.MainWindow.setScene(self.sceneObj)

    @staticmethod
    def addVisualField(sceneObj,sceneColour,eye):
        visualField = viz.addCustomNode('skydome.dlc', scene = sceneObj)
        visualField.color(sceneColour)
        visualField.renderToEye(eye)
        return visualField

        
    def reset(self):
        self.left_field = self.addVisualField(self.sceneObj,self.sceneColour, viz.LEFT_EYE)
        self.right_field = self.addVisualField(self.sceneObj,self.sceneColour, viz.RIGHT_EYE)    
                
                
    def setColour(self, eye, rgb):
        
        if eye == "left":
            
            self.left_field.color(rgb[0],rgb[1],rgb[2])
            self.right_field.color([0,0,0])

        elif eye == "right":
            self.left_field.color([0,0,0])
            self.right_field.color(rgb[0],rgb[1],rgb[2])
                    
        else:
            raise ValueError("Eye value not recognised")

        


#___________________________________________________
# TEMPORAL MEASUREMENTS PARAMETERS
#___________________________________________________

def getMeasuresParams():
    
    totalTime = 30
    
    gammaCorr = 1 # 2.2252
    
    freqs = [.05, .1, .2, .4, .79, 1.58, 3.16, 6.3, 12.56, 25.06, 45] # Hz
    
    conditionsFreq = [[2,0]] # constant light
    for i in freqs:
        conditionsFreq.append([3,i])
        #conditionsFreq.append([4,i])
    
    #conditions: 1-dark, 2-constant, 3-in phase, 4-counter phase
    
    
    # conditionsFreq.append([1,0]) # append dark

    #pathToComms = os.path.dirname(os.path.abspath(__file__)) + '/comms'
    
    pathToComms = 'D:/Calibration code/comms'

    return gammaCorr, totalTime, conditionsFreq, pathToComms

    
  

    
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
    
    return [hmd,VivePro]



#___________________________________________________
# EXPERIMENT
#___________________________________________________


#____________________
## EXP SCENE

class DichopticScene:
    
    def __init__(self, sceneColour = viz.GRAY, fixationColour = viz.RED, window = viz.MainWindow):

        self.sceneObj = viz.addScene()
        self.sceneColour = sceneColour
        
        self.left_field = self.addVisualField(self.sceneObj,self.sceneColour, viz.LEFT_EYE)
        self.right_field = self.addVisualField(self.sceneObj,self.sceneColour, viz.RIGHT_EYE)


        # fixation cross
        self.fixationCross = viz.addText('+', scene = self.sceneObj)
        self.fixationCross.alignment(viz.ALIGN_CENTER_CENTER)
        self.fixationCross.color(fixationColour)
        self.fixationCross.setPosition([0,1.8,2])
        self.fixationCross.fontSize(0.2)
        self.fixationCross.resolution(2)
        self.fixationCross.visible(viz.OFF)
        
    
    @staticmethod
    def addVisualField(sceneObj,sceneColour,eye):
        visualField = viz.addCustomNode('skydome.dlc', scene = sceneObj)
        visualField.color(sceneColour)
        visualField.renderToEye(eye)
        return visualField


    def show(self):
        viz.MainWindow.setScene(self.sceneObj)
        
    def showFixationCross(self):
        self.fixationCross.visible(viz.ON)
        
    def hideFixationCross(self):
        self.fixationCross.visible(viz.OFF)

    def reset(self):
        self.left_field = self.addVisualField(self.sceneObj,self.sceneColour, viz.LEFT_EYE)
        self.right_field = self.addVisualField(self.sceneObj,self.sceneColour, viz.RIGHT_EYE)    
        
    def hide(self):
        self.left_field.visible(viz.OFF)
        self.right_field.visible(viz.OFF)
        self.hideFixationCross()
    
    
    def setCondition(self, condCode, freq = 0, crest = 1):
        
        if condCode == 1: # dark
            self.left_field.color([0,0,0])
            self.right_field.color([0,0,0])

        elif condCode == 2: # constant light 
            self.left_field.color([1,1,1])
            self.right_field.color([1,1,1])
                    
        elif condCode == 3 or condCode == 4: # FLICKER
            
            half_period = 0.5/freq
            
            lumMax = vizact.fadeTo([crest]*3, time=half_period, interpolate = vizact.easeOutSine())
            lumMin = vizact.fadeTo([1-crest]*3, time=half_period, interpolate = vizact.easeInSine())
            flicker = vizact.sequence(lumMin,lumMax,viz.FOREVER)
            
            if condCode == 3: # in-phase flicker
                
                vizact.parallel(self.left_field.add(flicker),self.right_field.add(flicker))
                
            elif condCode == 4: # counter-phase flicker
                
                counter_flicker = vizact.sequence(lumMax,lumMin,viz.FOREVER)
                
                vizact.parallel(self.left_field.add(flicker),self.right_field.add(counter_flicker))
            
        else:
            raise ValueError("Invalid condition code provided")
            


#____________________
## INFO SCENE

class InfoScene:
    
    def __init__(self, window, sceneColour = viz.BLACK, textColor = viz.WHITE, fontSize = 12):

        self.sceneObj = viz.addScene()
        self.sceneColour = sceneColour

        window.clearColor
        

    def show(self):
        viz.window.setScene(self.sceneObj)
