#!/usr/bin/env python2
"""Display images from a specified folder and present them to the subject."""
# GalbraithHeat.py
# Created 11/09/15 by DJ based on DistractionTask_practice_d3.py
# Updated 11/10/15 by DJ - cleaned up comments
# Adapted 7/7/2020 by JG - Heat Anticipation Task: change stimuli and timings
# Updated 7/16/20 by DJ - pickle->psydat extension, .JPG image extension, set flip time to now after instructions
# Updated 7/29/20 by DJ - added VAS that's persistent throughout block, fixed color order, removed trial responses, simplified params
# Updated 8/20/20 by JG - created functions for output
# Updated 8/31/20 by JG - changed visuals, added heat input, added VAS pre, mid, post, modified instructions to start over


from psychopy import core, gui, data, event, sound, logging 
# from psychopy import visual # visual causes a bug in the guis, so it's declared after all GUIs run.
from psychopy.tools.filetools import fromFile, toFile # saving and loading parameter files
import time as ts, numpy as np # for timing and array operations
from scipy.integrate import simps
from numpy import trapz
import os, glob
#import AppKit, os, glob # for monitor size detection, files - could not import on windows
import BasicPromptTools # for loading/presenting prompts and questions
import RatingScales
import random # for randomization of trials
import string
import math


# ====================== #
# ===== PARAMETERS ===== #
# ====================== #
# Save the parameters declared below?
saveParams = True;
newParamsFilename = 'GalbraithHeatParams.psydat'

# Declare primary task parameters.
params = {
# Declare stimulus and response parameters
    'nTrials': 20,            # number of trials in each block
    'nBlocks': 3,             # number of blocks - need time to move electrode in between
    'stimDur': 2,             # time when stimulus is presented (in seconds)
    'painDur': 8,             # time of heat sensation (in seconds)
    'ISI': 0,                 # time between when one stimulus disappears and the next appears (in seconds)
    'tStartup': 5,            # pause time before starting first stimulus
    'imageDir': 'Circles/',   # directory containing image stimluli
    'imageSuffix': '.JPG',    # images will be selected randomly (without replacement) from all files in imageDir that end in imageSuffix.
# declare prompt and question files
    'skipPrompts': False,     # go right to the scanner-wait page
    'promptDir': 'Text/',     # directory containing prompts and questions files
    'promptFile': 'HeatAnticipationPrompts.txt', # Name of text file containing prompts 
    'questionFile': 'Text/AnxietyScale.txt', # Name of text file containing Q&As
    'questionDownKey': '1',   # move slider left
    'questionUpKey':'2',      # move slider right
    'questionDur': 999.0,
    'vasStepSize': 0.5,       # how far the slider moves with a keypress (increase to move faster)
    'textColor':(0,0,0),      # black in rgb255 space or gray in rgb space
    'PreVasMsg': "Let's do some rating scales.",             # Text shown BEFORE each VAS except the final one
    'moodQuestionFile1': 'Questions/ERVas1RatingScales.txt', # Name of text file containing mood Q&As presented before run
    'moodQuestionFile2': 'Questions/ERVasRatingScales.txt', # Name of text file containing mood Q&As presented after 3rd block
    'moodQuestionFile3': 'Questions/ERVas4RatingScales.txt', # Name of text file containing mood Q&As presented after run
    'questionSelectKey':'3', # select answer for VAS
    'questionSelectAdvances': True, # will locking in an answer advance past an image rating?
    'vasTextColor': (-1,-1,-1), # color of text in both VAS types (-1,-1,-1) = black
    'vasMarkerSize': 0.1,   # in norm units (2 = whole screen)
    'vasLabelYDist': 0.1,   # distance below line that VAS label/option text should be, in norm units
# declare display parameters
    'fullScreen': True,       # run in full screen mode?
    'screenToShow': 0,        # display on primary screen (0) or secondary (1)?
    'fixCrossSize': 50,       # size of cross, in pixels
    'fixCrossPos': [0,0],     # (x,y) pos of fixation cross displayed before each stimulus (for gaze drift correction)
    'screenColor':(255,255,255) # in rgb255 space: (r,g,b) all between 0 and 255 - white
# parallel port parameters
#    'sendPortEvents': False, # send event markers to biopac computer via parallel port
#    'portAddress': 0xE050,  # 0xE050,  0x0378,  address of parallel port
#    'codeBaseline': 31,     # parallel port code for baseline period (make sure it's greater than nBlocks*2*len(imageNames)!)
#    'codeVas': 32,          # parallel port code for mood ratings (make sure it's greater than nBlocks*2*len(imageNames)!)
}

# save parameters - isn't working on personal laptop
if saveParams:
    dlgResult = gui.fileSaveDlg(prompt='Save Params...',initFilePath = os.getcwd() + '/Params', initFileName = newParamsFilename,
        allowed="PICKLE files (.psydat)|.psydat|All files (.*)|")
    newParamsFilename = dlgResult
    if newParamsFilename is None: # keep going, but don't save
        saveParams = False
    else:
        toFile(newParamsFilename, params) # save it!

# ========================== #
# ===== SET UP LOGGING ===== #
# ========================== # didn't change
scriptName = os.path.basename(__file__)
scriptName = os.path.splitext(scriptName)[0] #% remove extension
try: # try to get a previous parameters file
    expInfo = fromFile('%s-lastExpInfo.psydat'%scriptName)
    expInfo['session'] +=1 # automatically increment session number
    expInfo['paramsFile'] = [expInfo['paramsFile'],'Load...']
    expInfo['LHeat'] = 34.5
    expInfo['MHeat'] = 35.5
    expInfo['HHeat'] = 36.5
except: # if not there then use a default set
    expInfo = {
        'subject':'1', 
        'session': 1, 
        'LHeat': '34.5',
        'MHeat': '35.5',
        'HHeat': '36.5',
        'skipPrompts':False, 
        'paramsFile':['DEFAULT','Load...']}
# overwrite params struct if you just saved a new parameter set
if saveParams:
    expInfo['paramsFile'] = [newParamsFilename,'Load...']

#present a dialogue to change select params
dlg = gui.DlgFromDict(expInfo, title=scriptName, order=['subject','session','LHeat','MHeat','HHeat','skipPrompts','paramsFile'])
if not dlg.OK:
    core.quit() # the user hit cancel, so exit

# find parameter file
if expInfo['paramsFile'] == 'Load...':
    dlgResult = gui.fileOpenDlg(prompt='Select parameters file',tryFilePath=os.getcwd(),
        allowed="PICKLE files (.psydat)|.psydat|All files (.*)|")
    expInfo['paramsFile'] = dlgResult[0]
# load parameter file
if expInfo['paramsFile'] not in ['DEFAULT', None]: # otherwise, just use defaults.
    # load params file
    params = fromFile(expInfo['paramsFile'])


# transfer skipPrompts from expInfo (gui input) to params (logged parameters)
params['skipPrompts'] = expInfo['skipPrompts']

# print params to Output
print 'params = {'
for key in sorted(params.keys()):
    print "   '%s': %s"%(key,params[key]) # print each value as-is (no quotes)
print '}'
    
# save experimental info
toFile('%s-lastExpInfo.psydat'%scriptName, expInfo)#save params to file for next time

#make a log file to save parameter/event  data
dateStr = ts.strftime("%b_%d_%H%M", ts.localtime()) # add the current time
filename = '%s-%s-%d-%s'%(scriptName,expInfo['subject'], expInfo['session'], dateStr) # log filename
logging.LogFile((filename+'.log'), level=logging.INFO)#, mode='w') # w=overwrite
logging.log(level=logging.INFO, msg='---START PARAMETERS---')
logging.log(level=logging.INFO, msg='filename: %s'%filename)
logging.log(level=logging.INFO, msg='subject: %s'%expInfo['subject'])
logging.log(level=logging.INFO, msg='session: %s'%expInfo['session'])
logging.log(level=logging.INFO, msg='LHeat: %s'%expInfo['LHeat'])
logging.log(level=logging.INFO, msg='MHeat: %s'%expInfo['MHeat'])
logging.log(level=logging.INFO, msg='HHeat: %s'%expInfo['HHeat'])
logging.log(level=logging.INFO, msg='date: %s'%dateStr)
# log everything in the params struct
for key in sorted(params.keys()): # in alphabetical order
    logging.log(level=logging.INFO, msg='%s: %s'%(key,params[key])) # log each parameter

logging.log(level=logging.INFO, msg='---END PARAMETERS---')


# ========================== #
# ===== GET SCREEN RES ===== #
# ========================== # can't use AppKit on windows

# kluge for secondary monitor
#if params['fullScreen']: 
#    screens = AppKit.NSScreen.screens()
#    screenRes = (int(screens[params['screenToShow']].frame().size.width), int(screens[params['screenToShow']].frame().size.height))
#    screenRes = [1920, 1200]
#    if params['screenToShow']>0:
#        params['fullScreen'] = False
#else:
#    screenRes = [800,600]

screenRes = [1920,1080]


# ========================== #
# == SET UP PARALLEL PORT == #
# ========================== #
#
#if params['sendPortEvents']:
#    from psychopy import parallel
#    port = parallel.ParallelPort(address=params['portAddress'])
#    port.setData(0) # initialize to all zeros
#else:
#    print("Parallel port not used.")


# ========================== #
# ===== SET UP STIMULI ===== #
# ========================== #
from psychopy import visual

# Initialize deadline for displaying next frame
tNextFlip = [0.0] # put in a list to make it mutable (weird quirk of python variables) 

#create clocks and window
globalClock = core.Clock()#to keep track of time
win = visual.Window(screenRes, fullscr=params['fullScreen'], allowGUI=False, monitor='testMonitor', screen=params['screenToShow'], units='deg', name='win',color=params['screenColor'],colorSpace='rgb255')
# create fixation cross
fCS = params['fixCrossSize'] # size (for brevity)
fCP = params['fixCrossPos'] # position (for brevity)
fixation = visual.ShapeStim(win,lineColor='#000000',lineWidth=3.0,vertices=((fCP[0]-fCS/2,fCP[1]),(fCP[0]+fCS/2,fCP[1]),(fCP[0],fCP[1]),(fCP[0],fCP[1]+fCS/2),(fCP[0],fCP[1]-fCS/2)),units='pix',closeShape=False,name='fixCross');
# create text stimuli
message1 = visual.TextStim(win, pos=[0,+.5], wrapWidth=1.5, color='#000000', alignHoriz='center', name='topMsg', text="aaa",units='norm')
message2 = visual.TextStim(win, pos=[0,-.5], wrapWidth=1.5, color='#000000', alignHoriz='center', name='bottomMsg', text="bbb",units='norm')

# load VAS Qs & options
[questions,options,answers] = BasicPromptTools.ParseQuestionFile(params['questionFile'])
print('%d questions loaded from %s'%(len(questions),params['questionFile']))

# get stimulus files
allImages = glob.glob(params['imageDir']+"*"+params['imageSuffix']) # get all files in <imageDir> that end in .<imageSuffix>.
# put in alpha order
allImages.sort()
print('%d images loaded from %s'%(len(allImages),params['imageDir']))
# make sure there are enough images - should always be 20
if len(allImages)< 20:
    raise ValueError("# images found in '%s' (%d) is less than # trials (%d)!"%(params['imageDir'],len(allImages),params['nTrials']))

# slice allImages into different colors 
green = allImages[0:5]
yellow = allImages [5:10]
red = allImages [10:15]
black = allImages [15:20]
color_list = [1,2,3,4,1,2,3,4] #1-green, 2-yellow, 3-red, 4-black, ensure each color is presented twice at random per block

painISI = [6,8,12,14,6,8,12,14]
random.shuffle(painISI)

# create stimImage
stimImage = visual.ImageStim(win, pos=[0,0], name='ImageStimulus',image=black[0], units='pix')

# read questions and answers from text files
[topPrompts,bottomPrompts] = BasicPromptTools.ParsePromptFile(params['promptDir']+params['promptFile'])
print('%d prompts loaded from %s'%(len(topPrompts),params['promptFile']))

[questions_vas1,options_vas1,answers_vas1] = BasicPromptTools.ParseQuestionFile(params['moodQuestionFile1'])
print('%d questions loaded from %s'%(len(questions_vas1),params['moodQuestionFile1']))

[questions_vas2,options_vas2,answers_vas2] = BasicPromptTools.ParseQuestionFile(params['moodQuestionFile2'])
print('%d questions loaded from %s'%(len(questions_vas2),params['moodQuestionFile2']))

[questions_vas3,options_vas3,answers_vas3] = BasicPromptTools.ParseQuestionFile(params['moodQuestionFile3'])
print('%d questions loaded from %s'%(len(questions_vas3),params['moodQuestionFile3']))

avgFile = open("anxScaleAvgs.csv", "w+")
avgFile.write('filename: %s\n'%filename)
avgFile.write('subject: %s\n'%expInfo['subject'])
avgFile.write('session: %s\n'%expInfo['session'])
avgFile.write('date: %s\n\n'%dateStr)


#allCodes = list(range(1,len(allImages)+1))

# ============================ #
# ======= SUBFUNCTIONS ======= #
# ============================ #

# increment time of next window flip
def AddToFlipTime(tIncrement=1.0):
    tNextFlip[0] += tIncrement

# flip window as soon as possible
def SetFlipTimeToNow():
    tNextFlip[0] = globalClock.getTime()
    
def WaitForFlipTime():
    while (globalClock.getTime()<tNextFlip[0]):
        keyList = event.getKeys()
        # Check for escape characters
        for key in keyList:
            if key in ['q','escape']:
                CoolDown()

def ShowImage(imageName, stimDur=float('Inf')):
    # display info to experimenter
    print('Showing Stimulus %s'%imageName) 
    
    # Set image
    stimImage.setImage(imageName)
    # Wait until it's time to display
    while (globalClock.getTime()<tNextFlip[0]):
        win.flip() # to update ratingScale
    # Start drawing stim image every frame
    stimImage.autoDraw = True; 
    ratingScale.autoDraw = False; # to put it on top?
    ratingScale.autoDraw = True; # to put it on top?
    
    # log & flip window to display image
    win.logOnFlip(level=logging.EXP, msg='Display %s'%imageName)
    win.flip()
    tStimStart = globalClock.getTime() # record time when window flipped
    # set up next win flip time after this one
    AddToFlipTime(stimDur) # add to tNextFlip[0]
    
    # Flush the key buffer and mouse movements
    event.clearEvents()
    # Wait for relevant key press or 'stimDur' seconds
    while (globalClock.getTime()<tNextFlip[0]): # until it's time for the next frame
        win.flip() # to update rating scale
        # get new keys
        newKeys = event.getKeys(keyList=['q','escape'],timeStamped=globalClock)
        # check each keypress for escape keys
        if len(newKeys)>0:
            for thisKey in newKeys: 
                if thisKey[0] in ['q','escape']: # escape keys
                    CoolDown() # exit gracefully
    
    # Stop drawing stim image every frame
    stimImage.autoDraw = False;
    
    # Get stimulus time
    tStim = globalClock.getTime()-tStimStart
    print('Stim %s: %.3f seconds'%(imageName,tStim))
    
    # Display the fixation cross
    if params['ISI']>0:# if there should be a fixation cross
        #fixation.draw() # draw it
        #win.logOnFlip(level=logging.EXP, msg='Display Fixation')
        win.flip()
        
    return tStimStart

# Send parallel port event
#def SetPortData(data):
#    if params['sendPortEvents']:
#        logging.log(level=logging.EXP,msg='set port %s to %d'%(format(params['portAddress'],'#04x'),data))
#        port.setData(data)
#    else:
#        print('Port event: %d'%data)


# Handle end of a session

def RunVas(questions,options,pos=(0.,-0.25),scaleTextPos=[0.,0.25],questionDur=params['questionDur'],isEndedByKeypress=params['questionSelectAdvances'],name='Vas'):
    
    # wait until it's time
    WaitForFlipTime()
    
    # Show questions and options
    [rating,decisionTime,choiceHistory] = RatingScales.ShowVAS(questions,options, win, questionDur=questionDur, \
        upKey=params['questionUpKey'], downKey=params['questionDownKey'], selectKey=params['questionSelectKey'],\
        isEndedByKeypress=isEndedByKeypress, textColor=params['vasTextColor'], name=name, pos=pos,\
        scaleTextPos=scaleTextPos, labelYPos=pos[1]-params['vasLabelYDist'], markerSize=params['vasMarkerSize'],\
        tickHeight=1,tickLabelWidth = 0.9)
    
    # Update next stim time
    if isEndedByKeypress:
        SetFlipTimeToNow() # no duration specified, so timing creep isn't an issue
    else:
        AddToFlipTime(questionDur*len(questions)) # add question duration * # of questions

def RunMoodVas(questions,options,name='MoodVas'):
    
    # Wait until it's time
    WaitForFlipTime()

    
    # display pre-VAS prompt
    if not params['skipPrompts']:
        BasicPromptTools.RunPrompts([params['PreVasMsg']],["Press any button to continue."],win,message1,message2)
    
    # Display this VAS
    #win.callOnFlip(SetPortData,data=params['codeVas'])
    RunVas(questions,options,questionDur=float("inf"), isEndedByKeypress=True,name=name)
    
    
    
def CoolDown():
    
    # Stop drawing ratingScale (if it exists)
    try:
        ratingScale.autoDraw = False
    except:
        print('ratingScale does not exist.')
    # Stop drawing stimImage (if it exists)
    try:
        stimImage.autoDraw = False
    except:
        print('stimImage does not exist.')


    # display cool-down message
    message1.setText("That's the end! ")
    message2.setText("Press 'q' or 'escape' to end the session.")
    win.logOnFlip(level=logging.EXP, msg='Display TheEnd')
    message1.draw()
    message2.draw()
    win.flip()
    thisKey = event.waitKeys(keyList=['q','escape'])
    
    # exit
    core.quit()

#handle transition between blocks
def BetweenBlock():
    AddToFlipTime(180)
    message1.setText("This concludes the current block. Please wait for further instruction before continuing.")
    message2.setText("Press SPACE to continue.")
    win.logOnFlip(level=logging.EXP, msg='BetweenBlock')
    message1.draw()
    message2.draw()
    win.flip()
    thisKey = event.waitKeys(keyList=['space']) # use space bar to avoid accidental advancing
    if thisKey :
        tNextFlip[0] = globalClock.getTime() + 2.0

#creates a new random color order to ensure each color is presented exactly twice at random within each block
def colorOrder():
    #randomize order
    color_list = [1,2,3,4,1,2,3,4] #1-green, 2-yellow, 3-red, 4-black, ensure each color is presented twice at random
    newImages = []
    random.shuffle(color_list)
    for i in color_list:
        if i == 1 :
            newImages = newImages + green
        elif i == 2 :
            newImages = newImages + yellow
        elif i == 3 :
            newImages = newImages + red
        else :
            newImages = newImages + black
    # initialize main image stimulus
    stimImage.setImage(newImages[0]) # initialize with first image
    return newImages
    
def integrateData(ratingScale, arrayLength, iStim, avgArray, block):
    thisHistory = ratingScale.getHistory()[arrayLength - 1:]
    logging.log(level=logging.DATA,msg='RatingScale %s: history=%s'%(finalImages[iStim],thisHistory))
    if len(avgArray) == 0:
        avgFile.write('%s,' %(block + 1))
        avgFile.write(finalImages[iStim][9:-6] + ',')
    x = [a[1] for a in thisHistory]
    y = [a[0] for a in thisHistory]
    if len(thisHistory) == 1:
        avgRate = y[0]
    else :
        avgRate = trapz(y,x)/(x[-1] - x[0])
    avgArray.append(avgRate)
    logging.log(level=logging.DATA,msg='RatingScale %s: avgRate=%s'%(finalImages[iStim],avgRate))
    avgFile.write('%.3f,' % (avgRate))
    if len(avgArray) == 5 :
        avgFile.write(str(sum(avgArray) / float(len(avgArray))) + '\n')
        avgArray *= 0
    arrayLength = len(ratingScale.getHistory())
    return arrayLength

def EveryHalf(ratingScale):
    x = [a[1] for a in ratingScale.getHistory()]
    y = [a[0] for a in ratingScale.getHistory()]
    countTime = round(x[-1])
    for b in np.arange(0, countTime, 0.5):
        avgFile.write(str(b) + ',')
    avgFile.write('\n')
    i = 0
    for a in range(len(x)):
        if x[a] == i:
            avgFile.write(str(y[a]) + ',')
            i = i + 0.5
        elif x[a] > i:
            missed = math.ceil((x[a] - i)/0.5)
            avgFile.write((str(y[a-1]) + ',') * missed)
            i = i + 0.5 * missed
    avgFile.write('\n\n')

def MakePersistentVAS(question, options, win, name='Question', textColor='black',pos=(0.,0.),stepSize=1., scaleTextPos=[0.,0.45], 
                  labelYPos=-0.27648, markerSize=0.1, tickHeight=0.0, tickLabelWidth=0.0, downKey='down',upKey='up',selectKey=[],hideMouse=True):
    # Make triangle
    markerStim = visual.ShapeStim(win,lineColor=textColor,fillColor=textColor,vertices=((-markerSize/2.,markerSize*np.sqrt(5./4.)),(markerSize/2.,markerSize*np.sqrt(5./4.)),(0,0)),units='norm',closeShape=True,name='triangle');
    
    tickMarks = np.linspace(0,100,len(options)).tolist()
    if tickLabelWidth==0.0: # if default value, determine automatically to fit all tick mark labels
      tickWrapWidth = (tickMarks[1]-tickMarks[0])*0.9/100 # *.9 for extra space, /100 for norm units
    else: # use user-specified value
      tickWrapWidth = tickLabelWidth;
    
    # Create ratingScale
    ratingScale = visual.RatingScale(win, scale=question, \
      low=0., high=100., markerStart=50., precision=1., labels=options, tickMarks=tickMarks, tickHeight=tickHeight, \
      marker=markerStim, markerColor=textColor, markerExpansion=1, singleClick=False, disappear=False, \
      textSize=0.8, textColor=textColor, textFont='Helvetica Bold', showValue=False, \
      showAccept=False, acceptKeys=selectKey, acceptPreText='key, click', acceptText='accept?', acceptSize=1.0, \
      leftKeys=downKey, rightKeys=upKey, respKeys=(), lineColor=textColor, skipKeys=[], \
      mouseOnly=False, noMouse=hideMouse, size=1.0, stretch=1.5, pos=pos, minTime=0.4, maxTime=np.inf, \
      flipVert=False, depth=0, name=name, autoLog=True)
    # Fix text wrapWidth
    for iLabel in range(len(ratingScale.labels)):
      ratingScale.labels[iLabel].wrapWidth = tickWrapWidth
      ratingScale.labels[iLabel].pos = (ratingScale.labels[iLabel].pos[0],labelYPos)
      ratingScale.labels[iLabel].alignHoriz = 'center'
    # Move main text
    ratingScale.scaleDescription.pos = scaleTextPos
    
    # Make it persistent by setting autoDraw to True
    ratingScale.autoDraw = True;
    
    # Display until time runs out (or key is pressed, if specified)
    win.logOnFlip(level=logging.EXP, msg='Display %s'%name)
    win.flip()
    
    return ratingScale

# =========================== #
# ======= RUN PROMPTS ======= #
# =========================== #
def RunPrompts():
    # display prompts
    if not params['skipPrompts']:
        BasicPromptTools.RunPrompts(topPrompts,bottomPrompts,win,message1,message2)
        thisKey = event.waitKeys() # use if need to repeat instructions
        if thisKey[0] == 'r':
            RunPrompts()
        tNextFlip[0] = globalClock.getTime() + 5.0


# =========================== #
# ===== MAIN EXPERIMENT ===== #
# =========================== #

RunMoodVas(questions_vas1,options_vas1,name='PreVAS')


RunPrompts()

# log experiment start and set up
logging.log(level=logging.EXP, msg='---START EXPERIMENT---')
tStimVec = np.zeros(params['nTrials'])

# Randomize image order for first block
finalImages = colorOrder()

avgArray = []
avgFile.write('Block,Color,Circ1,Circ2,Circ3,Circ4,Full,Avg\n')

# display images
for block in range(0, params['nBlocks']):
    if block == 3:
        RunMoodVas(questions_vas2,options_vas2,name='MidRun')
        AddToFlipTime(180)
        BasicPromptTools.RunPrompts(["Thank you for your responses."],["Press the space bar to continue."],win,message1,message2)
        thisKey = event.waitKeys(keyList=['space']) # use space bar to avoid accidental advancing
        if thisKey :
            tNextFlip[0] = globalClock.getTime() + 5.0
    logging.log(level=logging.EXP,msg='==== START BLOCK %d/%d ===='%(block+1,params['nBlocks']))
    # wait before first stimulus
    fixation.autoDraw = True # Start drawing fixation cross
    #win.callOnFlip(SetPortData,data=params['codeBaseline'])
    win.logOnFlip(level=logging.EXP, msg='Display Fixation')
    # Show questions and options
    ratingScale = MakePersistentVAS(questions[0], options[0], win,name='anxScale',pos=(0.,-0.70),scaleTextPos=[0.,-0.50], 
                                    textColor=params['textColor'],stepSize=params['vasStepSize'],
                                    labelYPos=-0.75, markerSize=0.1, tickHeight=0.0, tickLabelWidth=0.0, 
                                    downKey=params['questionDownKey'],upKey=params['questionUpKey'],hideMouse=False)
                                    
# Wait until it's time to display first stimulus
    while (globalClock.getTime()<tNextFlip[0]):
        win.flip() # to update ratingScale
    fixation.autoDraw = False # stop  drawing fixation cross
    arrayLength = 1
    painITI = 0
              
    for iStim in range(0,params['nTrials']):
        if ((iStim + 1) % 5 == 0):
            #portCode = len(allCodes)*(blockOrder[block]) + allCodes[iStim]
            #win.callOnFlip(SetPortData,data=portCode)
            tStimStart = ShowImage(imageName=finalImages[iStim],stimDur=params['painDur'])
            arrayLength = integrateData(ratingScale, arrayLength, iStim, avgArray, block)
            if iStim < params['nTrials']:
                # pause
                AddToFlipTime(painISI[painITI])
                painITI += 1
                fixation.autoDraw = True

        else:
            tStimStart = ShowImage(imageName=finalImages[iStim],stimDur=params['stimDur'])
            arrayLength = integrateData(ratingScale, arrayLength, iStim, avgArray, block)
            if iStim < params['nTrials']:
                # pause
                AddToFlipTime(params['ISI'])
        # save stimulus time
        tStimVec[iStim] = tStimStart
    
    # stop autoDraw
    ratingScale.autoDraw = False
    
    # Log anxiety responses manually
    logging.log(level=logging.DATA,msg='RatingScale %s: history=%s'%(ratingScale.name,ratingScale.getHistory()))
    
    # Randomize order of colors for next block
    if block < (params['nBlocks']-1):
        BetweenBlock()
        finalImages = colorOrder()
    logging.log(level=logging.EXP,msg='==== END BLOCK %d/%d ===='%(block+1,params['nBlocks']))
    avgFile.write('\n')
    EveryHalf(ratingScale)

RunMoodVas(questions_vas3,options_vas3,name='PostRun')


# Log end of experiment
logging.log(level=logging.EXP, msg='--- END EXPERIMENT ---')
avgFile.close()

# exit experiment
CoolDown()
