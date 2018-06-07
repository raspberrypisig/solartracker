#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Initial draft solar reflector tracking code using photo resistors on Raspberry Pi
# NB- Must be used with GPIO 0.3.1a or later as earlier verions are not fast enough!

# So what's all this then?
# This code is being developed to control an array of solar reflectors to heat
# a home with low cost components, so making it economically appealing enough
# to be adopted an a large scale. The system may also be used for cooling with
# a simple condensor loop. When not used for heating or cooling for any decent
# duration the array should track the sun or at least be parked in a position
# to reflect heat back to the sky. Once adopted on a large scale besides saving
# vast amounts of CO2 emissions this extra heat reflected away from the earth
# should play a significant role in combatting climate change.

# Great, where's is at now?
# Currently this is the first software to fully autonomosly control a reflector,
# by simply plugging in the reflector and collector (ring of LDRs / PRs / photo
# resistors) and turning it on, it will search until it finds the sun and track
# it. All other known systems either require complex setup variables on start up
# (as in large scale solar power plants) or user intervention to locate the sun
# before starting tracking, or after the sun disapears behind clouds. The later
# just being used with a single reflector and similar sensor to this system's by
# some home hobbiests. See https://en.wikipedia.org/wiki/Heliostat for more info

# What's next?
# Use Baysian or other analysis to as accurately as possible control a reflector
# to track the sun. Then multiple reflectors can be added and manouvered in the
# same way. Later add multiple sensor capability and focusing to enable cooling
# of buildings, and with reflective tubes (as used for air conditioning) enable
# direct heating of water tank or even make cooking possibe! Also pole forecast
# to pre heat a home for cool nights, to be ported to android / ios for control
# by phone or tablet. The rest of this software should finally be ported to C++
# or micro python to run on ATmega (android type) chips for mass production.

# TODO-
# test- store calibration array and use when skipping or no sun, like cat5 cable type
# test- get sun from start position if located when calibrating (common to start on sun)
# do changemod once on startup then show log lines for debug instead of error
# move randomly between sensor calibration and health check, nb colides with axis
# update box seek to 4 corners and enable user input, and offer bolInterweave to orientate
# not seek when sun in, sleep at night etc
# when found sun on 'SeekSunIn' get min width and hight of sun and box search...
# around that until outside of sun, taking average positions when sensors see sun...
# to later use to calculate directions of motors in relation to movement on sensor.
# autoseeking stop, centre and verify coordinates, storing candidates
# recheck automatically if cable connected part way through sensor check
# use PWM on PR capacitor charging input?
# ad vertical and horizontal scrolling menus
# fix segmentation faults without try catch (max point 2/3 box 6 level 4)


# for release to calculate position of sun from time loose pyephem and use...
# https://en.wikipedia.org/wiki/Position_of_the_Sun
#
# Ecliptic coordinates (orbital plane):
# n is number of days (positive or negative) since Greenwich noon, 2000-1-1
# from the julian date that's:
# n = JD - 2451545
#
# mean longitude of the sun (corrected for aberration)
# L = 280.460deg + 0.9856474deg n
#
# mean anomaly of sun
# g = 357.528deg + 0.9856003deg n
#
# use modulus % 360 for L and g
#
# longitude of sun (ecliptic latitude of sun B is 0 - never exceeds 0.00033deg)
# y = L + (1.915deg * sin( g )) + (0.020deg * sin( 2 g ))
#
# obliquity of ecleptic
# e = 23.439deg - 0.0000004n
#
# Equatorial coordinates (equatorial plane):
# calculated from ecliptic variables above and e (the obliquity of the ecliptic)
#
# obliquity of ecleptic (angle between earth's rotational and orbital axis)
# e = 23.439deg - 0.0000004n
#
# a is ascension
# a = arctan((cos e) * (tan y))
# ... or in software...
# a = atan2((cos e) * (sin y), (cos y))
#
# d = arcsin((sin e) * (sin y))
# or aprox...
# d = arcsin((sin -23.44deg) * (sin y))
# d = -23.44deg * cos((360/365) * (N + 10))... 2deg err
# (N=0 at midnight Universal Time (UT) as January 1 begins (i.e. the days part of the ordinal date -1). The number 10, in (N+10), is the approximate number of days after the December solstice to January 1
# d = arcsin(sin(-23.44deg) * cos( ((360/365.24) * (N + 10)) + ( (360deg/pi) * 0.0167 * sin((360/365.24) * (N - 2)) ))... 2deg err
# d = -arcsin(0.39779 * cos( (0.98565 * (N + 10)) + (1.914deg * sin(0.98565 * (N - 2))) ))... 0.2deg err, 0.03deg err if 10 in N + 10 is adjusted to days after solstice from December 22
# also 0.1deg error morning / evening due to atmoshperic refraction
# for comparison sun is 0.5deg wide
#
# then make fuctions to do
# d = -23.44deg * cos((360/365) * (N + 10))... 2deg err
# a = atan2((cos e) * (sin y), (cos y))
# then get altazimuth by...
# use http://sciencing.com/calculate-solar-time-8612288.html to get 'local solar time'
# then get Solar zenith angle https://en.wikipedia.org/wiki/Solar_zenith_angle
# then get Solar azimuth angle https://en.wikipedia.org/wiki/Solar_azimuth_angle
# ie...
#def solarTimeMeridia():
#def solarTime():
#... etc

### set constants ###
# compilation
DEBUG       = 1      # 1 for debug mode, 0 for release
#TIME_RC     = True   # measure photo resistor reading by time not loop counter
TIME_RC     = False  # NB- FAILS! always gives time 0.00012 to 00015 sun or not
AUTO_ZOOM   = False  # true to handle zoom automatically
SHOW_GRAPHS = False  # true to show graphs (very slow, needs matplotlib too)
#SHOW_GRAPHS = Trues
USE_EPHEM   = True   # uses ephemeral astronomical data if set
DO_MOON_TOO = True   # tracks moon at night instead of sun if true
AUTO_START  = True   # true if starting automatically on repower (requires setup)
SOUND_ON    = True   # true will sound beeps, false is silent
#SOUND_ON    = False
# done below automagically now
#COL_CAT5_X  = False  # true if cat 5 cable for collector is crossed
#COL_CAT5_X  = True
MOT_X_REV   = False  # true if motor 1 for turning is reveresed
#MOT_X_REV   = True
MOT_Y_REV   = False  # true if motor 2 for tilting is reveresed
#MOT_Y_REV   = True
USE_OK_BTN  = True   # true to use OK button (L+R together or seperate OK button)
LR_OK_BTNS  = True   # true to use left and right buttons pressed together as OK
TRACK_POS   = True   # true to count stepper motor steps, required for s/w limits
SW_LIMITS   = True   # true to enable software limit switches, stops motor overrun
#SW_LIMITS   = False
LAZY_TRACK  = False  # true prevents software constantly writing position to file
LOG_DATA    = True   # true to log all data to periodic files
PR_CUTOFF   = 100    # min PR val to start autotracking (ie when sun is out), full ambient sun is below 50, but can track around 100 through light cloud
#PR_CUTOFF   = 2000    # crazy high for testing in dark
CALOBRATE   = True   # calibrate PRs to handle old sensors or ambient light
RECAL_ERR   = 0.1    # forces recalibration if differences above this threshold
#RECAL_ERR   = 0.15   # needed to pass calibration at night when calibration is crap
#RECAL_ERR   = 0.05   # only passed occasionaly when really bright
PI_CONST = 3.14159   # maths pi constant, use import math, math.pi when need maths module

# general
CONFIG_FILE = "vinvar.json"

# current version
CODE_VERSION = 0.15

# previous version additions
# 0.1  - initial for john with lcd and stepper functionality only
# 0.11 - JSON config file storage and mid tracking halt and options
# 0.12 - non verbose text mode and scroll back and forth through setup
# 0.13 - self tests PRs and auto straight / crossover cable select
# 0.14 - global logging and autoseeking sun, fully autonomous :D
# 0.15 - TODO- PR location direction and use with auto tracking

# control
MAX_RC_TIME    = 100000 # max PR reading, prevents hanging on broken circuit
PWM_MAX_HZ     = 200    # max steps per second reflector moves (ie slew rate)
#PWM_MAX_HZ     = 2000   # 2k Hz max clock impulses per second for motor control
#PWM_MAX_HZ     = 800    # jumped badly
#PWM_MAX_HZ     = 500    # REALLY jittery
#PWM_MAX_HZ     = 300    # nearly nothing
#PWM_MAX_HZ     = 450    # nothing
#PWM_MAX_HZ     = 400    # works fine usually
#PWM_MAX_HZ     = 350    # works like a charm (john just soldered something though)
#PWM_MAX_HZ     = 5      # fine now
#PWM_MAX_HZ     = 1      # just 1 Hz max pluses a second for testing motors
PWM_TRACK_HZ   = 2      # rate of steps per second that reflector tracks sun
PWM_DUTY_CYCLE = 50     # percentage ratio of hi to low signal in each PWM pulse
#PWM_DUTY_CYCLE = 1

# set min thresholds to act on for various motors (smaller is more sensitive)
# (amounts)
# X_ACT_MIN = 50
# Y_ACT_MIN = 50
# Z_ACT_MIN = 10
# (differences)
#X_ACT_MIN = 0.5
#Y_ACT_MIN = 0.5
#Z_ACT_MIN = 0.5

# set all together
#ALL_ACT_MIN = 0.2    # 0.2 works great in the mornings, but careers off in the day:
ALL_ACT_MIN = 0.35
#ALL_ACT_MIN = 0.5    # 0.5 works in day but not so well in the mornings:

X_ACT_MIN = ALL_ACT_MIN
Y_ACT_MIN = ALL_ACT_MIN
Z_ACT_MIN = ALL_ACT_MIN


# import external code
import RPi.GPIO as GPIO    # raspberry pi GPIO handling
import time
import os

# only use astronomical data if set to
if USE_EPHEM:
        import ephem               # for solar angles: 'sudo apt-get install python-dev' then 'sudo pip install pyephem'
        import datetime            # for UTC time required by ephem

# only import matplot lib if showing graphs as it's big n slow
if SHOW_GRAPHS:
	import matplotlib.pyplot as plt

# for storing vars, pickle is usual for python, but json easier to port to c++
#import pickle	# usual for python storing and retreiving variables to a file
#import cPickle as pickle	# faster storing and retreiving variables
import json	# similar to pickle, easier porting to c++

# Make it work for Python 2+3 and with Unicode
import io
#from builtins import chr       # to make code python 2 and 3 compatable, but breaks 2 :(
try:
	to_unicode = unicode
except NameError:
	to_unicode = str

# set to Broadcom chip pin numbering
GPIO.setmode( GPIO.BCM )

# import LCD wrapper package
import vinlcd as Lcd


### set pin numbers ###
# buttons
PIN_BTN_LEFT  = 5
PIN_BTN_RIGHT = 19
PIN_BTN_DOWN  = 13
PIN_BTN_UP    = 6
#PIN_BTN_OK    = X

# array for processing
buttons = [PIN_BTN_UP, PIN_BTN_RIGHT, PIN_BTN_DOWN, PIN_BTN_LEFT]
#buttons = [PIN_BTN_UP, PIN_BTN_RIGHT, PIN_BTN_DOWN, PIN_BTN_LEFT, PIN_BTN_OK]

# array positions
aBTN_UP = 0
aBTN_RIGHT = 1
aBTN_DOWN = 2
aBTN_LEFT = 3
aBTN_OK = 4

# photo resistors
# PIN_PR_LEFT   = 19
# PIN_PR_RIGHT  = 26
# PIN_PR_UP     = 20
# PIN_PR_DOWN   = 21
# PIN_PR_INNER  = 16
PIN_PR_LEFT   = 16
PIN_PR_RIGHT  = 12
PIN_PR_UP     = 7
PIN_PR_DOWN   = 20
PIN_PR_INNER  = 21
PIN_PR_DEMAND = 26
# PIN_PR_Ref    = 25	# TODO- add
# PIN_PR_Safe   = 12	# TODO- add

# arrays for processing
PRs = [PIN_PR_UP, PIN_PR_RIGHT, PIN_PR_DOWN, PIN_PR_LEFT, PIN_PR_INNER, PIN_PR_DEMAND ]
PRvals = [None, None, None, None, None, None]   # values
##PRavgs = [0, 0, 0, 0, 0, 0]                     # averages
##PRdifs = [0, 0, 0, 0, 0, 0]                     # differences
###PRerrs = [None, None, None, None, None, None]   # average differences (using difs array for this now)
###PRadjs = [1, 1, 1, 1, 1, 1]                     # multipliers
##PRcals = [1, 1, 1, 1, 1, 1]                     # calibration variables
PRavgs = [0, 0, 0, 0, 0]                     # averages
PRdifs = [0, 0, 0, 0, 0]                     # differences
#PRerrs = [None, None, None, None, None]   # average differences (using difs array for this now)
#PRadjs = [1, 1, 1, 1, 1]                     # multipliers
PRcals = [1, 1, 1, 1, 1]                     # calibration variables
PRtime = None

# array positions
aPR_UP     = 0
aPR_RIGHT  = 1
aPR_DOWN   = 2
aPR_LEFT   = 3
aPR_INNER  = 4
aPR_DEMAND = 5

# swap crossed over lines if collector cat 5 cable is crossed
# NB: with current setup can sense automatically if Y+ is huge!
# - needs 6 capacitors though or will get 0 not max charge time
# done below now automagically
##if COL_CAT5_X:
##
##   # crossover orange/green and white line
##   intPrTemp = PIN_PR_DEMAND
##   PIN_PR_DEMAND = PIN_PR_UP
##   PIN_PR_UP = intPrTemp
##
##   # crossover plain orange/green line
##   intPrTemp = PIN_PR_INNER
##   PIN_PR_INNER = PIN_PR_LEFT
##   PIN_PR_LEFT = intPrTemp

# display
#PIN_LCD_RS = 14
#PIN_LCD_E  = 15
#PIN_LCD_D4 = 23
#PIN_LCD_D5 = 24
#PIN_LCD_D6 = 25
#PIN_LCD_D7 = 8

# motors, pump and valve
# PIN_X_MOTOR_N = 5
# PIN_X_MOTOR_P = 6
# PIN_Y_MOTOR_N = 8
# PIN_Y_MOTOR_P = 7
# PIN_VALVE     = 9
# PIN_PUMP      = 10
PIN_X_MOTOR_N = 17
PIN_X_MOTOR_P = 22
PIN_Y_MOTOR_N = 27
PIN_Y_MOTOR_P = 11
PIN_VALVE     = 10
PIN_PUMP      = 9

# display backlight
LCD_LED       = 4

# buzzer
PIN_BUZZER    = 18

### initialise GPIO pins ###
# set buttons as inputs
GPIO.setup( PIN_BTN_LEFT, GPIO.IN )
GPIO.setup( PIN_BTN_RIGHT, GPIO.IN )
GPIO.setup( PIN_BTN_DOWN, GPIO.IN )
GPIO.setup( PIN_BTN_UP, GPIO.IN )

# set motors, pump and valve as outputs
GPIO.setup( PIN_X_MOTOR_N, GPIO.OUT )
GPIO.setup( PIN_X_MOTOR_P, GPIO.OUT )
GPIO.setup( PIN_Y_MOTOR_N, GPIO.OUT )
GPIO.setup( PIN_Y_MOTOR_P, GPIO.OUT )
GPIO.setup( PIN_VALVE, GPIO.OUT )
GPIO.setup( PIN_PUMP, GPIO.OUT )

# set LCD backlight as output
GPIO.setup( LCD_LED, GPIO.OUT )

# set buzzer as output
GPIO.setup( PIN_BUZZER, GPIO.OUT )

# TODO- halt everything?
# GPIO.output( PIN_X_MOTOR_N, GPIO.LOW )
# GPIO.output( PIN_X_MOTOR_P, GPIO.LOW )
# GPIO.output( PIN_Y_MOTOR_N, GPIO.LOW )
# GPIO.output( PIN_Y_MOTOR_P, GPIO.LOW )
# GPIO.output( PIN_VALVE, GPIO.LOW )
# GPIO.output( PIN_PUMP, GPIO.LOW )


### initialise variables ###
# previous version run
#dblLastVsn = 0  # initialise to 0 so unknown always run

# modes
bolVerbose     = None   # display more help text (easier but slower) or less
bolDcMotors    = None   # send DC motor signals or stepper
bolTestOptions = False  # don't show test options by default

# zoom
zActCount  = 0	# number of actions (pumps + vavle opennings/zoom ins + outs)
zActFrom   = 0	# last zoom action carried out from
zActMaxDif = 0	# maximum zoom difference of this zoom action
zMaxDif    = 0	# last maximum achievable zoom difference

# configuration vars dictionary object
dicConfig = {}

# initialise coordinates if tracking
if TRACK_POS:
	#intPoss       = [0, 0]
	intPoss       = [None, None]
	intLastTimes  = [time.time(), time.time()]
	intSunAt      = [None, None]
	maxEphem      = [None, None]
	minEphem      = [None, None]
	maxSun        = [None, None]
	minSun        = [None, None]

# steps per full 360 rotation for each axis (should be pre-set in config file)
intStepsPerRotation = [None, None]

# stores scale and baseline for ephem to steps conversion for shadowing sun
intEphem2stepsRatio = [None, None]
intEphem2stepsBase  = [None, None]

# remembers current speeds of motors for smooth acc/decelearation
intLastSpeeds = [0, 0]

# set X,Y positions / limits to unset
#if SW_LIMITS:
#intLimits     = [0, 0]
intLimits     = [None, None]
# limits aprox X 10,000, Y 6,000 for john's 30cm newtonian test reflector

# initialise to no ephemeral data
#global ephemBody
ephemBody = None
ephemViewer = None

### main code and function definitions ###
# toggle comments on 2 lines below and near &
# to enable or dissable error handling. enable
# for release or may get segmentation errors
#try:
if True:
	#GPIO.setwarnings(False)

        # writes the given string to screen if debugging
        def vindebug( strDebug ):
                print( strDebug )


        # writes axis pos var into given file, returning true if set.
        # NB- fails if called from lower user than original creator!
        # https://stackoverflow.com/questions/5994840/how-to-change-the-user-and-group-permissions-for-a-directory-by-name
        def setAxisPos( intAxis, intPos ):
                bolPosSet = True      # return flag set true if axis position set

                # set axis position if tracking or using software limits
                if (TRACK_POS or SW_LIMITS) and not LAZY_TRACK:
                        try:
                                with open("axis" + str(intAxis) + "pos.txt", 'w') as f:

                                        # set file to anyone read and write
                                        try:
                                                os.chmod( "axis" + str(intAxis) + "pos.txt", 0o666 )
                                        except:
                                                vindebug( "axis" + str(intAxis) + " file belongs to other user so can't chmod" )

                                        # write position
                                        f.write('%d' % intPos)
                        except:
                                bolPosSet = False

                return bolPosSet

        # reads axis pos var into given varaible, returning true if set
        def getAxisPos( intAxis ):
                bolPosGot = False       # return flag set true if axis position retrieved

                # get axis position if tracking or using software limits
                if TRACK_POS or SW_LIMITS:
                        try:
                                # open file containing variable
                                file = open("axis" + str(intAxis) + "pos.txt", 'r')

                                # read contents from it
                                strTemp = file.readline()

                                # if given variable is ok read to axis
                                intPoss[intAxis - 1] = int(strTemp)

                                # close the file
                                file.close()

                                # set to return true as axis position retrieved
                                bolPosGot = True
                        except:
                                intPoss[intAxis - 1] = None

                return bolPosGot

	# global functions- should be outside 'try' if called in error handlers

		#######################
		#  general functions  #
		#######################

	### general ###
	# clean up before exiting
	def CleanUp( ):
		Lcd.Clear( )
		Lcd.ShowStr( "    Exiting,    ", 1 )
		Lcd.ShowStr( "  Please wait   ", 2 )

		# all stop
		SetMotor( 1, 0 )
		SetMotor( 2, 0 )
		SetZoom( 0 )

	### returns true if given var set to false, none or true returns false
	##        def IsFalse bolToTest:
	##
	##        # returns true if given var set to true, none or false returns false
	##        def IsTrue bolToTest:
	##                bolReturn = False       # initialise to return false
	##
	##                # only set to return true if not none or false
	##        	if not bolToTest is None:
	##                        if not bolToTest:
	##                                bolReturn = True
	##
	##                return bolReturn

		# stop PWM motor signals if using stepper motors
		# TODO finish defs above and use those if perform this logic elsewhere
		if not bolDcMotors is None:
			if not bolDcMotors:
				pwmMotorXp.stop( )
				pwmMotorYp.stop( )

		# show user program ended
		if AUTO_START:
			Lcd.Clear( )
			Lcd.ShowStr( "Exited. Repower ", 1 )
			Lcd.ShowStr( "   to restart.  ", 2 )
		else:
			Lcd.Clear( )
			Lcd.ShowStr( "Exited, restart ", 1 )
			Lcd.ShowStr( "  from console. ", 2 )

		# clear GPIOs
		GPIO.cleanup( ) # clear GPIOs for other processes
		vindebug( "GPIOs cleaned" )


	# update requested configuration variable and store in JSON config file
	def SetConfigVar( strName, varValue ):
		print( "Called SetConfigVar( " + str(strName) + ", " + str(varValue) + " )" )
		global dicConfig

		# set requested variable
		dicConfig[strName] = varValue

		# Write JSON config file
		with io.open(CONFIG_FILE, 'w', encoding='utf8') as outfile:
		    str_ = json.dumps(dicConfig,
				      indent=4, sort_keys=True,
				      separators=(',', ':'), ensure_ascii=False)
		    outfile.write(to_unicode(str_))

		# set file to anyone read and write
                try:
                        os.chmod( CONFIG_FILE, 0o666 )
                except:
                        vindebug( str(CONFIG_FILE) + " file belongs to other user so can't chmod" )

	# sets requested configuration variable to given value if doesn't yet exist
	def SetDefaultVar( strName, varValue ):
		global dicConfig

		# try getting requested variable
		try:
			tryValue = dicConfig[strName]

		# if failed (ie probably doesn't exist) set to given value
		except:
			SetConfigVar( strName, varValue )

	# gets configuration variables, returning true if found or false otherwise
	def getConfigVars( strVarFile ):
		global dicConfig

		# try getting configuration variables from JSON file
		#if True:       # for testing
		try:
			with open(strVarFile) as data_file:
				dicConfig = json.load(data_file)

			# if succeeded read in last version run
			#dblLastVsn = dicConfig["dblLastVsn"]
			#vindebug( "got previous config data version " + str(dicConfig["dblLastVsn"]) + ", current version " + str(CODE_VERSION) )
			vindebug( "got previous config data from file '" + str(strVarFile) + "'" )

		# if no file make empty dictionary object
		#else:       # for testing
		except:
			dicConfig = {}
			vindebug( "made new default config data" )

		# if no file make it with initial values
		##                dicConfig = {'dblVersion': str(CODE_VERSION),
		##                             'dblVsnWelcomed': 0,
		##                             'dblVsnDisclaimed': 0,
		##                             'bolVerbose': None,
		##                             'bolDcMotors': None,
		##                             'dtmFirstRun': time.strftime("%Y-%m-%d %H:%M:%S"),
		##                             'intRuns': 0
		##                }

			# NB- do nested / other data types like...
			##data = {'a list': [1, 42, 3.141, 1337, 'help', u''],
			##        'a string': 'bla',
			##        'another dict': {'foo': 'bar',
			##                         'key': 'value',
			##                         'the answer': 42}}

		# set default values (only updates if doesn't already exist ie for new variables on upgrade, or bizarely if called within function :/ )
		# NB- dicConfig.setdefault( 'dblVersion', CODE_VERSION ) etc doesn't work within function for some reason
		vindebug( "setting any unset variables to default" )
		SetDefaultVar( 'dblVersion', CODE_VERSION )
		SetDefaultVar( 'dblVsnWelcomed', 0 )
		SetDefaultVar( 'dblVsnDisclaimed', 0 )
		SetDefaultVar( 'bolVerbose', None )
		SetDefaultVar( 'bolDcMotors', None )
		SetDefaultVar( 'intStepsPerRotation', [None, None] )
		SetDefaultVar( 'bolUtpXed', None )
		SetDefaultVar( 'strCity', None )
		SetDefaultVar( 'fltLong', None )
		SetDefaultVar( 'fltLat', None )
		SetDefaultVar( 'fltElev', None )
		SetDefaultVar( 'minSun', [None, None] )
		SetDefaultVar( 'maxSun', [None, None] )
		SetDefaultVar( 'minEphem', [None, None] )
		SetDefaultVar( 'maxEphem', [None, None] )
		SetDefaultVar( 'dtmFirstRun', time.strftime("%Y-%m-%d %H:%M:%S") )
		SetDefaultVar( 'intRuns', 0 )

		# add software limits if processing
		if SW_LIMITS:
			SetDefaultVar( 'intLimits', [None, None] )


	# return user firendly time string in hours and mins since given time
	def GetTimeDif( dtmSince ):

		# get seconds elapsed since given time
		intSecsSince = time.time() - dtmSince

		# speed up for testing
		#intSecsSince *= 2555555

		# initialise elapsed string to seconds
		strTimeDif = str(intSecsSince) + " seconds"

		# if less than 2 mins show min
		if intSecsSince < 120:

			# if less than 1 min show first min
			if intSecsSince < 60:
				strTimeDif = "1st minute"
			else:
				strTimeDif = "2nd minute"

		# else if less than one hour show mins
		elif intSecsSince < (60 * 60):
			strTimeDif = str(int(intSecsSince / 60)) + " minutes"

		# else show hours and mins
		else:
			# get hours and minutes elapsed since given time
			intHoursSince = int(intSecsSince / (60 * 60))
			intMinsSince  = int((intSecsSince - (60 * 60 * intHoursSince)) / 60)

			# if less than 24 hours show hours and mins
			if intHoursSince < 24:
				strTimeDif = str(intHoursSince) + "hrs " + str(intMinsSince) + "mins"

			# else show days and time
			else:
				# get days elapsed
				intDaysSince = int(intHoursSince / 24)

				# set hours and minutes to remainders
				intHoursSince = int(intHoursSince - (intDaysSince * 24))
				#intMinsSince  = int((intSecsSince - (60 * 60 * intHoursSince)) / 60)

				# if less than 100 days show days and time elapsed
				if intDaysSince < 100:

					# initialise string to pad minutes if not double figures
					if intMinsSince < 10:
						strTimeDif = "0"
					else:
						strTimeDif = ""

					# get minutes elapsed
					strTimeDif = strTimeDif + str(intMinsSince)

					# add days and hours
					strTimeDif = str(intDaysSince) + "days " + str(intHoursSince) + ":" + strTimeDif

				# else show months and days
				else:
					# get months elapsed
					intMonthsSince = int(intDaysSince / 30)

					# if less than 24 months show months and days elapsed
					if intMonthsSince < 24:

						# set days to remainder
						intDaysSince = int(intDaysSince - (intMonthsSince * 30))

						# show months and days elapsed
						strTimeDif = str(intMonthsSince) + "mths " + str(intDaysSince) + "dys"

					# else show years and days
					else:
						# get years elapsed
						intYearsSince = int(intDaysSince / 365.25)

						# set days to remainder
						intDaysSince = int(intDaysSince - (intYearsSince * 365.25))

						# show years and days elapsed
						strTimeDif = str(intYearsSince) + "yrs " + str(intDaysSince) + "dys"

		# return time difference
		return strTimeDif


	#####################
	#  input functions  #
	#####################

	### LDR brightness ###

	# return calibrated photo resistor reading from capacitor charging time
	# and updates list. high number means darker, low number means lighter.
	def PRval( intPRpos ):

                MAX_READS = 2  # set max repeated PR reads if reading excesive
                intReads = 0

                # read a few times if value excesive
                while intReads < MAX_READS:

                        # first get PR value
                        fltCalPrVal = RCtime(PRs[intPRpos])
                        #vindebug( "read " + str(intReads) + " for PRval " + str(intPRpos) + " raw value " + str(fltCalPrVal) )

                        # calibrate if required and not demand PR
                        if CALOBRATE and (intPRpos < aPR_DEMAND):
                        	#vindebug( "callibrated raw value: " + str(fltCalPrVal) + ", by: " + str(PRcals[intPRpos]) )
                                fltCalPrVal = PRcals[intPRpos] * fltCalPrVal

                        # exit loop if not too different from the previous
                        # reading, else increase read count to check again
                        try:
                                #if abs((fltCalPrVal - PRvals[intPRpos]) / (PRvals[intPRpos] + 0.01)) < 0.2:
                                if abs((fltCalPrVal - PRvals[intPRpos]) / (PRvals[intPRpos] + 0.01)) < (0.2 + (0.0005 * fltCalPrVal)):  # added portion of value to error ratio as larger values vary more
                                        #print( "read " + str(intReads) + " done for PRval( " + str(intPRpos) + " ) = " + str(fltCalPrVal) )
                                        break
                                else:
                                        #print( "read " + str(intReads) + " outsided PRval( " + str(intPRpos) + " ) = " + str(fltCalPrVal) )
                                        intReads += 1
                                        BoxBeep( 0.05 )
                                        #print( "rechecking excesive reading " + str(fltCalPrVal) + " on PR " + str(intPRpos) + ", was " + str(PRvals[intPRpos]) )
                        except:
                                intReads += 1

                # add calibrated value to array
                PRvals[intPRpos] = fltCalPrVal

                # return calibrated PR value
		#print( "Called PRval( " + str(intPRpos) + " ) = " + str(fltCalPrVal) )
                return fltCalPrVal

	# return photo resistor light readings from capacitor charging time
	# - high number means darker, low number means lighter
	def RCtime( RCpin ):

		# zero counter and decharge capacitor before starting
		GPIO.setup( RCpin, GPIO.OUT )
		GPIO.output( RCpin, GPIO.LOW )
		time.sleep( 0.1 )

                # time RC if set to
                if TIME_RC:

                        # set variables for charging
                        reading = float( MAX_RC_TIME )
        		bolTime = False

                        # get charge start time
                        try:
                                dtmPRstart = time.process_time()
                        except:
                                dtmPRstart = time.time()

        		# start charging capacitor
                	GPIO.setup( RCpin, GPIO.IN )

                        # count loops done until charged.
        		# This takes under 1ms per cycle
                	# NB- see if for loop to MAX_RC_TIME with break when high quicker
                        while (GPIO.input(RCpin) == GPIO.LOW) and (reading < MAX_RC_TIME):
                                bolTime = True
                        #bolTime = False

        		# show value for debug
                	# (done together below now)
                        #if not SHOW_GRAPHS:
        		#	print( reading )

                        # get total charge time
                        try:
                                reading = time.process_time() - dtmPRstart
                        except:
                                reading = time.time() - dtmPRstart
                        print( "raw reading: " + str(reading) )

                        # make similar to previous format values, up to max
                        if reading < (MAX_RC_TIME / 100000):
                                reading = round(reading * float(100000), 2)
                                #reading = 1000 * reading
        			#print( "reading adjusted to " + str(reading) )
                                #reading = round(reading, 2)
                                print( "reading rounded to " + str(reading) )
                        else:
                                reading = float(MAX_RC_TIME)
                                print( "set to max" )

                # else time by loop counters
                else:

                        # initialise time counter
        		reading = 0

        		# start charging capacitor and count loops done until charged
                	GPIO.setup( RCpin, GPIO.IN )

        		# This takes about 1 millisecond per loop cycle
                	# NB- see if for loop to MAX_RC_TIME with break when high quicker
                        while (GPIO.input(RCpin) == GPIO.LOW) and (reading < MAX_RC_TIME):
                                reading += 1

		# return value
		return reading

	# returns time for photo resistor to charge capitcitor and returns value
	# as well as adding it to the given list for graphing display later
	def RCgraphTime( RCpin, pinValues ):

		# get reading
		reading = RCtime( RCpin )

		# add to given list and plot graph
		pinValues.append( reading )
		plt.plot( [i for i in range(intMainLoop)], pinValues )

		# return reading
		return reading


	### buttons ###

	# returns true if the given button GPIO was pressed
	# waiting the given time to debounce (0 if no need)
	#def btnPress(btnPin, msWait):

	# 		#initialise a previous input variable to 0 (assume button not pressed last)
	# 		prev_input = 0
	# 		while True:
	#
	# 		  #take a reading
	# 		  input = GPIO.input(17)
	# 		  #if the last reading was low and this one high, print
	# 		  if ((not prev_input) and input):
	# 		    print("Button pressed")
	# 		  #update previous input
	# 		  prev_input = input
	# 		  #slight pause to debounce
	# 		  time.sleep(0.05)

	# returns true if given button is pressed
	def BtnOn( intBtnToCheck ):
		bolOn = False

		# process if 0 or above
		if intBtnToCheck > -1:

			# return GPIO pin logic unless OK button, then check left and right pressed together
			if intBtnToCheck < aBTN_OK:
				bolOn = GPIO.input( buttons[intBtnToCheck] )

			elif LR_OK_BTNS:
				bolOn = (BtnOn( aBTN_LEFT ) and BtnOn( aBTN_RIGHT ))

		# return true if button pressed
		return bolOn

	# waits for given time (forever if given -1)
	# unless key pressed, return number of key pressed
	def BtnWait( dblSecs ):
		# wait for requested time
		#time.sleep( dblSecs )

		intBtnReturn = -1	# button value to return, default to none

		# calculate time to stop
		dtmStop = time.time( ) + dblSecs

		# check for input until time elapsed
		#while time.time( ) < dtmStop:
		# changed above to Do-While structure, now exit from loop
		while True:

			# if input given set action and exit loop to end delay
			#if GPIO.input(PIN_BTN_LEFT):
			if BtnOn( aBTN_LEFT ):
				intBtnReturn = Lcd.CHR_BTN_LEFT
				break

			elif BtnOn( aBTN_RIGHT ):
				intBtnReturn = Lcd.CHR_BTN_RIGHT
				break

			elif BtnOn( aBTN_DOWN ):
				intBtnReturn = Lcd.CHR_BTN_DOWN
				break

			elif BtnOn( aBTN_UP ):
				intBtnReturn = Lcd.CHR_BTN_UP
				break

			# exit if reached stop time and not waiting forever
			elif (dblSecs != -1) and (time.time( ) >= dtmStop):
				break

		# return button result
		print( "Called BtnWait( " + str(dblSecs) + " ) = " + str(intBtnReturn) )
		return intBtnReturn

	# returns true if any button pressed
	def AnyBtnPressed( ):
		#return GPIO.input(PIN_BTN_LEFT) or GPIO.input(PIN_BTN_RIGHT) or GPIO.input(PIN_BTN_UP) or GPIO.input(PIN_BTN_DOWN)
		return BtnOn( aBTN_UP ) or BtnOn( aBTN_RIGHT ) or BtnOn( aBTN_DOWN ) or BtnOn( aBTN_LEFT ) or BtnOn( aBTN_OK )

	# waits given max seconds or until no switches pressed
	def DebounceBtns( intMaxSecsWait = 4 ):

		# calculate time to stop
		dtmStop = time.time( ) + intMaxSecsWait

		# check for input until time elapsed
		while time.time( ) < dtmStop:
			#print( "debounce Btns: Left " + str(GPIO.input(PIN_BTN_LEFT)) + "\tRight " + str(GPIO.input(PIN_BTN_RIGHT)) + "\tDown " + str(GPIO.input(PIN_BTN_DOWN)) + "\tUp " + str(GPIO.input(PIN_BTN_UP)) )
			print( "debounce Btns: Left " + str(BtnOn( aBTN_LEFT )) + "\tRight " + str(BtnOn( aBTN_RIGHT )) + "\tDown " + str(BtnOn( aBTN_DOWN )) + "\tUp " + str(BtnOn( aBTN_UP )) + "\tOK " + str(BtnOn( aBTN_OK )) )

			# sleep for a moment if any button still pressed
			if AnyBtnPressed( ):
				time.sleep( 0.05 )

			# else no button pressed now so exit
			else:
				break

		# sleep for another moment to ensure debounce
		time.sleep( 0.05 )


	######################
	#  output functions  #
	######################

	### drive ###

	# moves given motor 1(X) or 2(Y) in given direction
	# -ve reverse or +ve forward, at given speed, or 0 to stop
	def SetMotor( intMotor, intSpeed ):
		#print( str(time.time()) + " Called SetMotor( " + str(intMotor) + ", " + str(intSpeed) + " ) for DC motors: " + str(bolDcMotors) )

		bolMove = True # initialise flag to carry out movement

		# set direction from sign of given speed
		#if intSpeed > 0:
		#        intDirection = 1
		#elif intSpeed < 0:
		#        intDirection = -1
		#else:
		#        intDirection = 0

		# reduce speed to max in either direction if too high
		if abs(intSpeed) > PWM_MAX_HZ:
			intSpeed = (intSpeed / abs(intSpeed)) * PWM_MAX_HZ

		# get start time stamp
		dtmTrackFrom = time.time()

		# prcoess tracking or limits if set to
		if TRACK_POS or SW_LIMITS:

			# process coordinates if enabled
			if not intPoss[intMotor-1] is None:

				# this step counter system for position tracking works on averages,
				# because the first instant creates 1 step, then one for each full
				# pulse period after, the average system works by awarding 1/2 step
				# if starting from 0, then time divided by pulse periods afterwards
				if intLastSpeeds[intMotor-1] != 0:

					# add previous movement to current position
					# NB- ballsed up as actual PWM control only counts complete cycles maybe?
					#intPoss[intMotor-1] = intPoss[intMotor-1] + (intLastSpeeds[intMotor-1] * (dtmTrackFrom - intLastTimes[intMotor-1]))

					# get time in secs last movement was running
					#print( "getting time as now: " + str(dtmTrackFrom) + " less Last Time: " + str(intLastTimes[intMotor-1]) )
					fltLastRunSecs = dtmTrackFrom - intLastTimes[intMotor-1]
					#print( " = dif of: " + str(fltLastRunSecs) )

					# run below if starting from 0 and changing speeds (NB- fudges to only check if below rounded down too much, so trying rounding up :(
	##                                if (abs(intLastSpeeds[intMotor-1]) < 3) and (intLastSpeeds[intMotor-1] != intSpeed):
	##                                        print( "processing first run as: " + str(intLastSpeeds[intMotor-1]) + " < 3 and != current speed: " + str(intSpeed) )
	##
	##                                        # get pulse period for previous speed
	##                                        print( "cycle length for Last Speed: " + str(intLastSpeeds[intMotor-1]) )
	##                                        fltLastCycle = 1.0 / abs(intLastSpeeds[intMotor-1])
	##                                        print( " = " + str(fltLastCycle) )
	##
	##                                        # remove remainder
	##                                        #print( "removing remainder for Last Speed: " + str(intLastSpeeds[intMotor-1]) + " and Last Time: " + str(fltLastRunSecs) )
	##                                        print( "removing remainder: " + str(fltLastRunSecs % fltLastCycle) + " from last run time: " + str(fltLastRunSecs) )
	##                                        fltLastRunSecs = fltLastRunSecs - (fltLastRunSecs % fltLastCycle)
	##                                        print( "new run time rounded down: " + str(fltLastRunSecs) )
	##
	##                                        # add extra initial step
	##                                        intPoss[intMotor-1] = intPoss[intMotor-1] + (intLastSpeeds[intMotor-1] / abs(intLastSpeeds[intMotor-1]))
	##                                        print( "added initial step: " + str(intPoss[intMotor-1]) )
	# other fixes:
	#fltLastRunSecs = fltLastRunSecs - (fltLastRunSecs % (0.5 / intLastSpeeds[intMotor-1]))
	#fltLastRunSecs = fltLastRunSecs - (fltLastRunSecs % (2 / intLastSpeeds[intMotor-1]))

					# add previous movement to current position
					#print( "adding last speed: " + str(intLastSpeeds[intMotor-1]) + ", for time: " + str(fltLastRunSecs) + ", to last position of: " + str(intPoss[intMotor-1]) )
					intPoss[intMotor-1] = round( intPoss[intMotor-1] + (intLastSpeeds[intMotor-1] * fltLastRunSecs), 2 )

	# other fixes:
					#intLastTimes[intMotor-1] = dtmTrackFrom
	# test for reuse after processing
					intLastTimes[intMotor-1] = "ardvark" + str(dtmTrackFrom)
					intLastSpeeds[intMotor-1] = "penguin" + str(dtmTrackFrom)


					# store in file
					setAxisPos( intMotor, intPoss[intMotor-1] )
	##                                with open("axis" + str(intMotor) + "pos.txt", 'w') as f:
	##
	##                                        # set file to anyone read and write
	##                                        os.chmod( "axis" + str(intMotor) + "pos.txt", 0o666 )
	##
	##                                        # write position
	##                                        f.write('%d' % intPoss[intMotor-1])

				# else last movement was stop so if moving now add initial half step average
				elif intSpeed != 0:
					intPoss[intMotor-1] = intPoss[intMotor-1] + (0.5 * (intSpeed / abs(intSpeed)))

					# store in file
					setAxisPos( intMotor, intPoss[intMotor-1] )

				# stop if aproaching -ve limits
				if SW_LIMITS and (intSpeed < 0):
					if abs(intSpeed) > intPoss[intMotor-1]:
						Lcd.ShowStr( "Axis " + str(intMotor) + " low limit", 1 )
						print( "Axis " + str(intMotor) + " low limit aproaching" )
						print( "speed: " + str(intSpeed) + " > pos: " + str(intPoss[intMotor-1]) )
						bolMove = False
						intSpeed = 0

				# stop if aproaching +ve limits
				# added indent 2017-6-9 as uses intPoss
				if SW_LIMITS and not (intLimits[intMotor-1] is None):
					if intSpeed > 0:
						if intSpeed > (intLimits[intMotor-1] - intPoss[intMotor-1]):
							Lcd.ShowStr( "Axis " + str(intMotor) + " top limit", 1 )
							print( "Axis " + str(intMotor) + " top limit " + str(intLimits[intMotor-1]) + " current pos " + str(intPoss[intMotor-1]) )
							print( "speed: " + str(intSpeed) + " > dif: " + str(intLimits[intMotor-1] - intPoss[intMotor-1]) )
							bolMove = False
							intSpeed = 0
	##                                        else:
	##                                                print( "Axis " + str(intMotor) + " with limit " + str(intLimits[intMotor-1]) + " by speed " + str(intSpeed) )
	##                                else:
	##                                        print( "Axis " + str(intMotor) + " unlimited speed " + str(intSpeed) )
	##                        else:
	##                                print( "Axis " + str(intMotor) + " unlimited as using software limits: " + str(SW_LIMITS) + ", and no limit set: " + str(intLimits[intMotor-1] is None) )


		# set output pins for requested motor
		# X motor
		if intMotor == 1:
			intMotorPinN = PIN_X_MOTOR_N
			intMotorPinP = PIN_X_MOTOR_P

			# reverse direction if required for this motor
			if MOT_X_REV:
				intSpeed = -intSpeed

		# Y motor
		else:
			intMotorPinN = PIN_Y_MOTOR_N
			intMotorPinP = PIN_Y_MOTOR_P

			# reverse direction if required for this motor
			if MOT_Y_REV:
				intSpeed = -intSpeed

		# move DC motor
		# TODO vary speed using
		#pwnMotorXp.ChangeDutyCycle( not 50 ) no point
		if bolDcMotors or (bolDcMotors is None):

			# move forward
			#if intDirection == 1:
			if intSpeed > 0:
				GPIO.output( intMotorPinN, GPIO.LOW )
				GPIO.output( intMotorPinP, GPIO.HIGH )
				print( "DC Motor " + str(intMotor) + " forward" )

			# move back
			#elif intDirection == -1:
			elif intSpeed < 0:
				GPIO.output( intMotorPinN, GPIO.HIGH )
				GPIO.output( intMotorPinP, GPIO.LOW )
				print( "DC Motor " + str(intMotor) + " back" )

			# stop
			else:
				GPIO.output( intMotorPinN, GPIO.LOW )
				GPIO.output( intMotorPinP, GPIO.LOW )
				print( "DC Motor " + str(intMotor) + " stop" )

		# else move stepper motor via controller
		else:
			#print( "pre setting motor pin function " + str(GPIO.gpio_function(intMotorPinP)) )
			# set direction to forward
			#if intDirection == 1:
			if intSpeed > 0:
				GPIO.output( intMotorPinN, GPIO.HIGH )

			# set direction to back
			#elif intDirection == -1:
			elif intSpeed < 0:
				GPIO.output( intMotorPinN, GPIO.LOW )

			# set to manage PWM for requested stepper motor
			if intMotor == 1:
				pwmMotorP = pwmMotorXp
			else:
				pwmMotorP = pwmMotorYp

			# if stopping stop PWM signals
			#if intDirection == 0:
			if intSpeed == 0:
				# to fix GPIO PWM error https://raspberrypi.stackexchange.com/questions/68386/pwm-stop-respond-after-hundreds-of-start-stop
				pwmMotorP.ChangeDutyCycle( 0 )
				#pwmMotorP.stop( )
				#pwmMotorXp.stop( )
				#pwmMotorYp.stop( )
				#print( "Stepper Motor " + str(intMotor) + " stopped" )

			# else moving so send clock pulses to move motor
			else:
			#if (intSpeed > 0) or (intSpeed < 0):
				#pwmMotorP = GPIO.PWM( intMotorPinP, PWM_MAX_HZ )
				#print( "Stepper Motor " + str(intMotor) + " to move at " + str(intSpeed) )
				pwmMotorP.ChangeFrequency( abs(intSpeed) ) # to change speed
				pwmMotorP.ChangeDutyCycle( 50 )
				pwmMotorP.start( PWM_DUTY_CYCLE )
				#pwmMotorXp.start( PWM_DUTY_CYCLE )
				#pwmMotorYp.start( PWM_DUTY_CYCLE )
				#print( "Stepper Motor " + str(intMotor) + " moving at " + str(intSpeed) )

			#print( "post setting motor pin function " + str(GPIO.gpio_function(intMotorPinP)) )


		# set software limits if using
		# now used to prevent cutoff if moving so used allways
		#if TRACK_POS or SW_LIMITS:

			# set next previous movement to given
			intLastSpeeds[intMotor-1] = intSpeed
			intLastTimes[intMotor-1]  = dtmTrackFrom

			# alert if aproaching limits
			if SW_LIMITS and not bolMove:

				# show text and beep
				Lcd.ShowStr( "! Reverse Out ! ", 2 )
				BoxBeep( 1 )

				# return to previous display
				Lcd.ShowPrev( )

			# print coordinates for debug
			#print( "intPoss: " + str(intPoss) )

		# return true if movement made
		return bolMove

        # move specified axis if difference exceeds threshold,
        # also updates ephem and reflector limits if exceeded.
        def CorrectAxis( intAxis, strAxisName, intAxisDif, axisActMin ):
		#print( str(time.time()) + " Called CorrectAxis( " + str(intAxis) + ", " + str(strAxisName) + ", " + str(intAxisDif) + ", " + str(axisActMin) + " )" )

                # set minimum difference threshold to act on for this axis
                #if intAxis == 0:
                #        axisActMin = X_ACT_MIN
                #else:
                #        axisActMin = Y_ACT_MIN

                # set movement or stop if difference thresholds exceeded
                if intAxisDif > axisActMin:
                        #vindebug( "*** X Right ***" )
                        SetMotor( intAxis + 1, PWM_TRACK_HZ )

                elif intAxisDif < -axisActMin:
                        #vindebug( "*** X Left ***" )
                        SetMotor( intAxis + 1, -PWM_TRACK_HZ )

                elif (intAxisDif < (axisActMin / 2)) and (intAxisDif > -(axisActMin / 2)):
                        #vindebug( "*** X Stop ***" )
                        SetMotor( intAxis + 1, 0 )

                        # if tracking and ephem data set update limits if exceeded
                        if TRACK_POS and (not ephemBody is None):

                                # initialise to extremes not updated
                                bolSetMin = False
                                bolSetMax = False
                                
                                # set to initialise if empty or replace if exceeded
                                # min and max solar tracking positions for conversion
        # TODO- do above in initialisation to limits?
                                if minSun[intAxis] is None:
                                        bolSetMin = True

                                elif minSun[intAxis] > intPoss[intAxis]:
                                        bolSetMin = True

                                elif maxSun[intAxis] is None:
                                        bolSetMax = True

                                elif maxSun[intAxis] < intPoss[intAxis]:
                                        bolSetMax = True

                                print( "checking source: " + str(ephemBody.name) + " for axis: " + str(intAxis) )

                                # do the same with ephem object if is sun
                                #if not ephemBody is None:
                                # prompt if ephem object not set
                                if ephemBody is None:
                                        print( "ephemBody is empty" )

                                # do the same with ephem object if is sun and any extremes updated
        # TODO- and sensing sun, not just predicting with ephem info 
                                elif (bolSetMin or bolSetMax) and (ephemBody.name == "Sun"):
                                
                                        # initialise min and max solar tracking positions if unset
                                        # TODO- do above in initialisation to limits?
                                        if bolSetMin:
                                                minSun[intAxis] = intPoss[intAxis]
                                                SetConfigVar( "minSun", minSun )

                                        elif bolSetMax:
                                                maxSun[intAxis] = intPoss[intAxis]
                                                SetConfigVar( "maxSun", maxSun )

                                        # get latest coordinats for source
                                        #ephemViewer.date = time.strftime("%Y-%m-%d %H:%M:%S")
                                        ephemViewer.date = datetime.datetime.utcnow()
                                        ephemBody.compute( ephemViewer )
                                        print( str(ephemBody.name) + " az: " + str(ephemBody.az) + ", alt: " + str(ephemBody.alt) )

                                        # show ephem observer for debug
                                        print( "ephemViewer- lat: " + str(ephemViewer.lat) + ", lon: " + str(ephemViewer.lon) )
                                        print( "ephemViewer.date: " + str(ephemViewer.date) )
                                        #print( "next setting: " + str(ephemViewer.next_setting(ephemBody)) )   # WARNING- messes up future queries!

                                        # set azimouth for x axis else altitude for y
                                        if intAxis == 0:
                                                ephemData = ephemBody.az
                                        else:
                                                ephemData = ephemBody.alt
                                        print( "using ephemData: " + str(ephemData) )

                                        # initialise max and min solar positions if unset
                                        # TODO- do above in initialisation to limits?
                                        #if minEphem[intAxis] is None:
                                        #        minEphem[intAxis] = ephemData

                                        #if maxEphem[intAxis] is None:
                                        #        maxEphem[intAxis] = ephemData

                                        # set max and min solar positions if exceeded
                                        # storing them, clear ephem conversions so redone
                                        #if minEphem[intAxis] > ephemData:
                                        if bolSetMin:
                                                minEphem[intAxis] = ephemData
                                                SetConfigVar( "minEphem", minEphem )
                                                intEphem2stepsRatio[intAxis] = None
                                                #intEphem2stepsBase[intAxis]  = None
                                                print( "updated minSun: " + str(minSun) + " from pos: " + str(intPoss) + ",\nand minEphem: " + str(minEphem) + ", from: " + str(ephemData) )

                                        #if maxEphem[intAxis] < ephemData:
                                        elif bolSetMax:
                                                maxEphem[intAxis] = ephemData
                                                SetConfigVar( "maxEphem", maxEphem )
                                                intEphem2stepsRatio[intAxis] = None
                                                #intEphem2stepsBase[intAxis]  = None
        # TODO- use other variable to compare new ratio and base with old?
                                                print( "updated maxSun: " + str(maxSun) + " from pos: " + str(intPoss) + ",\nand maxEphem: " + str(maxEphem) + ", from: " + str(ephemData) )

                                        # test ephem data
                                        if True:

                                                # if azimouth and altitude set show calculated and current positions
                                                if getStepsFromEphem( ephemBody.az, 0, intSunAt ) and getStepsFromEphem( ephemBody.alt, 1, intSunAt ):
                                                        print( str(ephemBody.name) + " calculated to steps position: " + str(intSunAt) )
                                                        print( "Current position is: " + str(intPoss) )
                                                else:
                                                        print( "failed to get steps position for " + str(ephemBody.name) )

                                                # beep, stop motors and pause to debug
                                                BoxBeep( 3 )
                                                SetMotor( 0, 0 )
                                                SetMotor( 1, 0 )
                                                #strPause = raw_input( "hit enter to continue: " )

                # prompt movement for debug
                vindebug( "*** Axis " + strAxisName + " motor set to " + str(intLastSpeeds[intAxis]) + " by diff " + str(intAxisDif) + " ***" )







Called getStepsFromEphem( 28:23:28.6, 1, [6339.548827555205, 357.39229096825466] )
min sun and ephem set
max sun and ephem set
using min and max as far enough appart
from min: [3289.22, 139.85] / max: [3501.52, 231.82] sun sensed pos
and min: [5.992926120758057, 0.4955214262008667]
/ max: [6.062948226928711, 0.5023022294044495] Ephem pos
set ephem ratio: [6063.799323105006, 27126.57991649306] and base: [29761.461354471016, 13162.10156817243]
Sun calculated to steps position: [6339.548827555205, 279.7000000000007]
Current position is: [3348.49, 139.85]
*** Axis Y motor set to 0 by diff -0.105328996748 ***
auto zoom disabled, zActFrom:0
log file belongs to other user so can't chmod
********************
* Autotracking Sun *
*                  *
********************


Called BtnWait( 0.1 ) = -1
PRs:  -X 26.56  +X 23.66   -Y 19.27  +Y 14.9   Z 21.09   D 100000
Difs: X -0.057745917961  Y -0.127889961955  Z 1.00035561878
RC reading by time: False, tracking variation: 0.0360232255007
Btns: Left 0	Right 0	Down 0	Up 0	OK 0
checking source: Sun for axis: 0
Called SetConfigVar( minSun, [3264.53, 139.85] )
Sun az: 339:48:18.1, alt: 28:03:03.8
ephemViewer- lat: -37:48:47.5, lon: 144:57:46.7
ephemViewer.date: 2017/7/15 03:42:35
using ephemData: 339:48:18.1
Called SetConfigVar( minEphem, [5.930716514587402, 0.4955214262008667] )
updated minSun: [3264.53, 139.85] from pos: [3264.53, 139.35],
and minEphem: [5.930716514587402, 0.4955214262008667], from: 339:48:18.1
Called getStepsFromEphem( 339:48:18.1, 0, [6569.700000000001, 170.2136371227898] )
min sun and ephem set
max sun and ephem set
using min and max as far enough appart
from min: [3264.53, 139.85] / max: [3501.52, 231.82] sun sensed pos
and min: [5.930716514587402, 0.4955214262008667]
/ max: [6.062948226928711, 0.5023022294044495] Ephem pos
set ephem ratio: [3584.4654176192676, 27126.57991649306] and base: [14729.38824824202, 13162.10156817243]
Called getStepsFromEphem( 28:03:03.8, 1, [6529.060000000001, 170.2136371227898] )
Sun calculated to steps position: [6529.060000000001, 118.61445971009925]
Current position is: [3264.53, 139.35]
*** Axis X motor set to 0 by diff -0.057745917961 ***
checking source: Sun for axis: 1
Called SetConfigVar( minSun, [3264.53, 118.32] )
Sun az: 339:47:31.4, alt: 28:02:51.2
ephemViewer- lat: -37:48:47.5, lon: 144:57:46.7
ephemViewer.date: 2017/7/15 03:42:38
using ephemData: 28:02:51.2
Called SetConfigVar( minEphem, [5.930716514587402, 0.48952198028564453] )
updated minSun: [3264.53, 118.32] from pos: [3264.53, 118.32],
and minEphem: [5.930716514587402, 0.48952198028564453], from: 28:02:51.2
Called getStepsFromEphem( 339:47:31.4, 0, [6529.060000000001, 118.61445971009925] )
Called getStepsFromEphem( 28:02:51.2, 1, [6528.248127005878, 118.61445971009925] )
min sun and ephem set
max sun and ephem set
using min and max as far enough appart
from min: [3264.53, 118.32] / max: [3501.52, 231.82] sun sensed pos
and min: [5.930716514587402, 0.48952198028564453]
/ max: [6.062948226928711, 0.5023022294044495] Ephem pos
set ephem ratio: [3584.4654176192676, 17761.782097501597] and base: [14729.38824824202, 8458.14274577109]
Sun calculated to steps position: [6528.248127005878, 236.63999999999942]
Current position is: [3264.53, 118.32]
*** Axis Y motor set to 0 by diff -0.127889961955 ***
auto zoom disabled, zActFrom:0


        # sets ephem to steps conversion variables for processing
        #def setEphemToSteps( intAxis ):
        # sets given axis of given array to steps position equivalent of given ephem angle
        def getStepsFromEphem( fltEphem, intAxis, intPos ):
		print( "Called getStepsFromEphem( " + str(fltEphem) + ", " + str(intAxis) + ", " + str(intPos) + " )" )

                # initialise to not set                
                bolSet = False

                # (re)calculate conversion variables if not (yet) set
                if intEphem2stepsRatio[intAxis] is None:
                        #intEphem2stepsBase[intAxis]  = None

                        # check given min sun and ephem positions
                        if (not minSun[intAxis] is None) and (not minEphem[intAxis] is None):
                                print( "min sun and ephem set" )

                                # if given max too use those if they're far enough appart
                                if (not maxSun[intAxis] is None) and (not maxEphem[intAxis] is None):
                                        print( "max sun and ephem set" )

                                        # if they're appart enough use them to get ratio and 0
                                        if maxSun[intAxis] - minSun[intAxis] > 50:
                                                print( "using min and max as far enough appart" )

                                                # get ratio and offset / intersect
                                                intEphem2stepsRatio[intAxis] = (2 * (maxSun[intAxis] - minSun[intAxis])) / (maxEphem[intAxis] - minEphem[intAxis])
                                                intEphem2stepsBase[intAxis]  = (intEphem2stepsRatio[intAxis] * maxEphem[intAxis]) - (2 * maxSun[intAxis])
                                                #bolSet = True
                                                print( "from min: " + str(minSun) + " / max: " + str(maxSun) + " sun sensed pos\nand min: " + str(minEphem) + "\n/ max: " + str(maxEphem) + " Ephem pos\nset ephem ratio: " + str(intEphem2stepsRatio) + " and base: " + str(intEphem2stepsBase) )
                                                #strPause = raw_input( "hit enter to continue: " )

                                        # else too close so...

                                # if not yet set try using rotational info if given
                                if intEphem2stepsRatio[intAxis] is None:
                                #intEphem2stepsBase[intAxis]  = None

                                        # if given steps per rotation calculate ephem ratio and baseline from that
                                        if not intStepsPerRotation[intAxis] is None:
                                                print( "using steps per rotation" )
                                                intEphem2stepsRatio[intAxis] = intStepsPerRotation[intAxis] / (2 * PI_CONST)
                                                intEphem2stepsBase[intAxis]  = (intEphem2stepsRatio[intAxis] * minEphem[intAxis]) - (2 * minSun[intAxis])
                                                #bolSet = True
                                                print( "from min sun: " + str(minSun) + "\nand ephem: " + str(minEphem) + " data\nand steps per rotation: " + str(intStepsPerRotation) + "\nset ephem ratio: " + str(intEphem2stepsRatio) + " and base: " + str(intEphem2stepsBase) )
                                                #strPause = raw_input( "hit enter to continue: " )

                                # TODO- if still not set asume base 0 if no steps per rotation and low difference? ok for y axis but z needs magnetic sensor
                                #if intEphem2stepsRatio[intAxis] is None:
                                        #print( "using accelerometer / compass 0 per rotation" )

                # calculate steps if conversion variables set
                if not intEphem2stepsRatio[intAxis] is None:

                        # get steps angle for given ephem
                        fltSteps = (intEphem2stepsRatio[intAxis] * fltEphem) - intEphem2stepsBase[intAxis]

                        # set given element of given array
                        intPos[intAxis] = fltSteps

                        # set flag to return element was set
                        bolSet = True

                # return true only if set
                return bolSet

        # ac/decelerates the given motor from it's current speed to the given speed by the given increments the given periods appart
        def AccMotor( intMotor, intToSpeed, intIncrement, fltPeriod ):

		# get current speed of last direction
		intLastSpeed = intLastSpeeds[ intMotor-1 ]

                # repeatedly ac/decelerate by increment until same speed
                while abs(intLastSpeed) != intToSpeed:

                        # set to requested speed if close enough
                        if abs(intLastSpeed - intToSpeed) < intIncrement:
                                intLastSpeed = intToSpeed

                        # else set accelerate if too slow / in opposite direction than target speed
                        elif intLastSpeed < intToSpeed:
                                intLastSpeed = intLastSpeed + intIncrement

                        # else set to deccelarate / reverse as current velocity higher than target
                        else:
                                #intLastSpeed = intLastSpeed + (intIncrement * ((intToSpeed-intLastSpeed) / abs(intToSpeed-intLastSpeed)))
                                intLastSpeed = intLastSpeed - intIncrement

                        # set requested motor to required speed
                        #SetMotor( (1 + int(intDir > 2)), (1 - (2 * (intDir%2))) * intLastSpeed )
                        SetMotor( intMotor, intLastSpeed )

                        # pause for the requested time before next speed change
                        time.sleep( fltPeriod )


	# moves reflector towards given coordinates
	# IMPORTANT - will not stop like MoveTo !!!
	# so call repeatedly until returns true or
	# stop movement manually with SetMotors(X, 0.
	# returns true only when coordinates reached
	def MoveTowards( intMaxSpeed, intMaxErr, fltPeriod, intXPos, intYPos ):
		#print( str(time.time()) + " Called MoveTowards( " + str(intMaxSpeed) + ", " + str(intMaxErr) + ", " + str(fltPeriod) + ", " + str(intXPos) + ", " + str(intYPos) + " ) from: " + str(intPoss) )

		bolFound = False # initialise found flag

		# prcoess only if tracking and position and limits are set
		if TRACK_POS and not ((intPoss[0] is None) or (intPoss[1] is None)):

			# get differences between current position and target
			intXDif = intXPos - intPoss[0]
			intYDif = intYPos - intPoss[1]

			# get max difference
			if abs(intXDif) > abs(intYDif):
				intMaxDif = intXDif
			else:
				intMaxDif = intYDif
			#print( "difs X: " + str(intXDif) + ", Y: " + str(intYDif) + ", Max: " + str(intMaxDif) )

			# process if difference greater than error
			#if abs(intMaxDif) > intMaxErr:
			# process if difference greater than error
			if abs(intMaxDif) > intMaxErr:

				# limit requested max speed to global max if exceeded
				if intMaxSpeed > PWM_MAX_HZ:
					intMaxSpeed = PWM_MAX_HZ

				# calculate what direct speed would be
				intDirectSpeed = int(intMaxDif / ( 1 + (2 * fltPeriod) ))

				# if greater than max speed reduce to max in that direction
				if abs(intDirectSpeed) > intMaxSpeed:
					intDirectSpeed = (intDirectSpeed / abs(intDirectSpeed)) * intMaxSpeed
				#print( "speeds intDirectSpeed: " + str(intDirectSpeed) + ", Max: " + str(intMaxSpeed) )

				# set both speeds
				if intXDif == intMaxDif:
					intXSpeed = intDirectSpeed
					intYSpeed = int((intYDif / intXDif) * intXSpeed)
				else:
					intYSpeed = intDirectSpeed
					intXSpeed = int((intXDif / intYDif) * intYSpeed)

			# else stop both motors and set flag as done
			else:
				intXSpeed = 0
				intYSpeed = 0
				bolFound = True


                        AUTO_ACC = 50

                        # if difference between desired velocity and present in either direction too great reduce
                        if intXSpeed != 0:
                                if abs(intXSpeed - intLastSpeeds[0]) > AUTO_ACC:
                			intXSpeed = intLastSpeeds[0] + (AUTO_ACC * ( intXSpeed / abs(intXSpeed) ))
                	elif abs(intLastSpeeds[0]) > AUTO_ACC:
                		intXSpeed = intLastSpeeds[0] - (AUTO_ACC * ( intLastSpeeds[0] / abs(intLastSpeeds[0]) ))

                        if intYSpeed != 0:
                                if abs(intYSpeed - intLastSpeeds[1]) > AUTO_ACC:
        				intYSpeed = intLastSpeeds[1] + (AUTO_ACC * ( intYSpeed / abs(intYSpeed) ))
                	elif abs(intLastSpeeds[1]) > AUTO_ACC:
                		intYSpeed = intLastSpeeds[1] - (AUTO_ACC * ( intLastSpeeds[1] / abs(intLastSpeeds[1]) ))

			# set both movements
			time.sleep(0.1)
			SetMotor( 1, intXSpeed )
			time.sleep(0.2)
			SetMotor( 2, intYSpeed )

                        # ensure flag not set as found if still moving so it's called again to stop
                        if (intXSpeed != 0) or (intYSpeed != 0):
				bolFound = False

		else:
			print( "couldn't MoveTowards as tracking not set" )

		# return result
		return bolFound

	# returns time required to reach given coordinates
	# (from the current position) at the given speed
	def TimeTo( intMaxSpeed, intXPos, intYPos ):
		#print( str(time.time()) + " Called TimeTo( " + str(intMaxSpeed) + ", " + str(intXPos) + ", " + str(intYPos) + " ) from: " + str(intPoss) )

		fltTime = None

		# find time to X coordinate if furthest, else time to Y coordinate
		if intMaxSpeed > 0:
                        
        		if abs(abs(intXPos) - intPoss[0]) > abs(abs(intYPos) - intPoss[1]):
                		fltTime = abs(1.0 * abs(intXPos) - intPoss[0]) / intMaxSpeed
                        else:
                                fltTime = abs(1.0 * abs(intYPos) - intPoss[1]) / intMaxSpeed

		return fltTime


        # moves reflector to requested coordinates,
        # stopping when found sun and returning true
        # with dish all lined up, else returns false.
        # or continues even if sun found if flag off
        def SeekTo( intMaxSpeed, intMaxErr, intXPos, intYPos, bolStopOnSun ):
                #print( str(time.time()) + " Called SeekTo( " + str(intMaxSpeed) + ", " + str(intXPos) + ", " + str(intYPos) + ", " + str(bolStopOnSun) + ") from: " + str(intPoss) )

		#bolFound     = False    # initialise to sun not found
		#bolArrived   = False    # initialise to not arrived
                intReturn    = 0        # initialise to return not arrived or found sun
                intPrCounter = 0        # initialise to check first PR
                #intPrTime    = 0        # value of current PR
                fltMaxPrTime = 0.5      # max time to check PR
                #intSunFrom = [ 0, 0 ]
                #intSunTo = [ 0, 0 ]

                # default start time to now
                dtmStart = time.time()

                # check duration of motion to requested coordinates at max speed
                intMaxTime = TimeTo( intMaxSpeed, intXPos, intYPos )
                print( "time available: " + str(intMaxTime) )

                # if less than time required to check PRs reduce max speed
                if intMaxTime < fltMaxPrTime:
                        intSeekSpeed = int(intMaxSpeed * (intMaxTime / PRtime))
                        print( "set preliminary speed to: " + str(intSeekSpeed) + " so available time to process PRs: " + str(PRtime) )

                # else set to max
                else:
                        intSeekSpeed = PWM_MAX_HZ
                        print( "set seek speed to max: " + str(intSeekSpeed) + " as plenty of time to check PRs: " + str(PRtime) )

                # decrease if too big
                if intSeekSpeed > intMaxSpeed:
                        intSeekSpeed = intMaxSpeed
                        print( "decreased speed to max of: " + str(intSeekSpeed) )

                # else increase if too small
                elif intSeekSpeed < 1:
                        intSeekSpeed = 1
                        print( "increased speed to min of: " + str(intSeekSpeed) )


		# keep moving until sun found or arrived at requested coordinates
		#while not (bolFound or bolArrived):
                while intReturn == 0:

                        # TODO- add function argument to make optional?
                        #if bolStopOnBtn:

                        # exit if user pressed OK
                        #if BtnOn( aBTN_OK ):
                        if BtnOn( aBTN_RIGHT ):

                                # stop motors first
                                AccMotor( 1, 0, 25, 0.1 )
                                AccMotor( 2, 0, 25, 0.1 )

                                # set to return user ended and exit loop
                                intReturn = -1
                                break

        		# move to required coordinates
                        #bolArrived = MoveTowards(intSeekSpeed, intMaxErr, fltMaxPrTime, intXPos, intYPos )

                        # find time to furthest point
        ##                if abs(abs(intXPos) - intPoss[0]) > abs(abs(intYPos) - intPoss[1]):
        ##                        intMaxTime = abs(abs(intXPos) - intPoss[0]) / intMaxSpeed
        ##                else:
        ##                        intMaxTime = abs(abs(intYPos) - intPoss[1]) / intMaxSpeed

                        #intMaxTime = TimeTo( intMaxSpeed, intXPos, intYPos )

                        # move to given coordinates, exiting if arrived
                        if MoveTowards(intSeekSpeed, intMaxErr, fltMaxPrTime, intXPos, intYPos ):
                                break

                        # if have enough time check next sensor for sun
                        #if intMaxTime > (PRtime / 4):
                        # if not arrived yet check next sensor for sun
                        #if not bolArrived:
                        else:
                                # find time to furthest point
                                intMaxTime = TimeTo( intMaxSpeed, intXPos, intYPos )

# TODO- if have enough time check next sensor for sun?
# if intMaxTime > fltMaxPrTime:
                                # set to set speed again mid way between
                                #dtmSetSpeed = time.time() + (intMaxTime / 2)

                                # TODO- to read multiple PRs between MoveTowards calls
                                # - handy if MoveTowards is slow
                                #while time.time() < dtmSetSpeed:

                                # get value of next sensor
                                #intPrTime = RCtime( PRs[intPrCounter] )
                                #PRvals[intPrCounter] = PRval(intPrCounter)
                                PRval( intPrCounter )

                                # if checking for sun check sensor value
                                if bolStopOnSun:

                                        # process if different enough to average
                                        #print( "*** PR " + str(intPrCounter) + " - Time: " + str(PRvals[intPrCounter]) + ", average: " + str(PRavgs[intPrCounter]) + ", Dif " + str(PRavgs[intPrCounter] - PRvals[intPrCounter]) + ", ratio " + str(PRvals[intPrCounter] / PRavgs[intPrCounter]) + " ***" )
                                        #if (PRvals[intPrCounter] / PRavgs[ intPrCounter ]) < (1 - (0.5 * ALL_ACT_MIN)):
                                        #if (PRvals[intPrCounter] / PRavgs[ intPrCounter ]) < (1 - (2 * ALL_ACT_MIN)):
                                        #if False:
                                        if (2 * PRvals[intPrCounter]) < PRavgs[intPrCounter]:

                                                # record cooridinates and speed at this point
                                                intSunFrom  = [ intPoss[0], intPoss[1] ]
                                                intSunTo    = [ intPoss[0], intPoss[1] ]
                                                intSunSpeed = [ intLastSpeeds[0], intLastSpeeds[1] ]
                                                print( "detected sun on PR " + str(intPrCounter) + " at " + str(intSunTo) )
                                                #intSunFrom[0] = intPoss[0]
                                                #intSunFrom[1] = intPoss[1]

                                                # stop motors
                                                #SetMotor( 1, 0 )
                                                #SetMotor( 2, 0 )

                                                # slow motors
                                                #SetMotor( 1, intSunSpeed[0] / 2 )
                                                #SetMotor( 2, intSunSpeed[1] / 2 )

                                                # slow if going fast enough
                                                if (abs(intSunSpeed[0]) > (intSeekSpeed / 2)) or (abs(intSunSpeed[1]) > (intSeekSpeed / 2)):
                                                        MoveTowards((intSeekSpeed / 2), intMaxErr, fltMaxPrTime, intXPos, intYPos )
                                                        print( "slowed to seek speed " + str(intSeekSpeed / 2) )

                                                # get opposite PR
                                                intOpPR = (intPrCounter + 2) % 4
                                                print( "suspect sun on last PR so checking oposite" )

                                                # get value of sensor opposite
                                                PRval( intOpPR )

                                                # if oposite PR similar difference then just sun coming out so continue
                                                if (1.5 * PRvals[intOpPR]) < PRavgs[intOpPR]:
                                                        print( "similar reading on oposite PR " + str(intOpPR) + " - Time: " + str(PRvals[intOpPR]) + ", average: " + str(PRavgs[intOpPR]) + ", Dif " + str(PRavgs[intOpPR] - PRvals[intOpPR]) + ", ratio " + str(PRvals[intOpPR] / PRavgs[intOpPR]) + "so continuing" )

                                                # else sun not on oposite PR so keep moving until sun passed
                                                else:
                                                        intSunHits   = 1
                                                        intSunMisses = 0

                                                        # keep moving until passed sun by half distance again
                                                        while intSunHits > -2:

                                                                # get value of sun sensor
                                                                PRval( intPrCounter )

                                                                # if stil sun set 'sun to' position
                                                                if (2 * PRvals[intPrCounter]) < PRavgs[intPrCounter]:
                                                                        intSunHits  += 1
                                                                        #intSunMisses = 0
                                                                        intSunTo = [ intPoss[0], intPoss[1] ]
                                                                        print( "incremented total sun hits to " + str(intSunHits) + " as still sun at " + str(intSunTo) )

                                                                # else sun passed so check if had more hits
                                                                else:
                                                                        #intSunHits -= 1
                                                                        intSunMisses += 1
                                                                        #intSunHits    = 0
                                                                        #print( "decremented total sun hits to " + str(intSunHits) + " as no sun at " + str(intPoss) )
                                                                        print( "incremented total sun misses: " + str(intSunMisses) + " as no sun at " + str(intPoss) )

                                                                        # exit if got more sun misses than hits / didn't get any more hits
                                                                        #if intSunTo == intSunFrom:
                                                                        if intSunMisses > intSunHits:
                                                                                #print( "exiting as sun from and to are the same so no further hits - sun hits counter is " + str(intSunHits) )
                                                                                print( "exiting as more sun misses " + str(intSunMisses) + " than hits " + str(intSunHits) )
                                                                                break

                                                                        # else had more hits so return to centre of sun on this axis if over half way past
                                                                        #elif (intSunTo - intSunFrom) / (intPoss - intSunFrom) > 1.5:
                                                                        #elif (intSunTo - intSunFrom) > 1.5 * (intPoss - intSunFrom):
                                                                        #elif (intSunTo[0] - intSunFrom[0]) > 1.5 * ((intPoss[0] - intSunFrom[0]) + intMaxErr):
                                                                        #elif (abs(intSunTo[0] - intSunFrom[0]) > 1.5 * abs(intPoss[0] - intSunFrom[0])) and (abs(intSunTo[1] - intSunFrom[1]) > 1.5 * abs(intPoss[1] - intSunFrom[1])):
                                                                        elif intSunHits > 1.5 * intSunMisses:
                                                                                #print( "setting sun found and returning to centre - sun hits counter is " + str(intSunHits) )
                                                                                print( "setting sun found and returning to centre as had 1.5 * as many sun hits " + str(intSunHits) + " as sun misses " + str(intSunMisses) )
                                                                                #bolFound = True
                                                                                intReturn = 1
                                                                                SeekTo( intMaxSpeed, intMaxErr, (intSunTo[0] + intSunFrom[0]) / 2, (intSunTo[1] + intSunFrom[1]) / 2, False )
                                                                                break

                                                                        # else not more than half way past so continue
                                                                        else:
                                                                                time.sleep( 0.1 )

                                                        # prompt found
                                                        #if bolFound:
                                                        if intReturn == 1:
                                                                print( "sun found at: " + str(intPoss) )
                                                                #Lcd.ShowStr( "Sun Found on PR" + str(intPrCounter), 1 )
                                                                #Lcd.ShowStr( chr(Lcd.CHR_BTN_RIGHT) + " to continue >>", 2 )

                                                                # if testing wait until user presses right button to continue
                                                                #if bolTestOptions:
                                                                #        while not BtnOn( aBTN_RIGHT ):
                                                                #                time.sleep( 0.2 )

                                                                # overwrite average to ignore next time
                                                                # TODO- remove as just for testing
                                                                #PRavgs[ intPrCounter ] = PRvals[intPrCounter]

                                        # if sun not found update averages
                                        #if not bolFound:
                                        if intReturn != 1:
                                                PRavgs[ intPrCounter ] = round( ((99 * PRavgs[ intPrCounter ]) + PRvals[intPrCounter]) / 100, 2 )
                                                #print( "new averages: " + str(PRavgs) )

                                # else not seeking sun so delay a moment before next pass
                                else:

                                        # delay for max time if less than usual delay, else just use usual delay
                                        if intMaxTime < 0.2:
                                                time.sleep( intMaxTime )
                                        else:
                                                time.sleep( 0.2 )

                                # set to process next PR
                                #intPrCounter = (intPrCounter + 1) % 4
                                intPrCounter += 1

                                # if last PR log line and set to start first next time
                                if intPrCounter == 4:
                                        #strLogMode = "Tracking"

                                        # log data if logging
                        		LogData( "Seeking" )

                                        # set to restart from first PR next time
                                        intPrCounter = 0


                        # else no time to check PRs so just wait for a moment
                        #else:
                        #        time.sleep( 0.2 )

                        # calculate next period
                        fltMaxPrTime = time.time() - dtmStart
                        dtmStart  = time.time()
                        #print( "period: " + str(fltPeriod) + " at " + str(dtmStart) )

                # return true if sun found
                #return bolFound
                return intReturn


	# repeatedly scans inside coordinte box for sun until
	# found (returning true) or finished (returning false)
	def SeekSunIn( intMaxSpeed, intMaxBoxSweep, intMinX, intMaxX, intMinY, intMaxY ):
		print( str(time.time()) + " Called SeekSunIn( " + str(intMaxSpeed) + ", " + str(intMinX) + ", " + str(intMaxX) + ", " + str(intMinY) + ", " + str(intMaxY) + " )" )

		# initialise directions, first sweep and sun not found
		intXDir     = 1
		intYDir     = -1
		intSweep    = 0
		#bolSunFound = False
		intSeekResult   = 0

		# get centre of given box
	#	intNewX = (intMinX + intMaxX) / 2
	#	intNewY = (intMinY + intMaxY) / 2

		# move to centre then scan within
	#	if not SeekTo( intMaxSpeed, intMaxBoxSweep, intNewX, intNewY ):
	#		print( "moving to box centre " + str(intPoss) )
		# NB- above scrapped as centre now bisected regularly

		# repeat until all levels swept, 1st level is just one
		# box bisecting between centre and outside of main. 2nd
		# level is 2 boxes bisecting between 1st and centre and
		#while (intSweep < intMaxBoxSweep) and not bolSunFound:
		while (intSweep < intMaxBoxSweep) and (intSeekResult == 0):

			print( "*** sweeping new box level " + str(intSweep + 1) + " ***" )

			Lcd.ShowStr( "Seek Level: " + str(intSweep + 1), 1 )
			# TODO- sort pause
			# try sleeping for different secs and writing result here
			# didn't cause segmentation fault:
			# 10 x 2 (called to level 5), lcd
			# did:
			# 1, 2, 3, 10 x 2 (called to level 8 but ended level 4!) lcd
			#time.sleep( 2 )

			# increase sweep count and reset box count
			# changing Y direction and max error allowed
			intSweep += 1
			intBox    = 1
			intYDir   = -1 * intYDir
			intMaxErr = 5 + (intMaxBoxSweep - intSweep)

			# repeat until all boxes for this level are swept
			#while (intBox <= (2 ** (intSweep - 1))) and not bolSunFound:
			while (intBox <= (2 ** (intSweep - 1))) and (intSeekResult == 0):

				print( "** sweeping new box " + str(intBox) + " in level " + str(intSweep) + " **" )

				# try sleeping for different secs and writing result here
				# didn't cause segmentation fault:
				# did: 2
				#time.sleep( 2 )

				# reset to first point on box
				intBoxPoint = 0

				# repeat until all points for this box are swept
				while intBoxPoint < 6:
					print( "* sweeping to box point " + str(intBoxPoint) + " of box " + str(intBox) + " in level " + str(intSweep) + " *" )

					Lcd.ShowStr( "Box: " + str(intBox) + ", Cnr: " + str(intBoxPoint + 1), 2 )

					# middle of first side
					if intBoxPoint == 0:

						# get centre of given box
						intNewX = (intMinX + intMaxX) / 2
						intNewY = (intMinY + intMaxY) / 2

						# get sides for this box
						intXside = (((2 * intBox) - 1) * (intMaxX - intMinX)) / (2 ** intSweep)
						intYside = (((2 * intBox) - 1) * (intMaxY - intMinY)) / (2 ** intSweep)

						# set to move to middle of first horizontal side
						intNewY = intNewY + (intYDir * (intYside / 2))
						#intNewY = intNewY + (intYDir * ( intYside / (2 ** (intSweep + 1)) ))
						#intNewX = intNewX + (intXDir * ( intXside / (2 ** (intSweep + 1)) ))

						print( "bisecting first side at " + str(intPoss) )

					# first corner
					elif intBoxPoint == 1:
						intNewX = intNewX + (intXDir * (intXside / 2))
						print( "moving to first corner from " + str(intPoss) )

					# second corner
					elif intBoxPoint == 2:
						intNewY = intNewY - (intYDir * intYside)
						print( "moving to second corner from " + str(intPoss) )

					# third corner
					elif intBoxPoint == 3:
						intNewX = intNewX - (intXDir * intXside)
						print( "moved to third corner from " + str(intPoss) )

					# last corner
					elif intBoxPoint == 4:
						intNewY = intNewY + (intYDir * intYside)
						print( "moving to last corner from " + str(intPoss) )

					# back to middle of first side
					elif intBoxPoint == 5:
						intNewX = intNewX + (intXDir * (intXside / 2))
						print( "moving back to bisect first side from " + str(intPoss) )

					# move to next point
					intSeekResult = SeekTo( intMaxSpeed, intMaxErr, intNewX, intNewY, True )

					# end if found or user quit
					if intSeekResult != 0:

                                                # if sun found report
                                                if intSeekResult == 1:
                                                        print( "**** sun located at " + str(intPoss) + " ****" )
                                                        #bolSunFound = True
						break

					# else continue to next point
					#else:
					intBoxPoint += 1

					# if last point change X direction and increase box count
					if intBoxPoint > 5:
						intXDir = -1 * intXDir
						intBox += 1
						break

		# return flag true if sun found
		#return bolSunFound
		return intSeekResult


	# Moves focus of reflector closer / zooms in (direction 1), fixes if (0) or focuses out (-1)
	# TODO offer other values of direction for focus speed
	def SetZoom( intDirection ):

		# zoom in by turning on pump and sealing valve
		if intDirection == 1:
			GPIO.output( PIN_PUMP, GPIO.HIGH )
			GPIO.output( PIN_VALVE, GPIO.HIGH )
			print( "Zooming In" )

		# zoom out by turning of pump and openning valve
		elif intDirection == -1:
			GPIO.output( PIN_PUMP, GPIO.LOW )
			GPIO.output( PIN_VALVE, GPIO.LOW )
			print( "Zooming Out" )

		# fix zoom by turning off pump and sealing valve
		else:
			GPIO.output( PIN_PUMP, GPIO.LOW )
			GPIO.output( PIN_VALVE, GPIO.HIGH )
			print( "Zoom fixed" )


	#################################################
	#  hi level functions for user interaction etc  #
	#################################################

	### LCD control ###

	# waits for given time on given page unless key pressed
	# updating variables on key press to scroll through pages
	def WaitOnTab( dblSecs, intTab ):
		print( "started WaitOnTab( dblSecs: " + str(dblSecs) + ", intTab: " + str(intTab) + " )" )

		# debounce for half a second max
		DebounceBtns( 0.5 )

		# wait for given time unless button pressed
		intBtn = BtnWait( 0 ) #dblSecs )

		# if pressed left button go to previous page
		if intBtn == Lcd.CHR_BTN_LEFT:
			intTab[0] -= 1

		# else go to next page
		else:
			intTab[0] += 1
		print( "ended WaitOnTab( dblSecs: " + str(dblSecs) + ", intTab: " + str(intTab) + " )" )


	# waits for given time unless key pressed
	# TODO perform various navigation functions by button pressed
	def LcdWait( dblSecs ):
		# wait for requested time
		#time.sleep( dblSecs )

		# calculate time to stop
		dtmStop = time.time( ) + dblSecs

		# check for input until time elapsed
		#while time.time( ) < dtmStop:
		# changed above to Do-While structure, now exit from loop
		while True:

			# if input given set action and exit loop to end delay
			# go to next display item
			if BtnOn( aBTN_RIGHT ):
				#dtmStop = time.time( )
				break

			# TODO go to previous display item
			#elif GPIO.input(PIN_BTN_LEFT):
			elif BtnOn( aBTN_LEFT ):
				#dtmStop = time.time( )
				break

			# TODO go to next display chapter
			elif BtnOn( aBTN_UP ):
				#dtmStop = time.time( )
				break

			# TODO go to previous display chapter
			elif BtnOn( aBTN_DOWN ):
				#dtmStop = time.time( )
				break


			# exit if reached stop time
			elif time.time( ) >= dtmStop:
				break

	# Beeps box buzzer for given number of seconds or until user clicks button
	def BoxBeep( secsBeep ):

		# sound beep if not silent mode
		if SOUND_ON:
			GPIO.output( PIN_BUZZER, GPIO.HIGH )

		# wait for given time before stopping beep
		#LcdWait( secsBeep )
		time.sleep( secsBeep )
		GPIO.output( PIN_BUZZER, GPIO.LOW )


	# show warnings, quiting if user didn't agree
	def UserDisclaimer( ):
		bolDisclaimed = False   # return flag only set if user disclaimed

		# show initial warning if first run
		if dicConfig["dblVsnDisclaimed"] == 0:

			# warn this is for testing only
			Lcd.ShowStr( "WARNING this is ", 1 )
			Lcd.ShowStr( " TEST SOFTWARE  ", 2 )
			time.sleep( 4 )

			Lcd.ShowStr( "DON'T DISTRIBUTE", 1 )
			Lcd.ShowStr( " this software  ", 2 )
			time.sleep( 4 )

			Lcd.ShowStr( "it will contain ", 1 )
			Lcd.ShowStr( "ERRORS and FAIL ", 2 )
			time.sleep( 4 )

		# else warn new test software
		else:

			Lcd.ShowStr( "WARNING, **NEW**", 1 )
			Lcd.ShowStr( " test software  ", 2 )
			time.sleep( 4 )

			Lcd.ShowStr( "DON'T DISTRIBUTE", 1 )
			Lcd.ShowStr( " this new code  ", 2 )
			time.sleep( 4 )

			Lcd.ShowStr( "it will contain ", 1 )
			Lcd.ShowStr( "   new ERRORS   ", 2 )
			time.sleep( 3.5 )

		Lcd.ShowStr( "you USE this AT ", 1 )
		Lcd.ShowStr( " YOUR OWN RISK  ", 2 )
		time.sleep( 4 )

		Lcd.ShowStr( "if you agree hit", 1 )
		Lcd.ShowStr( " the keys shown ", 2 )
		time.sleep( 4 )

		Lcd.ShowStr( "or other keys to", 1 )
		Lcd.ShowStr( "end -Recommended", 2 )
		time.sleep( 4 )

		# check if user will use at own risk
		Lcd.ShowStr( "Use at own risk?", 1 )

		# initialise loop counter to start
		intLcdLoop = 1

		# keep checking for pressed keys, aborting if wrong key pressed
		while intLcdLoop > 0:

			# show next button to press
			if intLcdLoop == 1:
				Lcd.ShowStr( "Agree? Left.... ", 2 )

			elif intLcdLoop == 2:
				Lcd.ShowStr( "Agree? .Down...", 2 )

			elif intLcdLoop == 3:
				Lcd.ShowStr( "Agree? ..Up.. ", 2 )

			elif intLcdLoop == 4:
				Lcd.ShowStr( "Agree? ...Right.   ", 2 )

			elif intLcdLoop == 5:
				Lcd.ShowStr( "Agree? ....Left ", 2 )

			# delay to debounce switch
			#time.sleep(0.5)

			# wait until no buttons pressed to debounce last switch
	##                        while GPIO.input(PIN_BTN_LEFT) or GPIO.input(PIN_BTN_RIGHT) or GPIO.input(PIN_BTN_DOWN) or GPIO.input(PIN_BTN_UP):
	##                                print( "debounce Loop: " + str(intLcdLoop) + " Btns: Left " + str(GPIO.input(PIN_BTN_LEFT)) + "\tRight " + str(GPIO.input(PIN_BTN_RIGHT)) + "\tDown " + str(GPIO.input(PIN_BTN_DOWN)) + "\tUp " + str(GPIO.input(PIN_BTN_UP)) )
	##                                time.sleep( 0.1 )
	##
	##                        print( "debounced Loop: " + str(intLcdLoop) + " Btns: Left " + str(GPIO.input(PIN_BTN_LEFT)) + "\tRight " + str(GPIO.input(PIN_BTN_RIGHT)) + "\tDown " + str(GPIO.input(PIN_BTN_DOWN)) + "\tUp " + str(GPIO.input(PIN_BTN_UP)) )
			DebounceBtns( 10 )

			# wait until next button pressed to continue
			#while not (GPIO.input(PIN_BTN_LEFT) or GPIO.input(PIN_BTN_RIGHT) or GPIO.input(PIN_BTN_DOWN) or GPIO.input(PIN_BTN_UP)):
			while not AnyBtnPressed( ):
				#print( "Wait on Loop: " + str(intLcdLoop) + " Btns: Left " + str(GPIO.input(PIN_BTN_LEFT)) + "\tRight " + str(GPIO.input(PIN_BTN_RIGHT)) + "\tDown " + str(GPIO.input(PIN_BTN_DOWN)) + "\tUp " + str(GPIO.input(PIN_BTN_UP)) )
				time.sleep( 0.1 )

			# on next button press increase loop count if agreed or exit if didn't
			#if GPIO.input(PIN_BTN_LEFT) or GPIO.input(PIN_BTN_RIGHT) or GPIO.input(PIN_BTN_DOWN) or GPIO.input(PIN_BTN_UP):
			if True:
				#print( "Key on Loop: " + str(intLcdLoop) + " Btns: Left " + str(GPIO.input(PIN_BTN_LEFT)) + "\tRight " + str(GPIO.input(PIN_BTN_RIGHT)) + "\tDown " + str(GPIO.input(PIN_BTN_DOWN)) + "\tUp " + str(GPIO.input(PIN_BTN_UP)) )
				print( "Key on Loop: " + str(intLcdLoop) + " Btns: Left " + str(BtnOn( aBTN_LEFT )) + "\tRight " + str(BtnOn( aBTN_RIGHT )) + "\tDown " + str(BtnOn( aBTN_DOWN )) + "\tUp " + str(BtnOn( aBTN_UP )) + "\tOK " + str(BtnOn( aBTN_OK )) )


				if intLcdLoop == 1:
					#if not GPIO.input(PIN_BTN_LEFT):
					if not BtnOn( aBTN_LEFT ):
						intLcdLoop = 0

				elif intLcdLoop == 2:
					if not BtnOn( aBTN_DOWN ):
						intLcdLoop = 0

				elif intLcdLoop == 3:
					if not BtnOn( aBTN_UP ):
						intLcdLoop = 0

				elif intLcdLoop == 4:
					if not BtnOn( aBTN_RIGHT ):
						intLcdLoop = 0

				elif intLcdLoop == 5:
					#if GPIO.input(PIN_BTN_LEFT):
					if BtnOn( aBTN_LEFT ):
						#intLcdLoop += 1

						# set configuration variable to prevent future prompting
						SetConfigVar( "dblVsnDisclaimed", CODE_VERSION )
						bolDisclaimed = True
						break
					else:
						intLcdLoop = 0


				# if button press was wrong exit
				if intLcdLoop == 0:
					Lcd.ShowStr( " You disagreed  ", 2 )
					time.sleep( 4 )

					Lcd.ShowStr( " If you change  ", 1 )
					Lcd.ShowStr( "your mind, power", 2 )
					time.sleep( 4 )

					Lcd.ShowStr( "off the unit and", 1 )
					Lcd.ShowStr( "on again. Bye :)", 2 )
					time.sleep( 4 )
					break

				# else button press was ok so increase loop count for next pass
				else:
					intLcdLoop += 1

				#print( "Now Loop: " + str(intLcdLoop) + " Btns: Left " + str(GPIO.input(PIN_BTN_LEFT)) + "\tRight " + str(GPIO.input(PIN_BTN_RIGHT)) + "\tDown " + str(GPIO.input(PIN_BTN_DOWN)) + "\tUp " + str(GPIO.input(PIN_BTN_UP)) )
				print( "Now Loop: " + str(intLcdLoop) + " Btns: Left " + str(BtnOn( aBTN_LEFT )) + "\tRight " + str(BtnOn( aBTN_RIGHT )) + "\tDown " + str(BtnOn( aBTN_DOWN )) + "\tUp " + str(BtnOn( aBTN_UP )) + "\tOK " + str(BtnOn( aBTN_OK )) )


		# return true only if user agreed to disclaimer
		return bolDisclaimed

	# put controller in welocome mode to greet user
	def UserWelcome( ):

		# send simple welcome text...
	# 		Lcd.ShowStr( "       Hi       ", 1 )
	# 		Lcd.ShowStr( "                ", 2 )
	#
	# 		LcdWait(1.5)
	#
	# 		Lcd.ShowStr( "Welcome to your ", 1 )
	# 		Lcd.ShowStr( "   new smile    ", 2 )
	#
	# 		LcdWait( 3 )
	#
	# 		Lcd.ShowStr( "   new smile :) ", 2 )
	#
	# 		LcdWait(1.5)
	#
	# 		Lcd.ShowStr( "   new smile ;) ", 2 )
	#
	# 		LcdWait(0.8)
	#
	# 		Lcd.ShowStr( "   new smile :) ", 2 )
	#
	# 		LcdWait(1.2)


		# send scrolling welcome text...
		SCROLL_DELAY = 0.1

		Lcd.ShowStr( "       Hi       ", 1 )
		Lcd.ShowStr( "                ", 2 )

		LcdWait( 1.5 )

		Lcd.ShowStr( "Welcome         ", 1 )
		LcdWait( 0.8 )
		Lcd.ShowStr( "Welcome to      ", 1 )
		LcdWait( 0.4 )
		Lcd.ShowStr( "Welcome to your ", 1 )
		LcdWait( 0.6 )

		Lcd.ShowStr( "new...          ", 2 )
		LcdWait( 1 )

		Lcd.ShowStr( "new             ", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new            S", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new           Su", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new          Sus", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new         Sust", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new        Susta", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new       Sustai", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new      Sustain", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new     Sustaina", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new    Sustainab", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new   Sustainabl", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new  Sustainably", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new Sustainably ", 2 )
		LcdWait( 2.5 )

		Lcd.ShowStr( "new s           ", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new s          M", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new s         Ma", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new s        Man", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new s       Mana", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new s      Manag", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new s     Manage", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new s    Managed", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new s   Managed ", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new s  Managed  ", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new s Managed   ", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new sManaged    ", 2 )
		LcdWait( 2 )

		Lcd.ShowStr( "new sm          ", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new sm         I", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new sm        In", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new sm       Int", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new sm      Inte", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new sm     Intel", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new sm    Inteli", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new sm   Intelig", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new sm  Intelige", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new sm Inteligen", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new smInteligent", 2 )
		LcdWait( 2 )

		Lcd.ShowStr( "new smi         ", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new smi        L", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new smi       Lo", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new smi      Loc", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new smi     Loca", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new smi    Local", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new smi   Local ", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new smi  Local  ", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new smi Local   ", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new smiLocal    ", 2 )
		LcdWait( 2 )

		Lcd.ShowStr( "new smil       E", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new smil      En", 2 )
		LcdWait( SCROLL_DELAY )
		Lcd.ShowStr( "new smil     Ene", 2 )
		LcdWa] Kernel command line: dma.dmachans=0x7f35 bcm2708_fb.fbwidth=1280 bcm2708_fb.fbheight=720 bcm2708.boardrev=0x9000c1 bcm2708.serial=0x14efb6d8 smsc95xx.macaddr=B8:27:EB:EF:B6:D8 bcm2708_fb.fbswap=1 bcm2708.uart_clock=48000000 bcm2708.disk_led_gpio=47 vc_mem.mem_base=0x1ec00000 vc_mem.mem_size=0x20000000  dwc_otg.lpm_enable=0 console=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait modules-load=dwc2,g_ether quiet splash plymouth.ignore-serial-consoles
Jul 17 15:12:09 raspberrypi kernel: [    0.000000] PID hash table entries: 2048 (order: 1, 8192 bytes)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000] Dentry cache hash table entries: 65536 (order: 6, 262144 bytes)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000] Inode-cache hash table entries: 32768 (order: 5, 131072 bytes)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000] Memory: 436516K/458752K available (6059K kernel code, 437K rwdata, 1844K rodata, 380K init, 726K bss, 14044K reserved, 8192K cma-reserved)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000] Virtual kernel memory layout:
Jul 17 15:12:09 raspberrypi kernel: [    0.000000]     vector  : 0xffff0000 - 0xffff1000   (   4 kB)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000]     fixmap  : 0xffc00000 - 0xfff00000   (3072 kB)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000]     vmalloc : 0xdc800000 - 0xff800000   ( 560 MB)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000]     lowmem  : 0xc0000000 - 0xdc000000   ( 448 MB)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000]     modules : 0xbf000000 - 0xc0000000   (  16 MB)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000]       .text : 0xc0008000 - 0xc07c0008   (7905 kB)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000]       .init : 0xc07c1000 - 0xc0820000   ( 380 kB)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000]       .data : 0xc0820000 - 0xc088d490   ( 438 kB)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000]        .bss : 0xc088d490 - 0xc0943050   ( 727 kB)
Jul 17 15:12:09 raspberrypi kernel: [    0.000000] SLUB: HWalign=32, Order=0-3, MinObjects=0, CPUs=1, Nodes=1
Jul 17 15:12:09 raspberrypi kernel: [    0.000000] NR_IRQS:16 nr_irqs:16 16
Jul 17 15:12:09 raspberrypi kernel: [    0.000028] sched_clock: 32 bits at 1000kHz, resolution 1000ns, wraps every 2147483647500ns
Jul 17 15:12:09 raspberrypi kernel: [    0.000071] clocksource: timer: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 1911260446275 ns
Jul 17 15:12:09 raspberrypi kernel: [    0.000172] bcm2835: system timer (irq = 27)
Jul 17 15:12:09 raspberrypi kernel: [    0.000482] Console: colour dummy device 80x30
Jul 17 15:12:09 raspberrypi kernel: [    0.000722] console [tty1] enabled
Jul 17 15:12:09 raspberrypi kernel: [    0.000753] Calibrating delay loop... 697.95 BogoMIPS (lpj=3489792)
Jul 17 15:12:09 raspberrypi kernel: [    0.060311] pid_max: default: 32768 minimum: 301
Jul 17 15:12:09 raspberrypi kernel: [    0.060688] Mount-cache hash table entries: 1024 (order: 0, 4096 bytes)
Jul 17 15:12:09 raspberrypi kernel: [    0.060717] Mountpoint-cache hash table entries: 1024 (order: 0, 4096 bytes)
Jul 17 15:12:09 raspberrypi kernel: [    0.061713] Disabling cpuset control group subsystem
Jul 17 15:12:09 raspberrypi kernel: [    0.061765] Initializing cgroup subsys io
Jul 17 15:12:09 raspberrypi kernel: [    0.061803] Initializing cgroup subsys memory
Jul 17 15:12:09 raspberrypi kernel: [    0.061866] Initializing cgroup subsys devices
Jul 17 15:12:09 raspberrypi kernel: [    0.061898] Initializing cgroup subsys freezer
Jul 17 15:12:09 raspberrypi kernel: [    0.061928] Initializing cgroup subsys net_cls
Jul 17 15:12:09 raspberrypi kernel: [    0.062015] CPU: Testing write buffer coherency: ok
Jul 17 15:12:09 raspberrypi kernel: [    0.062093] ftrace: allocating 20645 entries in 61 pages
Jul 17 15:12:09 raspberrypi kernel: [    0.172643] Setting up static identity map for 0x81c0 - 0x81f8
Jul 17 15:12:09 raspberrypi kernel: [    0.174493] devtmpfs: initialized
Jul 17 15:12:09 raspberrypi kernel: [    0.184097] VFP support v0.3: implementor 41 architecture 1 part 20 variant b rev 5
Jul 17 15:12:09 raspberrypi kernel: [    0.184617] clocksource: jiffies: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 19112604462750000 ns
Jul 17 15:12:09 raspberrypi kernel: [    0.186422] pinctrl core: initialized pinctrl subsystem
Jul 17 15:12:09 raspberrypi kernel: [    0.187298] NET: Registered protocol family 16
Jul 17 15:12:09 raspberrypi kernel: [    0.193060] DMA: preallocated 4096 KiB pool for atomic coherent allocations
Jul 17 15:12:09 raspberrypi kernel: [    0.201797] hw-breakpoint: found 6 breakpoint and 1 watchpoint registers.
Jul 17 15:12:09 raspberrypi kernel: [    0.201827] hw-breakpoint: maximum watchpoint size is 4 bytes.
Jul 17 15:12:09 raspberrypi kernel: [    0.202005] Serial: AMBA PL011 UART driver
Jul 17 15:12:09 raspberrypi kernel: [    0.202512] 20201000.uart: ttyAMA0 at MMIO 0x20201000 (irq = 81, base_baud = 0) is a PL011 rev2
Jul 17 15:12:09 raspberrypi kernel: [    0.202904] console [ttyAMA0] enabled
Jul 17 15:12:09 raspberrypi kernel: [    0.203646] bcm2835-mbox 2000b880.mailbox: mailbox enabled
Jul 17 15:12:09 raspberrypi kernel: [    0.247848] bcm2835-dma 20007000.dma: DMA legacy API manager at f2007000, dmachans=0x1
Jul 17 15:12:09 raspberrypi kernel: [    0.248730] SCSI subsystem initialized
Jul 17 15:12:09 raspberrypi kernel: [    0.249078] usbcore: registered new interface driver usbfs
Jul 17 15:12:09 raspberrypi kernel: [    0.249218] usbcore: registered new interface driver hub
Jul 17 15:12:09 raspberrypi kernel: [    0.249428] usbcore: registered new device driver usb
Jul 17 15:12:09 raspberrypi kernel: [    0.252557] raspberrypi-firmware soc:firmware: Attached to firmware from 2016-11-25 16:03
Jul 17 15:12:09 raspberrypi kernel: [    0.280460] clocksource: Switched to clocksource timer
Jul 17 15:12:09 raspberrypi kernel: [    0.333255] FS-Cache: Loaded
Jul 17 15:12:09 raspberrypi kernel: [    0.333659] CacheFiles: Loaded
Jul 17 15:12:09 raspberrypi kernel: [    0.353084] NET: Registered protocol family 2
Jul 17 15:12:09 raspberrypi kernel: [    0.354423] TCP established hash table entries: 4096 (order: 2, 16384 bytes)
Jul 17 15:12:09 raspberrypi kernel: [    0.354529] TCP bind hash table entries: 4096 (order: 2, 16384 bytes)
Jul 17 15:12:09 raspberrypi kernel: [    0.354632] TCP: Hash tables configured (established 4096 bind 4096)
Jul 17 15:12:09 raspberrypi kernel: [    0.354737] UDP hash table entries: 256 (order: 0, 4096 bytes)
Jul 17 15:12:09 raspberrypi kernel: [    0.354777] UDP-Lite hash table entries: 256 (order: 0, 4096 bytes)
Jul 17 15:12:09 raspberrypi kernel: [    0.355120] NET: Registered protocol family 1
Jul 17 15:12:09 raspberrypi kernel: [    0.355730] RPC: Registered named UNIX socket transport module.
Jul 17 15:12:09 raspberrypi kernel: [    0.355758] RPC: Registered udp transport module.
Jul 17 15:12:09 raspberrypi kernel: [    0.355771] RPC: Registered tcp transport module.
Jul 17 15:12:09 raspberrypi kernel: [    0.355784] RPC: Registered tcp NFSv4.1 backchannel transport module.
Jul 17 15:12:09 raspberrypi kernel: [    0.357218] hw perfevents: enabled with armv6_1176 PMU driver, 3 counters available
Jul 17 15:12:09 raspberrypi kernel: [    0.358618] futex hash table entries: 256 (order: -1, 3072 bytes)
Jul 17 15:12:09 raspberrypi kernel: [    0.375276] VFS: Disk quotas dquot_6.6.0
Jul 17 15:12:09 raspberrypi kernel: [    0.375700] VFS: Dquot-cache hash table entries: 1024 (order 0, 4096 bytes)
Jul 17 15:12:09 raspberrypi kernel: [    0.378391] FS-Cache: Netfs 'nfs' registered for caching
Jul 17 15:12:09 raspberrypi kernel: [    0.379779] NFS: Registering the id_resolver key type
Jul 17 15:12:09 raspberrypi kernel: [    0.379903] Key type id_resolver registered
Jul 17 15:12:09 raspberrypi kernel: [    0.379923] Key type id_legacy registered
Jul 17 15:12:09 raspberrypi kernel: [    0.384366] Block layer SCSI generic (bsg) driver version 0.4 loaded (major 252)
Jul 17 15:12:09 raspberrypi kernel: [    0.384806] io scheduler noop registered
Jul 17 15:12:09 raspberrypi kernel: [    0.384849] io scheduler deadline registered (default)
Jul 17 15:12:09 raspberrypi kernel: [    0.385275] io scheduler cfq registered
Jul 17 15:12:09 raspberrypi kernel: [    0.388016] BCM2708FB: allocated DMA memory 5b800000
Jul 17 15:12:09 raspberrypi kernel: [    0.388091] BCM2708FB: allocated DMA channel 0 @ f2007000
Jul 17 15:12:09 raspberrypi kernel: [    0.411203] Console: switching to colour frame buffer device 160x45
Jul 17 15:12:09 raspberrypi kernel: [    1.345178] bcm2835-rng 20104000.rng: hwrng registered
Jul 17 15:12:09 raspberrypi kernel: [    1.345527] vc-cma: Videocore CMA driver
Jul 17 15:12:09 raspberrypi kernel: [    1.345555] vc-cma: vc_cma_base      = 0x00000000
Jul 17 15:12:09 raspberrypi kernel: [    1.345568] vc-cma: vc_cma_size      = 0x00000000 (0 MiB)
Jul 17 15:12:09 raspberrypi kernel: [    1.345580] vc-cma: vc_cma_initial   = 0x00000000 (0 MiB)
Jul 17 15:12:09 raspberrypi kernel: [    1.346039] vc-mem: phys_addr:0x00000000 mem_base=0x1ec00000 mem_size:0x20000000(512 MiB)
Jul 17 15:12:09 raspberrypi kernel: [    1.372048] brd: module loaded
Jul 17 15:12:09 raspberrypi kernel: [    1.384764] loop: module loaded
Jul 17 15:12:09 raspberrypi kernel: [    1.385920] vchiq: vchiq_init_state: slot_zero = 0xdb880000, is_master = 0
Jul 17 15:12:09 raspberrypi kernel: [    1.388474] Loading iSCSI transport class v2.0-870.
Jul 17 15:12:09 raspberrypi kernel: [    1.389819] usbcore: registered new interface driver smsc95xx
Jul 17 15:12:09 raspberrypi kernel: [    1.389940] dwc_otg: version 3.00a 10-AUG-2012 (platform bus)
Jul 17 15:12:09 raspberrypi kernel: [    1.391189] usbcore: registered new interface driver usb-storage
Jul 17 15:12:09 raspberrypi kernel: [    1.391905] mousedev: PS/2 mouse device common for all mice
Jul 17 15:12:09 raspberrypi kernel: [    1.393420] bcm2835-cpufreq: min=700000 max=700000
Jul 17 15:12:09 raspberrypi kernel: [    1.393905] sdhci: Secure Digital Host Controller Interface driver
Jul 17 15:12:09 raspberrypi kernel: [    1.393930] sdhci: Copyright(c) Pierre Ossman
Jul 17 15:12:09 raspberrypi kernel: [    1.394520] sdhost: log_buf @ db810000 (5b810000)
Jul 17 15:12:09 raspberrypi kernel: [    1.450543] mmc0: sdhost-bcm2835 loaded - DMA enabled (>1)
Jul 17 15:12:09 raspberrypi kernel: [    1.451125] sdhci-pltfm: SDHCI platform and OF driver helper
Jul 17 15:12:09 raspberrypi kernel: [    1.451989] ledtrig-cpu: registered to indicate activity on CPUs
Jul 17 15:12:09 raspberrypi kernel: [    1.452280] hidraw: raw HID events driver (C) Jiri Kosina
Jul 17 15:12:09 raspberrypi kernel: [    1.452618] usbcore: registered new interface driver usbhid
Jul 17 15:12:09 raspberrypi kernel: [    1.452636] usbhid: USB HID core driver
Jul 17 15:12:09 raspberrypi kernel: [    1.473722] Initializing XFRM netlink socket
Jul 17 15:12:09 raspberrypi kernel: [    1.473800] NET: Registered protocol family 17
Jul 17 15:12:09 raspberrypi kernel: [    1.474031] Key type dns_resolver registered
Jul 17 15:12:09 raspberrypi kernel: [    1.476288] registered taskstats version 1
Jul 17 15:12:09 raspberrypi kernel: [    1.476651] vc-sm: Videocore shared memory driver
Jul 17 15:12:09 raspberrypi kernel: [    1.476686] [vc_sm_connected_init]: start
Jul 17 15:12:09 raspberrypi kernel: [    1.477760] [vc_sm_connected_init]: end - returning 0
Jul 17 15:12:09 raspberrypi kernel: [    1.478433] of_cfs_init
Jul 17 15:12:09 raspberrypi kernel: [    1.478599] of_cfs_init: OK
Jul 17 15:12:09 raspberrypi kernel: [    1.480157] Waiting for root device /dev/mmcblk0p2...
Jul 17 15:12:09 raspberrypi kernel: [    1.560272] mmc0: host does not support reading read-only switch, assuming write-enable
Jul 17 15:12:09 raspberrypi kernel: [    1.563297] mmc0: new high speed SDHC card at address e624
Jul 17 15:12:09 raspberrypi kernel: [    1.564395] mmcblk0: mmc0:e624 SU08G 7.40 GiB
Jul 17 15:12:09 raspberrypi kernel: [    1.569605]  mmcblk0: p1 p2
Jul 17 15:12:09 raspberrypi kernel: [    1.594802] EXT4-fs (mmcblk0p2): mounted filesystem with ordered data mode. Opts: (null)
Jul 17 15:12:09 raspberrypi kernel: [    1.594915] VFS: Mounted root (ext4 filesystem) readonly on device 179:2.
Jul 17 15:12:09 raspberrypi kernel: [    1.605185] devtmpfs: mounted
Jul 17 15:12:09 raspberrypi kernel: [    1.606519] Freeing unused kernel memory: 380K (c07c1000 - c0820000)
Jul 17 15:12:09 raspberrypi kernel: [    1.917282] random: systemd: uninitialized urandom read (16 bytes read, 8 bits of entropy available)
Jul 17 15:12:09 raspberrypi kernel: [    2.070793] NET: Registered protocol family 10
Jul 17 15:12:09 raspberrypi kernel: [    2.284987] uart-pl011 20201000.uart: no DMA platform data
Jul 17 15:12:09 raspberrypi kernel: [    2.302517] random: systemd-sysv-ge: uninitialized urandom read (16 bytes read, 10 bits of entropy available)
Jul 17 15:12:09 raspberrypi kernel: [    2.505281] random: systemd: uninitialized urandom read (16 bytes read, 12 bits of entropy available)
Jul 17 15:12:09 raspberrypi kernel: [    2.507487] random: systemd: uninitialized urandom read (16 bytes read, 12 bits of entropy available)
Jul 17 15:12:09 raspberrypi kernel: [    2.509967] random: systemd: uninitialized urandom read (16 bytes read, 12 bits of entropy available)
Jul 17 15:12:09 raspberrypi kernel: [    2.543671] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 17 15:12:09 raspberrypi kernel: [    2.545385] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 17 15:12:09 raspberrypi kernel: [    2.545843] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 17 15:12:09 raspberrypi kernel: [    2.633691] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 17 15:12:09 raspberrypi kernel: [    2.659563] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 17 15:12:09 raspberrypi kernel: [    3.830701] dwc2 20980000.usb: EPs: 8, dedicated fifos, 4080 entries in SPRAM
Jul 17 15:12:09 raspberrypi kernel: [    4.393758] dwc2 20980000.usb: DWC OTG Controller
Jul 17 15:12:09 raspberrypi kernel: [    4.393869] dwc2 20980000.usb: new USB bus registered, assigned bus number 1
Jul 17 15:12:09 raspberrypi kernel: [    4.393966] dwc2 20980000.usb: irq 33, io mem 0x00000000
Jul 17 15:12:09 raspberrypi kernel: [    4.394492] usb usb1: New USB device found, idVendor=1d6b, idProduct=0002
Jul 17 15:12:09 raspberrypi kernel: [    4.394527] usb usb1: New USB device strings: Mfr=3, Product=2, SerialNumber=1
Jul 17 15:12:09 raspberrypi kernel: [    4.394548] usb usb1: Product: DWC OTG Controller
Jul 17 15:12:09 raspberrypi kernel: [    4.394572] usb usb1: Manufacturer: Linux 4.4.34+ dwc2_hsotg
Jul 17 15:12:09 raspberrypi kernel: [    4.394590] usb usb1: SerialNumber: 20980000.usb
Jul 17 15:12:09 raspberrypi kernel: [    4.395906] hub 1-0:1.0: USB hub found
Jul 17 15:12:09 raspberrypi kernel: [    4.396025] hub 1-0:1.0: 1 port detected
Jul 17 15:12:09 raspberrypi kernel: [    4.526266] using random self ethernet address
Jul 17 15:12:09 raspberrypi kernel: [    4.526319] using random host ethernet address
Jul 17 15:12:09 raspberrypi kernel: [    4.527811] usb0: HOST MAC da:a4:b0:bf:10:92
Jul 17 15:12:09 raspberrypi kernel: [    4.527954] usb0: MAC e6:c6:8c:ac:35:05
Jul 17 15:12:09 raspberrypi kernel: [    4.528049] using random self ethernet address
Jul 17 15:12:09 raspberrypi kernel: [    4.528081] using random host ethernet address
Jul 17 15:12:09 raspberrypi kernel: [    4.528230] g_ether gadget: Ethernet Gadget, version: Memorial Day 2008
Jul 17 15:12:09 raspberrypi kernel: [    4.528254] g_ether gadget: g_ether ready
Jul 17 15:12:09 raspberrypi kernel: [    4.538686] dwc2 20980000.usb: bound driver g_ether
Jul 17 15:12:09 raspberrypi kernel: [    4.577829] dwc2 20980000.usb: new device is high-speed
Jul 17 15:12:09 raspberrypi kernel: [    4.612189] dwc2 20980000.usb: new address 1
Jul 17 15:12:09 raspberrypi kernel: [    4.625492] fuse init (API version 7.23)
Jul 17 15:12:09 raspberrypi kernel: [    4.650995] i2c /dev entries driver
Jul 17 15:12:09 raspberrypi kernel: [    5.833452] g_ether gadget: high-speed config #2: RNDIS
Jul 17 15:12:09 raspberrypi kernel: [    6.188904] bcm2835-wdt 20100000.watchdog: Broadcom BCM2835 watchdog timer
Jul 17 15:12:09 raspberrypi kernel: [    6.249006] gpiomem-bcm2835 20200000.gpiomem: Initialised: Registers at 0x20200000
Jul 17 15:12:09 raspberrypi kernel: [    6.431045] bcm2708_i2c 20804000.i2c: BSC1 Controller at 0x20804000 (irq 77) (baudrate 100000)
Jul 17 15:12:09 raspberrypi kernel: [    6.531537] EXT4-fs (mmcblk0p2): re-mounted. Opts: (null)
Jul 17 15:12:09 raspberrypi kernel: [   13.094810] random: nonblocking pool is initialized
Jul 17 15:12:09 raspberrypi kernel: [   15.447686] cfg80211: World regulatory domain updated:
Jul 17 15:12:09 raspberrypi kernel: [   15.447732] cfg80211:  DFS Master region: unset
Jul 17 15:12:09 raspberrypi kernel: [   15.447748] cfg80211:   (start_freq - end_freq @ bandwidth), (max_antenna_gain, max_eirp), (dfs_cac_time)
Jul 17 15:12:09 raspberrypi kernel: [   15.447796] cfg80211:   (2402000 KHz - 2472000 KHz @ 40000 KHz), (N/A, 2000 mBm), (N/A)
Jul 17 15:12:09 raspberrypi kernel: [   15.447816] cfg80211:   (2457000 KHz - 2482000 KHz @ 40000 KHz), (N/A, 2000 mBm), (N/A)
Jul 17 15:12:09 raspberrypi kernel: [   15.447835] cfg80211:   (2474000 KHz - 2494000 KHz @ 20000 KHz), (N/A, 2000 mBm), (N/A)
Jul 17 15:12:09 raspberrypi kernel: [   15.447856] cfg80211:   (5170000 KHz - 5250000 KHz @ 80000 KHz, 160000 KHz AUTO), (N/A, 2000 mBm), (N/A)
Jul 17 15:12:09 raspberrypi kernel: [   15.447876] cfg80211:   (5250000 KHz - 5330000 KHz @ 80000 KHz, 160000 KHz AUTO), (N/A, 2000 mBm), (0 s)
Jul 17 15:12:09 raspberrypi kernel: [   15.447942] cfg80211:   (5490000 KHz - 5730000 KHz @ 160000 KHz), (N/A, 2000 mBm), (0 s)
Jul 17 15:12:09 raspberrypi kernel: [   15.447961] cfg80211:   (5735000 KHz - 5835000 KHz @ 80000 KHz), (N/A, 2000 mBm), (N/A)
Jul 17 15:12:09 raspberrypi kernel: [   15.447980] cfg80211:   (57240000 KHz - 63720000 KHz @ 2160000 KHz), (N/A, 0 mBm), (N/A)
Jul 17 15:12:10 raspberrypi kernel: [   18.013270] Adding 102396k swap on /var/swap.  Priority:-1 extents:3 across:208896k SSFS
Jul 17 15:12:11 raspberrypi vncserver-x11[428]: ServerManager: Server started
Jul 17 15:12:13 raspberrypi vncserver-x11[428]: ConsoleDisplay: Cannot find a running X server on vt1
Jul 17 15:12:13 raspberrypi kernel: [   21.203013] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 17 15:12:16 raspberrypi vncserver-x11[428]: ConsoleDisplay: Found running X server (pid=484)
Jul 17 15:12:41 raspberrypi kernel: [   48.535378] Bluetooth: Core ver 2.21
Jul 17 15:12:41 raspberrypi kernel: [   48.535623] NET: Registered protocol family 31
Jul 17 15:12:41 raspberrypi kernel: [   48.535645] Bluetooth: HCI device and connection manager initialized
Jul 17 15:12:41 raspberrypi kernel: [   48.535689] Bluetooth: HCI socket layer initialized
Jul 17 15:12:41 raspberrypi kernel: [   48.535722] Bluetooth: L2CAP socket layer initialized
Jul 17 15:12:41 raspberrypi kernel: [   48.535786] Bluetooth: SCO socket layer initialized
Jul 17 15:12:41 raspberrypi kernel: [   49.045641] Bluetooth: BNEP (Ethernet Emulation) ver 1.3
Jul 17 15:12:41 raspberrypi kernel: [   49.045680] Bluetooth: BNEP filters: protocol multicast
Jul 17 15:12:41 raspberrypi kernel: [   49.045726] Bluetooth: BNEP socket layer initialized
Jul 17 15:12:48 raspberrypi org.gtk.Private.AfcVolumeMonitor[637]: Volume monitor alive
Jul 17 16:17:14 raspberrypi rsyslogd: [origin software="rsyslogd" swVersion="8.4.2" x-pid="383" x-info="http://www.rsyslog.com"] start
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Booting Linux on physical CPU 0x0
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Initializing cgroup subsys cpuset
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Initializing cgroup subsys cpu
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Initializing cgroup subsys cpuacct
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Linux version 4.4.34+ (dc4@dc4-XPS13-9333) (gcc version 4.9.3 (crosstool-NG crosstool-ng-1.22.0-88-g8460611) ) #930 Wed Nov 23 15:12:30 GMT 2016
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] CPU: ARMv6-compatible processor [410fb767] revision 7 (ARMv7), cr=00c5387d
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] CPU: PIPT / VIPT nonaliasing data cache, VIPT nonaliasing instruction cache
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Machine model: Raspberry Pi ? Rev 1.1
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] cma: Reserved 8 MiB at 0x1b400000
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Memory policy: Data cache writeback
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Built 1 zonelists in Zone order, mobility grouping on.  Total pages: 113680
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Kernel command line: dma.dmachans=0x7f35 bcm2708_fb.fbwidth=1280 bcm2708_fb.fbheight=720 bcm2708.boardrev=0x9000c1 bcm2708.serial=0x14efb6d8 smsc95xx.macaddr=B8:27:EB:EF:B6:D8 bcm2708_fb.fbswap=1 bcm2708.uart_clock=48000000 bcm2708.disk_led_gpio=47 vc_mem.mem_base=0x1ec00000 vc_mem.mem_size=0x20000000  dwc_otg.lpm_enable=0 console=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait modules-load=dwc2,g_ether quiet splash plymouth.ignore-serial-consoles
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] PID hash table entries: 2048 (order: 1, 8192 bytes)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Dentry cache hash table entries: 65536 (order: 6, 262144 bytes)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Inode-cache hash table entries: 32768 (order: 5, 131072 bytes)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Memory: 436516K/458752K available (6059K kernel code, 437K rwdata, 1844K rodata, 380K init, 726K bss, 14044K reserved, 8192K cma-reserved)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] Virtual kernel memory layout:
Jul 17 16:17:14 raspberrypi kernel: [    0.000000]     vector  : 0xffff0000 - 0xffff1000   (   4 kB)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000]     fixmap  : 0xffc00000 - 0xfff00000   (3072 kB)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000]     vmalloc : 0xdc800000 - 0xff800000   ( 560 MB)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000]     lowmem  : 0xc0000000 - 0xdc000000   ( 448 MB)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000]     modules : 0xbf000000 - 0xc0000000   (  16 MB)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000]       .text : 0xc0008000 - 0xc07c0008   (7905 kB)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000]       .init : 0xc07c1000 - 0xc0820000   ( 380 kB)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000]       .data : 0xc0820000 - 0xc088d490   ( 438 kB)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000]        .bss : 0xc088d490 - 0xc0943050   ( 727 kB)
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] SLUB: HWalign=32, Order=0-3, MinObjects=0, CPUs=1, Nodes=1
Jul 17 16:17:14 raspberrypi kernel: [    0.000000] NR_IRQS:16 nr_irqs:16 16
Jul 17 16:17:14 raspberrypi kernel: [    0.000027] sched_clock: 32 bits at 1000kHz, resolution 1000ns, wraps every 2147483647500ns
Jul 17 16:17:14 raspberrypi kernel: [    0.000070] clocksource: timer: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 1911260446275 ns
Jul 17 16:17:14 raspberrypi kernel: [    0.000172] bcm2835: system timer (irq = 27)
Jul 17 16:17:14 raspberrypi kernel: [    0.000486] Console: colour dummy device 80x30
Jul 17 16:17:14 raspberrypi kernel: [    0.000724] console [tty1] enabled
Jul 17 16:17:14 raspberrypi kernel: [    0.000754] Calibrating delay loop... 697.95 BogoMIPS (lpj=3489792)
Jul 17 16:17:14 raspberrypi kernel: [    0.060310] pid_max: default: 32768 minimum: 301
Jul 17 16:17:14 raspberrypi kernel: [    0.060692] Mount-cache hash table entries: 1024 (order: 0, 4096 bytes)
Jul 17 16:17:14 raspberrypi kernel: [    0.060721] Mountpoint-cache hash table entries: 1024 (order: 0, 4096 bytes)
Jul 17 16:17:14 raspberrypi kernel: [    0.061717] Disabling cpuset control group subsystem
Jul 17 16:17:14 raspberrypi kernel: [    0.061769] Initializing cgroup subsys io
Jul 17 16:17:14 raspberrypi kernel: [    0.061806] Initializing cgroup subsys memory
Jul 17 16:17:14 raspberrypi kernel: [    0.061867] Initializing cgroup subsys devices
Jul 17 16:17:14 raspberrypi kernel: [    0.061901] Initializing cgroup subsys freezer
Jul 17 16:17:14 raspberrypi kernel: [    0.061933] Initializing cgroup subsys net_cls
Jul 17 16:17:14 raspberrypi kernel: [    0.062018] CPU: Testing write buffer coherency: ok
Jul 17 16:17:14 raspberrypi kernel: [    0.062097] ftrace: allocating 20645 entries in 61 pages
Jul 17 16:17:14 raspberrypi kernel: [    0.172648] Setting up static identity map for 0x81c0 - 0x81f8
Jul 17 16:17:14 raspberrypi kernel: [    0.174500] devtmpfs: initialized
Jul 17 16:17:14 raspberrypi kernel: [    0.184094] VFP support v0.3: implementor 41 architecture 1 part 20 variant b rev 5
Jul 17 16:17:14 raspberrypi kernel: [    0.184617] clocksource: jiffies: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 19112604462750000 ns
Jul 17 16:17:14 raspberrypi kernel: [    0.186410] pinctrl core: initialized pinctrl subsystem
Jul 17 16:17:14 raspberrypi kernel: [    0.187288] NET: Registered protocol family 16
Jul 17 16:17:14 raspberrypi kernel: [    0.193050] DMA: preallocated 4096 KiB pool for atomic coherent allocations
Jul 17 16:17:14 raspberrypi kernel: [    0.201789] hw-breakpoint: found 6 breakpoint and 1 watchpoint registers.
Jul 17 16:17:14 raspberrypi kernel: [    0.201820] hw-breakpoint: maximum watchpoint size is 4 bytes.
Jul 17 16:17:14 raspberrypi kernel: [    0.201995] Serial: AMBA PL011 UART driver
Jul 17 16:17:14 raspberrypi kernel: [    0.202505] 20201000.uart: ttyAMA0 at MMIO 0x20201000 (irq = 81, base_baud = 0) is a PL011 rev2
Jul 17 16:17:14 raspberrypi kernel: [    0.202899] console [ttyAMA0] enabled
Jul 17 16:17:14 raspberrypi kernel: [    0.203648] bcm2835-mbox 2000b880.mailbox: mailbox enabled
Jul 17 16:17:14 raspberrypi kernel: [    0.247842] bcm2835-dma 20007000.dma: DMA legacy API manager at f2007000, dmachans=0x1
Jul 17 16:17:14 raspberrypi kernel: [    0.248725] SCSI subsystem initialized
Jul 17 16:17:14 raspberrypi kernel: [    0.249070] usbcore: registered new interface driver usbfs
Jul 17 16:17:14 raspberrypi kernel: [    0.249206] usbcore: registered new interface driver hub
Jul 17 16:17:14 raspberrypi kernel: [    0.249415] usbcore: registered new device driver usb
Jul 17 16:17:14 raspberrypi kernel: [    0.252563] raspberrypi-firmware soc:firmware: Attached to firmware from 2016-11-25 16:03
Jul 17 16:17:14 raspberrypi kernel: [    0.280455] clocksource: Switched to clocksource timer
Jul 17 16:17:14 raspberrypi kernel: [    0.333220] FS-Cache: Loaded
Jul 17 16:17:14 raspberrypi kernel: [    0.333628] CacheFiles: Loaded
Jul 17 16:17:14 raspberrypi kernel: [    0.353035] NET: Registered protocol family 2
Jul 17 16:17:14 raspberrypi kernel: [    0.354378] TCP established hash table entries: 4096 (order: 2, 16384 bytes)
Jul 17 16:17:14 raspberrypi kernel: [    0.354483] TCP bind hash table entries: 4096 (order: 2, 16384 bytes)
Jul 17 16:17:14 raspberrypi kernel: [    0.354587] TCP: Hash tables configured (established 4096 bind 4096)
Jul 17 16:17:14 raspberrypi kernel: [    0.354692] UDP hash table entries: 256 (order: 0, 4096 bytes)
Jul 17 16:17:14 raspberrypi kernel: [    0.354731] UDP-Lite hash table entries: 256 (order: 0, 4096 bytes)
Jul 17 16:17:14 raspberrypi kernel: [    0.355069] NET: Registered protocol family 1
Jul 17 16:17:14 raspberrypi kernel: [    0.355676] RPC: Registered named UNIX socket transport module.
Jul 17 16:17:14 raspberrypi kernel: [    0.355703] RPC: Registered udp transport module.
Jul 17 16:17:14 raspberrypi kernel: [    0.355715] RPC: Registered tcp transport module.
Jul 17 16:17:14 raspberrypi kernel: [    0.355728] RPC: Registered tcp NFSv4.1 backchannel transport module.
Jul 17 16:17:14 raspberrypi kernel: [    0.357157] hw perfevents: enabled with armv6_1176 PMU driver, 3 counters available
Jul 17 16:17:14 raspberrypi kernel: [    0.358559] futex hash table entries: 256 (order: -1, 3072 bytes)
Jul 17 16:17:14 raspberrypi kernel: [    0.375225] VFS: Disk quotas dquot_6.6.0
Jul 17 16:17:14 raspberrypi kernel: [    0.375647] VFS: Dquot-cache hash table entries: 1024 (order 0, 4096 bytes)
Jul 17 16:17:14 raspberrypi kernel: [    0.378337] FS-Cache: Netfs 'nfs' registered for caching
Jul 17 16:17:14 raspberrypi kernel: [    0.379724] NFS: Registering the id_resolver key type
Jul 17 16:17:14 raspberrypi kernel: [    0.379847] Key type id_resolver registered
Jul 17 16:17:14 raspberrypi kernel: [    0.379866] Key type id_legacy registered
Jul 17 16:17:14 raspberrypi kernel: [    0.384320] Block layer SCSI generic (bsg) driver version 0.4 loaded (major 252)
Jul 17 16:17:14 raspberrypi kernel: [    0.384754] io scheduler noop registered
Jul 17 16:17:14 raspberrypi kernel: [    0.384798] io scheduler deadline registered (default)
Jul 17 16:17:14 raspberrypi kernel: [    0.385219] io scheduler cfq registered
Jul 17 16:17:14 raspberrypi kernel: [    0.387960] BCM2708FB: allocated DMA memory 5b800000
Jul 17 16:17:14 raspberrypi kernel: [    0.388035] BCM2708FB: allocated DMA channel 0 @ f2007000
Jul 17 16:17:14 raspberrypi kernel: [    0.411205] Console: switching to colour frame buffer device 160x45
Jul 17 16:17:14 raspberrypi kernel: [    1.345382] bcm2835-rng 20104000.rng: hwrng registered
Jul 17 16:17:14 raspberrypi kernel: [    1.345730] vc-cma: Videocore CMA driver
Jul 17 16:17:14 raspberrypi kernel: [    1.345752] vc-cma: vc_cma_base      = 0x00000000
Jul 17 16:17:14 raspberrypi kernel: [    1.345765] vc-cma: vc_cma_size      = 0x00000000 (0 MiB)
Jul 17 16:17:14 raspberrypi kernel: [    1.345780] vc-cma: vc_cma_initial   = 0x00000000 (0 MiB)
Jul 17 16:17:14 raspberrypi kernel: [    1.346238] vc-mem: phys_addr:0x00000000 mem_base=0x1ec00000 mem_size:0x20000000(512 MiB)
Jul 17 16:17:14 raspberrypi kernel: [    1.372236] brd: module loaded
Jul 17 16:17:14 raspberrypi kernel: [    1.384887] loop: module loaded
Jul 17 16:17:14 raspberrypi kernel: [    1.386105] vchiq: vchiq_init_state: slot_zero = 0xdb880000, is_master = 0
Jul 17 16:17:14 raspberrypi kernel: [    1.388705] Loading iSCSI transport class v2.0-870.
Jul 17 16:17:14 raspberrypi kernel: [    1.390049] usbcore: registered new interface driver smsc95xx
Jul 17 16:17:14 raspberrypi kernel: [    1.390171] dwc_otg: version 3.00a 10-AUG-2012 (platform bus)
Jul 17 16:17:14 raspberrypi kernel: [    1.391482] usbcore: registered new interface driver usb-storage
Jul 17 16:17:14 raspberrypi kernel: [    1.392191] mousedev: PS/2 mouse device common for all mice
Jul 17 16:17:14 raspberrypi kernel: [    1.393685] bcm2835-cpufreq: min=700000 max=700000
Jul 17 16:17:14 raspberrypi kernel: [    1.394169] sdhci: Secure Digital Host Controller Interface driver
Jul 17 16:17:14 raspberrypi kernel: [    1.394191] sdhci: Copyright(c) Pierre Ossman
Jul 17 16:17:14 raspberrypi kernel: [    1.394795] sdhost: log_buf @ db810000 (5b810000)
Jul 17 16:17:14 raspberrypi kernel: [    1.450538] mmc0: sdhost-bcm2835 loaded - DMA enabled (>1)
Jul 17 16:17:14 raspberrypi kernel: [    1.451117] sdhci-pltfm: SDHCI platform and OF driver helper
Jul 17 16:17:14 raspberrypi kernel: [    1.451982] ledtrig-cpu: registered to indicate activity on CPUs
Jul 17 16:17:14 raspberrypi kernel: [    1.452288] hidraw: raw HID events driver (C) Jiri Kosina
Jul 17 16:17:14 raspberrypi kernel: [    1.452657] usbcore: registered new interface driver usbhid
Jul 17 16:17:14 raspberrypi kernel: [    1.452682] usbhid: USB HID core driver
Jul 17 16:17:14 raspberrypi kernel: [    1.473768] Initializing XFRM netlink socket
Jul 17 16:17:14 raspberrypi kernel: [    1.473847] NET: Registered protocol family 17
Jul 17 16:17:14 raspberrypi kernel: [    1.474070] Key type dns_resolver registered
Jul 17 16:17:14 raspberrypi kernel: [    1.476331] registered taskstats version 1
Jul 17 16:17:14 raspberrypi kernel: [    1.476680] vc-sm: Videocore shared memory driver
Jul 17 16:17:14 raspberrypi kernel: [    1.476716] [vc_sm_connected_init]: start
Jul 17 16:17:14 raspberrypi kernel: [    1.477793] [vc_sm_connected_init]: end - returning 0
Jul 17 16:17:14 raspberrypi kernel: [    1.478467] of_cfs_init
Jul 17 16:17:14 raspberrypi kernel: [    1.478632] of_cfs_init: OK
Jul 17 16:17:14 raspberrypi kernel: [    1.480181] Waiting for root device /dev/mmcblk0p2...
Jul 17 16:17:14 raspberrypi kernel: [    1.560270] mmc0: host does not support reading read-only switch, assuming write-enable
Jul 17 16:17:14 raspberrypi kernel: [    1.563311] mmc0: new high speed SDHC card at address e624
Jul 17 16:17:14 raspberrypi kernel: [    1.564371] mmcblk0: mmc0:e624 SU08G 7.40 GiB
Jul 17 16:17:14 raspberrypi kernel: [    1.569732]  mmcblk0: p1 p2
Jul 17 16:17:14 raspberrypi kernel: [    1.583570] EXT4-fs (mmcblk0p2): INFO: recovery required on readonly filesystem
Jul 17 16:17:14 raspberrypi kernel: [    1.583607] EXT4-fs (mmcblk0p2): write access will be enabled during recovery
Jul 17 16:17:14 raspberrypi kernel: [    2.174291] EXT4-fs (mmcblk0p2): orphan cleanup on readonly fs
Jul 17 16:17:14 raspberrypi kernel: [    2.174938] EXT4-fs (mmcblk0p2): 1 orphan inode deleted
Jul 17 16:17:14 raspberrypi kernel: [    2.174965] EXT4-fs (mmcblk0p2): recovery complete
Jul 17 16:17:14 raspberrypi kernel: [    2.210207] EXT4-fs (mmcblk0p2): mounted filesystem with ordered data mode. Opts: (null)
Jul 17 16:17:14 raspberrypi kernel: [    2.210314] VFS: Mounted root (ext4 filesystem) readonly on device 179:2.
Jul 17 16:17:14 raspberrypi kernel: [    2.214280] devtmpfs: mounted
Jul 17 16:17:14 raspberrypi kernel: [    2.215492] Freeing unused kernel memory: 380K (c07c1000 - c0820000)
Jul 17 16:17:14 raspberrypi kernel: [    2.517121] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 17 16:17:14 raspberrypi kernel: [    2.671512] NET: Registered protocol family 10
Jul 17 16:17:14 raspberrypi kernel: [    2.899356] uart-pl011 20201000.uart: no DMA platform data
Jul 17 16:17:14 raspberrypi kernel: [    2.912774] random: systemd-sysv-ge: uninitialized urandom read (16 bytes read, 15 bits of entropy available)
Jul 17 16:17:14 raspberrypi kernel: [    3.127466] random: systemd: uninitialized urandom read (16 bytes read, 17 bits of entropy available)
Jul 17 16:17:14 raspberrypi kernel: [    3.129655] random: systemd: uninitialized urandom read (16 bytes read, 17 bits of entropy available)
Jul 17 16:17:14 raspberrypi kernel: [    3.132304] random: systemd: uninitialized urandom read (16 bytes read, 17 bits of entropy available)
Jul 17 16:17:14 raspberrypi kernel: [    3.165864] random: systemd: uninitialized urandom read (16 bytes read, 18 bits of entropy available)
Jul 17 16:17:14 raspberrypi kernel: [    3.167456] random: systemd: uninitialized urandom read (16 bytes read, 18 bits of entropy available)
Jul 17 16:17:14 raspberrypi kernel: [    3.167862] random: systemd: uninitialized urandom read (16 bytes read, 18 bits of entropy available)
Jul 17 16:17:14 raspberrypi kernel: [    3.251417] random: systemd: uninitialized urandom read (16 bytes read, 18 bits of entropy available)
Jul 17 16:17:14 raspberrypi kernel: [    3.277138] random: systemd: uninitialized urandom read (16 bytes read, 18 bits of entropy available)
Jul 17 16:17:14 raspberrypi kernel: [    4.470653] dwc2 20980000.usb: EPs: 8, dedicated fifos, 4080 entries in SPRAM
Jul 17 16:17:14 raspberrypi kernel: [    5.041033] dwc2 20980000.usb: DWC OTG Controller
Jul 17 16:17:14 raspberrypi kernel: [    5.041141] dwc2 20980000.usb: new USB bus registered, assigned bus number 1
Jul 17 16:17:14 raspberrypi kernel: [    5.041242] dwc2 20980000.usb: irq 33, io mem 0x00000000
Jul 17 16:17:14 raspberrypi kernel: [    5.041726] usb usb1: New USB device found, idVendor=1d6b, idProduct=0002
Jul 17 16:17:14 raspberrypi kernel: [    5.041762] usb usb1: New USB device strings: Mfr=3, Product=2, SerialNumber=1
Jul 17 16:17:14 raspberrypi kernel: [    5.041782] usb usb1: Product: DWC OTG Controller
Jul 17 16:17:14 raspberrypi kernel: [    5.041806] usb usb1: Manufacturer: Linux 4.4.34+ dwc2_hsotg
Jul 17 16:17:14 raspberrypi kernel: [    5.041824] usb usb1: SerialNumber: 20980000.usb
Jul 17 16:17:14 raspberrypi kernel: [    5.043235] hub 1-0:1.0: USB hub found
Jul 17 16:17:14 raspberrypi kernel: [    5.043359] hub 1-0:1.0: 1 port detected
Jul 17 16:17:14 raspberrypi kernel: [    5.152477] using random self ethernet address
Jul 17 16:17:14 raspberrypi kernel: [    5.152526] using random host ethernet address
Jul 17 16:17:14 raspberrypi kernel: [    5.153961] usb0: HOST MAC 16:0b:b6:26:d1:e3
Jul 17 16:17:14 raspberrypi kernel: [    5.154092] usb0: MAC aa:cf:a2:db:e1:a3
Jul 17 16:17:14 raspberrypi kernel: [    5.154173] using random self ethernet address
Jul 17 16:17:14 raspberrypi kernel: [    5.154203] using random host ethernet address
Jul 17 16:17:14 raspberrypi kernel: [    5.154337] g_ether gadget: Ethernet Gadget, version: Memorial Day 2008
Jul 17 16:17:14 raspberrypi kernel: [    5.154360] g_ether gadget: g_ether ready
Jul 17 16:17:14 raspberrypi kernel: [    5.164766] dwc2 20980000.usb: bound driver g_ether
Jul 17 16:17:14 raspberrypi kernel: [    5.255841] fuse init (API version 7.23)
Jul 17 16:17:14 raspberrypi kernel: [    5.285656] i2c /dev entries driver
Jul 17 16:17:14 raspberrypi kernel: [    6.787520] bcm2835-wdt 20100000.watchdog: Broadcom BCM2835 watchdog timer
Jul 17 16:17:14 raspberrypi kernel: [    6.887774] gpiomem-bcm2835 20200000.gpiomem: Initialised: Registers at 0x20200000
Jul 17 16:17:14 raspberrypi kernel: [    6.920772] bcm2708_i2c 20804000.i2c: BSC1 Controller at 0x20804000 (irq 77) (baudrate 100000)
Jul 17 16:17:14 raspberrypi kernel: [    7.160570] EXT4-fs (mmcblk0p2): re-mounted. Opts: (null)
Jul 17 16:17:14 raspberrypi kernel: [   10.528651] dwc2 20980000.usb: new device is high-speed
Jul 17 16:17:14 raspberrypi kernel: [   10.628118] dwc2 20980000.usb: new address 1
Jul 17 16:17:14 raspberrypi kernel: [   11.222861] g_ether gadget: high-speed config #2: RNDIS
Jul 17 16:17:14 raspberrypi kernel: [   15.253504] random: nonblocking pool is initialized
Jul 17 16:17:14 raspberrypi kernel: [   15.976363] cfg80211: World regulatory domain updated:
Jul 17 16:17:14 raspberrypi kernel: [   15.976456] cfg80211:  DFS Master region: unset
Jul 17 16:17:14 raspberrypi kernel: [   15.976473] cfg80211:   (start_freq - end_freq @ bandwidth), (max_antenna_gain, max_eirp), (dfs_cac_time)
Jul 17 16:17:14 raspberrypi kernel: [   15.976502] cfg80211:   (2402000 KHz - 2472000 KHz @ 40000 KHz), (N/A, 2000 mBm), (N/A)
Jul 17 16:17:14 raspberrypi kernel: [   15.976520] cfg80211:   (2457000 KHz - 2482000 KHz @ 40000 KHz), (N/A, 2000 mBm), (N/A)
Jul 17 16:17:14 raspberrypi kernel: [   15.976537] cfg80211:   (2474000 KHz - 2494000 KHz @ 20000 KHz), (N/A, 2000 mBm), (N/A)
Jul 17 16:17:14 raspberrypi kernel: [   15.976562] cfg80211:   (5170000 KHz - 5250000 KHz @ 80000 KHz, 160000 KHz AUTO), (N/A, 2000 mBm), (N/A)
Jul 17 16:17:14 raspberrypi kernel: [   15.976582] cfg80211:   (5250000 KHz - 5330000 KHz @ 80000 KHz, 160000 KHz AUTO), (N/A, 2000 mBm), (0 s)
Jul 17 16:17:14 raspberrypi kernel: [   15.976599] cfg80211:   (5490000 KHz - 5730000 KHz @ 160000 KHz), (N/A, 2000 mBm), (0 s)
Jul 17 16:17:14 raspberrypi kernel: [   15.976617] cfg80211:   (5735000 KHz - 5835000 KHz @ 80000 KHz), (N/A, 2000 mBm), (N/A)
Jul 17 16:17:14 raspberrypi kernel: [   15.976639] cfg80211:   (57240000 KHz - 63720000 KHz @ 2160000 KHz), (N/A, 0 mBm), (N/A)
Jul 17 16:17:14 raspberrypi kernel: [   17.799969] Adding 102396k swap on /var/swap.  Priority:-1 extents:3 across:208896k SSFS
Jul 17 16:17:16 raspberrypi vncserver-x11[434]: ServerManager: Server started
Jul 17 16:17:18 raspberrypi vncserver-x11[434]: ConsoleDisplay: Cannot find a running X server on vt1
Jul 17 16:17:18 raspberrypi kernel: [   21.722560] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 17 16:17:21 raspberrypi vncserver-x11[434]: ConsoleDisplay: Found running X server (pid=480)
Jul 17 16:17:32 raspberrypi vncserver-x11[434]: Connections: connected: [fe80::4c4e:44a:585:fb99%usb0]::61449
Jul 17 16:17:38 raspberrypi vncserver-x11[434]: Connections: authenticated: [fe80::4c4e:44a:585:fb99%usb0]::61449, as pi (f permissions)
Jul 17 16:17:45 raspberrypi kernel: [   48.498297] Bluetooth: Core ver 2.21
Jul 17 16:17:45 raspberrypi kernel: [   48.511329] NET: Registered protocol family 31
Jul 17 16:17:45 raspberrypi kernel: [   48.511366] Bluetooth: HCI device and connection manager initialized
Jul 17 16:17:45 raspberrypi kernel: [   48.511412] Bluetooth: HCI socket layer initialized
Jul 17 16:17:45 raspberrypi kernel: [   48.511442] Bluetooth: L2CAP socket layer initialized
Jul 17 16:17:45 raspberrypi kernel: [   48.511516] Bluetooth: SCO socket layer initialized
Jul 17 16:17:45 raspberrypi kernel: [   48.650886] Bluetooth: BNEP (Ethernet Emulation) ver 1.3
Jul 17 16:17:45 raspberrypi kernel: [   48.650924] Bluetooth: BNEP filters: protocol multicast
Jul 17 16:17:45 raspberrypi kernel: [   48.650976] Bluetooth: BNEP socket layer initialized
Jul 17 16:17:54 raspberrypi kernel: [   57.590565] warning: process `colord-sane' used the deprecated sysctl system call with 8.1.2.
Jul 17 16:17:58 raspberrypi org.gtk.Private.AfcVolumeMonitor[641]: Volume monitor alive
Jul 18 05:28:41 raspberrypi kernel: [  333.796295] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 05:31:36 raspberrypi kernel: [  509.219222] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 05:31:55 raspberrypi kernel: [  527.559419] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 05:32:40 raspberrypi kernel: [  572.810521] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 06:25:16 raspberrypi rsyslogd: [origin software="rsyslogd" swVersion="8.4.2" x-pid="383" x-info="http://www.rsyslog.com"] rsyslogd was HUPed
Jul 18 06:32:50 raspberrypi kernel: [ 4183.117301] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 06:34:27 raspberrypi kernel: [ 4279.512236] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 06:34:53 raspberrypi kernel: [ 4305.582945] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 06:36:36 raspberrypi kernel: [ 4408.945466] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 06:38:08 raspberrypi kernel: [ 4500.516134] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 06:40:27 raspberrypi kernel: [ 4640.222630] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 06:43:46 raspberrypi kernel: [ 4839.369488] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 06:45:03 raspberrypi kernel: [ 4916.168976] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 06:48:29 raspberrypi kernel: [ 5121.712286] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 06:50:17 raspberrypi kernel: [ 5229.873608] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 06:50:47 raspberrypi kernel: [ 5259.740984] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 06:59:25 raspberrypi kernel: [ 5777.650545] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 07:00:08 raspberrypi kernel: [ 5821.008910] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 07:00:21 raspberrypi kernel: [ 5834.420155] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 07:00:58 raspberrypi kernel: [ 5870.548638] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 07:59:08 raspberrypi kernel: [ 5970.831482] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 07:02:18 raspberrypi kernel: [ 5991.373924] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 07:03:35 raspberrypi kernel: [ 6022.564132] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 07:06:22 raspberrypi kernel: [ 6189.278194] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 07:11:11 raspberrypi kernel: [ 6478.285513] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 08:13:14 raspberrypi vncserver-x11[434]: Connections: disconnected: [fe80::4c4e:44a:585:fb99%usb0]::61449 ([IdleTimeout] This connection has timed out through inactivity.)
Jul 18 09:34:54 raspberrypi vncserver-x11[434]: Connections: connected: [fe80::4c4e:44a:585:fb99%usb0]::53241
Jul 18 09:34:55 raspberrypi vncserver-x11[434]: Connections: authenticated: [fe80::4c4e:44a:585:fb99%usb0]::53241, as pi (f permissions)
Jul 18 09:35:26 raspberrypi kernel: [15139.298433] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 09:37:56 raspberrypi kernel: [15289.190306] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 10:07:22 raspberrypi kernel: [17054.657141] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 11:07:23 raspberrypi vncserver-x11[434]: Connections: disconnected: [fe80::4c4e:44a:585:fb99%usb0]::53241 ([IdleTimeout] This connection has timed out through inactivity.)
Jul 18 11:18:52 raspberrypi vncserver-x11[434]: Connections: connected: [fe80::4c4e:44a:585:fb99%usb0]::55610
Jul 18 11:18:54 raspberrypi vncserver-x11[434]: Connections: authenticated: [fe80::4c4e:44a:585:fb99%usb0]::55610, as pi (f permissions)
Jul 18 12:49:05 raspberrypi kernel: [26757.632643] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 12:56:26 raspberrypi kernel: [27199.611842] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 18 14:40:39 raspberrypi vncserver-x11[434]: Connections: disconnected: [fe80::4c4e:44a:585:fb99%usb0]::55610 ([IdleTimeout] This connection has timed out through inactivity.)
Jul 18 15:40:09 raspberrypi vncserver-x11[434]: Connections: connected: [fe80::4c4e:44a:585:fb99%usb0]::61551
Jul 18 15:40:11 raspberrypi vncserver-x11[434]: Connections: authenticated: [fe80::4c4e:44a:585:fb99%usb0]::61551, as pi (f permissions)
Jul 18 16:40:33 raspberrypi vncserver-x11[434]: Connections: disconnected: [fe80::4c4e:44a:585:fb99%usb0]::61551 ([IdleTimeout] This connection has timed out through inactivity.)
Jul 18 19:20:01 raspberrypi vncserver-x11[434]: Connections: connected: [fe80::4c4e:44a:585:fb99%usb0]::53356
Jul 18 19:20:03 raspberrypi vncserver-x11[434]: Connections: authenticated: [fe80::4c4e:44a:585:fb99%usb0]::53356, as pi (f permissions)
Jul 18 20:33:09 raspberrypi org.gtk.vfs.Daemon[641]: A connection to the bus can't be made
Jul 18 20:33:10 raspberrypi rsyslogd: [origin software="rsyslogd" swVersion="8.4.2" x-pid="383" x-info="http://www.rsyslog.com"] exiting on signal 15.
Jul 18 20:33:26 raspberrypi rsyslogd: [origin software="rsyslogd" swVersion="8.4.2" x-pid="375" x-info="http://www.rsyslog.com"] start
Jul 18 20:33:26 raspberrypi kernel: [    0.000000] Booting Linux on physical CPU 0x0
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] Initializing cgroup subsys cpuset
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] Initializing cgroup subsys cpu
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] Initializing cgroup subsys cpuacct
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] Linux version 4.4.34+ (dc4@dc4-XPS13-9333) (gcc version 4.9.3 (crosstool-NG crosstool-ng-1.22.0-88-g8460611) ) #930 Wed Nov 23 15:12:30 GMT 2016
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] CPU: ARMv6-compatible processor [410fb767] revision 7 (ARMv7), cr=00c5387d
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] CPU: PIPT / VIPT nonaliasing data cache, VIPT nonaliasing instruction cache
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] Machine model: Raspberry Pi ? Rev 1.1
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] cma: Reserved 8 MiB at 0x1b400000
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] Memory policy: Data cache writeback
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] Built 1 zonelists in Zone order, mobility grouping on.  Total pages: 113680
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] Kernel command line: dma.dmachans=0x7f35 bcm2708_fb.fbwidth=1280 bcm2708_fb.fbheight=720 bcm2708.boardrev=0x9000c1 bcm2708.serial=0x14efb6d8 smsc95xx.macaddr=B8:27:EB:EF:B6:D8 bcm2708_fb.fbswap=1 bcm2708.uart_clock=48000000 bcm2708.disk_led_gpio=47 vc_mem.mem_base=0x1ec00000 vc_mem.mem_size=0x20000000  dwc_otg.lpm_enable=0 console=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait modules-load=dwc2,g_ether quiet splash plymouth.ignore-serial-consoles
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] PID hash table entries: 2048 (order: 1, 8192 bytes)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] Dentry cache hash table entries: 65536 (order: 6, 262144 bytes)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] Inode-cache hash table entries: 32768 (order: 5, 131072 bytes)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] Memory: 436516K/458752K available (6059K kernel code, 437K rwdata, 1844K rodata, 380K init, 726K bss, 14044K reserved, 8192K cma-reserved)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] Virtual kernel memory layout:
Jul 18 20:33:27 raspberrypi kernel: [    0.000000]     vector  : 0xffff0000 - 0xffff1000   (   4 kB)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000]     fixmap  : 0xffc00000 - 0xfff00000   (3072 kB)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000]     vmalloc : 0xdc800000 - 0xff800000   ( 560 MB)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000]     lowmem  : 0xc0000000 - 0xdc000000   ( 448 MB)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000]     modules : 0xbf000000 - 0xc0000000   (  16 MB)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000]       .text : 0xc0008000 - 0xc07c0008   (7905 kB)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000]       .init : 0xc07c1000 - 0xc0820000   ( 380 kB)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000]       .data : 0xc0820000 - 0xc088d490   ( 438 kB)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000]        .bss : 0xc088d490 - 0xc0943050   ( 727 kB)
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] SLUB: HWalign=32, Order=0-3, MinObjects=0, CPUs=1, Nodes=1
Jul 18 20:33:27 raspberrypi kernel: [    0.000000] NR_IRQS:16 nr_irqs:16 16
Jul 18 20:33:27 raspberrypi kernel: [    0.000029] sched_clock: 32 bits at 1000kHz, resolution 1000ns, wraps every 2147483647500ns
Jul 18 20:33:27 raspberrypi kernel: [    0.000073] clocksource: timer: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 1911260446275 ns
Jul 18 20:33:27 raspberrypi kernel: [    0.000173] bcm2835: system timer (irq = 27)
Jul 18 20:33:27 raspberrypi kernel: [    0.000483] Console: colour dummy device 80x30
Jul 18 20:33:27 raspberrypi kernel: [    0.000723] console [tty1] enabled
Jul 18 20:33:27 raspberrypi kernel: [    0.000753] Calibrating delay loop... 697.95 BogoMIPS (lpj=3489792)
Jul 18 20:33:27 raspberrypi kernel: [    0.060314] pid_max: default: 32768 minimum: 301
Jul 18 20:33:27 raspberrypi kernel: [    0.060689] Mount-cache hash table entries: 1024 (order: 0, 4096 bytes)
Jul 18 20:33:27 raspberrypi kernel: [    0.060719] Mountpoint-cache hash table entries: 1024 (order: 0, 4096 bytes)
Jul 18 20:33:27 raspberrypi kernel: [    0.061714] Disabling cpuset control group subsystem
Jul 18 20:33:27 raspberrypi kernel: [    0.061766] Initializing cgroup subsys io
Jul 18 20:33:27 raspberrypi kernel: [    0.061804] Initializing cgroup subsys memory
Jul 18 20:33:27 raspberrypi kernel: [    0.061864] Initializing cgroup subsys devices
Jul 18 20:33:27 raspberrypi kernel: [    0.061898] Initializing cgroup subsys freezer
Jul 18 20:33:27 raspberrypi kernel: [    0.061930] Initializing cgroup subsys net_cls
Jul 18 20:33:27 raspberrypi kernel: [    0.062016] CPU: Testing write buffer coherency: ok
Jul 18 20:33:27 raspberrypi kernel: [    0.062095] ftrace: allocating 20645 entries in 61 pages
Jul 18 20:33:27 raspberrypi kernel: [    0.172716] Setting up static identity map for 0x81c0 - 0x81f8
Jul 18 20:33:27 raspberrypi kernel: [    0.174569] devtmpfs: initialized
Jul 18 20:33:27 raspberrypi kernel: [    0.184175] VFP support v0.3: implementor 41 architecture 1 part 20 variant b rev 5
Jul 18 20:33:27 raspberrypi kernel: [    0.184700] clocksource: jiffies: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 19112604462750000 ns
Jul 18 20:33:27 raspberrypi kernel: [    0.186490] pinctrl core: initialized pinctrl subsystem
Jul 18 20:33:27 raspberrypi kernel: [    0.187365] NET: Registered protocol family 16
Jul 18 20:33:27 raspberrypi kernel: [    0.193127] DMA: preallocated 4096 KiB pool for atomic coherent allocations
Jul 18 20:33:27 raspberrypi kernel: [    0.201888] hw-breakpoint: found 6 breakpoint and 1 watchpoint registers.
Jul 18 20:33:27 raspberrypi kernel: [    0.201919] hw-breakpoint: maximum watchpoint size is 4 bytes.
Jul 18 20:33:27 raspberrypi kernel: [    0.202098] Serial: AMBA PL011 UART driver
Jul 18 20:33:27 raspberrypi kernel: [    0.202606] 20201000.uart: ttyAMA0 at MMIO 0x20201000 (irq = 81, base_baud = 0) is a PL011 rev2
Jul 18 20:33:27 raspberrypi kernel: [    0.203001] console [ttyAMA0] enabled
Jul 18 20:33:27 raspberrypi kernel: [    0.203743] bcm2835-mbox 2000b880.mailbox: mailbox enabled
Jul 18 20:33:27 raspberrypi kernel: [    0.247952] bcm2835-dma 20007000.dma: DMA legacy API manager at f2007000, dmachans=0x1
Jul 18 20:33:27 raspberrypi kernel: [    0.248836] SCSI subsystem initialized
Jul 18 20:33:27 raspberrypi kernel: [    0.249185] usbcore: registered new interface driver usbfs
Jul 18 20:33:27 raspberrypi kernel: [    0.249320] usbcore: registered new interface driver hub
Jul 18 20:33:27 raspberrypi kernel: [    0.249530] usbcore: registered new device driver usb
Jul 18 20:33:27 raspberrypi kernel: [    0.252630] raspberrypi-firmware soc:firmware: Attached to firmware from 2016-11-25 16:03
Jul 18 20:33:27 raspberrypi kernel: [    0.280531] clocksource: Switched to clocksource timer
Jul 18 20:33:27 raspberrypi kernel: [    0.333309] FS-Cache: Loaded
Jul 18 20:33:27 raspberrypi kernel: [    0.333717] CacheFiles: Loaded
Jul 18 20:33:27 raspberrypi kernel: [    0.353127] NET: Registered protocol family 2
Jul 18 20:33:27 raspberrypi kernel: [    0.354467] TCP established hash table entries: 4096 (order: 2, 16384 bytes)
Jul 18 20:33:27 raspberrypi kernel: [    0.354574] TCP bind hash table entries: 4096 (order: 2, 16384 bytes)
Jul 18 20:33:27 raspberrypi kernel: [    0.354676] TCP: Hash tables configured (established 4096 bind 4096)
Jul 18 20:33:27 raspberrypi kernel: [    0.354782] UDP hash table entries: 256 (order: 0, 4096 bytes)
Jul 18 20:33:27 raspberrypi kernel: [    0.354822] UDP-Lite hash table entries: 256 (order: 0, 4096 bytes)
Jul 18 20:33:27 raspberrypi kernel: [    0.355162] NET: Registered protocol family 1
Jul 18 20:33:27 raspberrypi kernel: [    0.355770] RPC: Registered named UNIX socket transport module.
Jul 18 20:33:27 raspberrypi kernel: [    0.355799] RPC: Registered udp transport module.
Jul 18 20:33:27 raspberrypi kernel: [    0.355813] RPC: Registered tcp transport module.
Jul 18 20:33:27 raspberrypi kernel: [    0.355826] RPC: Registered tcp NFSv4.1 backchannel transport module.
Jul 18 20:33:27 raspberrypi kernel: [    0.357259] hw perfevents: enabled with armv6_1176 PMU driver, 3 counters available
Jul 18 20:33:27 raspberrypi kernel: [    0.358657] futex hash table entries: 256 (order: -1, 3072 bytes)
Jul 18 20:33:27 raspberrypi kernel: [    0.375314] VFS: Disk quotas dquot_6.6.0
Jul 18 20:33:27 raspberrypi kernel: [    0.375737] VFS: Dquot-cache hash table entries: 1024 (order 0, 4096 bytes)
Jul 18 20:33:27 raspberrypi kernel: [    0.378430] FS-Cache: Netfs 'nfs' registered for caching
Jul 18 20:33:27 raspberrypi kernel: [    0.379806] NFS: Registering the id_resolver key type
Jul 18 20:33:27 raspberrypi kernel: [    0.379929] Key type id_resolver registered
Jul 18 20:33:27 raspberrypi kernel: [    0.379947] Key type id_legacy registered
Jul 18 20:33:27 raspberrypi kernel: [    0.384392] Block layer SCSI generic (bsg) driver version 0.4 loaded (major 252)
Jul 18 20:33:27 raspberrypi kernel: [    0.384828] io scheduler noop registered
Jul 18 20:33:27 raspberrypi kernel: [    0.384870] io scheduler deadline registered (default)
Jul 18 20:33:27 raspberrypi kernel: [    0.385293] io scheduler cfq registered
Jul 18 20:33:27 raspberrypi kernel: [    0.388033] BCM2708FB: allocated DMA memory 5b800000
Jul 18 20:33:27 raspberrypi kernel: [    0.388108] BCM2708FB: allocated DMA channel 0 @ f2007000
Jul 18 20:33:27 raspberrypi kernel: [    0.411229] Console: switching to colour frame buffer device 160x45
Jul 18 20:33:27 raspberrypi kernel: [    1.345561] bcm2835-rng 20104000.rng: hwrng registered
Jul 18 20:33:27 raspberrypi kernel: [    1.345911] vc-cma: Videocore CMA driver
Jul 18 20:33:27 raspberrypi kernel: [    1.345932] vc-cma: vc_cma_base      = 0x00000000
Jul 18 20:33:27 raspberrypi kernel: [    1.345946] vc-cma: vc_cma_size      = 0x00000000 (0 MiB)
Jul 18 20:33:27 raspberrypi kernel: [    1.345965] vc-cma: vc_cma_initial   = 0x00000000 (0 MiB)
Jul 18 20:33:27 raspberrypi kernel: [    1.346423] vc-mem: phys_addr:0x00000000 mem_base=0x1ec00000 mem_size:0x20000000(512 MiB)
Jul 18 20:33:27 raspberrypi kernel: [    1.372389] brd: module loaded
Jul 18 20:33:27 raspberrypi kernel: [    1.385093] loop: module loaded
Jul 18 20:33:27 raspberrypi kernel: [    1.386293] vchiq: vchiq_init_state: slot_zero = 0xdb880000, is_master = 0
Jul 18 20:33:27 raspberrypi kernel: [    1.388886] Loading iSCSI transport class v2.0-870.
Jul 18 20:33:27 raspberrypi kernel: [    1.390241] usbcore: registered new interface driver smsc95xx
Jul 18 20:33:27 raspberrypi kernel: [    1.390364] dwc_otg: version 3.00a 10-AUG-2012 (platform bus)
Jul 18 20:33:27 raspberrypi kernel: [    1.391691] usbcore: registered new interface driver usb-storage
Jul 18 20:33:27 raspberrypi kernel: [    1.392392] mousedev: PS/2 mouse device common for all mice
Jul 18 20:33:27 raspberrypi kernel: [    1.393853] bcm2835-cpufreq: min=700000 max=700000
Jul 18 20:33:27 raspberrypi kernel: [    1.394341] sdhci: Secure Digital Host Controller Interface driver
Jul 18 20:33:27 raspberrypi kernel: [    1.394363] sdhci: Copyright(c) Pierre Ossman
Jul 18 20:33:27 raspberrypi kernel: [    1.394949] sdhost: log_buf @ db810000 (5b810000)
Jul 18 20:33:27 raspberrypi kernel: [    1.450613] mmc0: sdhost-bcm2835 loaded - DMA enabled (>1)
Jul 18 20:33:27 raspberrypi kernel: [    1.451198] sdhci-pltfm: SDHCI platform and OF driver helper
Jul 18 20:33:27 raspberrypi kernel: [    1.452073] ledtrig-cpu: registered to indicate activity on CPUs
Jul 18 20:33:27 raspberrypi kernel: [    1.452362] hidraw: raw HID events driver (C) Jiri Kosina
Jul 18 20:33:27 raspberrypi kernel: [    1.452714] usbcore: registered new interface driver usbhid
Jul 18 20:33:27 raspberrypi kernel: [    1.452738] usbhid: USB HID core driver
Jul 18 20:33:27 raspberrypi kernel: [    1.473827] Initializing XFRM netlink socket
Jul 18 20:33:27 raspberrypi kernel: [    1.473905] NET: Registered protocol family 17
Jul 18 20:33:27 raspberrypi kernel: [    1.474129] Key type dns_resolver registered
Jul 18 20:33:27 raspberrypi kernel: [    1.476372] registered taskstats version 1
Jul 18 20:33:27 raspberrypi kernel: [    1.476732] vc-sm: Videocore shared memory driver
Jul 18 20:33:27 raspberrypi kernel: [    1.476768] [vc_sm_connected_init]: start
Jul 18 20:33:27 raspberrypi kernel: [    1.477839] [vc_sm_connected_init]: end - returning 0
Jul 18 20:33:27 raspberrypi kernel: [    1.478506] of_cfs_init
Jul 18 20:33:27 raspberrypi kernel: [    1.478676] of_cfs_init: OK
Jul 18 20:33:27 raspberrypi kernel: [    1.480218] Waiting for root device /dev/mmcblk0p2...
Jul 18 20:33:27 raspberrypi kernel: [    1.560361] mmc0: host does not support reading read-only switch, assuming write-enable
Jul 18 20:33:27 raspberrypi kernel: [    1.563390] mmc0: new high speed SDHC card at address e624
Jul 18 20:33:27 raspberrypi kernel: [    1.564475] mmcblk0: mmc0:e624 SU08G 7.40 GiB
Jul 18 20:33:27 raspberrypi kernel: [    1.569663]  mmcblk0: p1 p2
Jul 18 20:33:27 raspberrypi kernel: [    1.594896] EXT4-fs (mmcblk0p2): mounted filesystem with ordered data mode. Opts: (null)
Jul 18 20:33:27 raspberrypi kernel: [    1.595011] VFS: Mounted root (ext4 filesystem) readonly on device 179:2.
Jul 18 20:33:27 raspberrypi kernel: [    1.605144] devtmpfs: mounted
Jul 18 20:33:27 raspberrypi kernel: [    1.606473] Freeing unused kernel memory: 380K (c07c1000 - c0820000)
Jul 18 20:33:27 raspberrypi kernel: [    1.916759] random: systemd: uninitialized urandom read (16 bytes read, 8 bits of entropy available)
Jul 18 20:33:27 raspberrypi kernel: [    2.070026] NET: Registered protocol family 10
Jul 18 20:33:27 raspberrypi kernel: [    2.302328] uart-pl011 20201000.uart: no DMA platform data
Jul 18 20:33:27 raspberrypi kernel: [    2.308175] random: systemd-sysv-ge: uninitialized urandom read (16 bytes read, 11 bits of entropy available)
Jul 18 20:33:27 raspberrypi kernel: [    2.516960] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 18 20:33:27 raspberrypi kernel: [    2.519033] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 18 20:33:27 raspberrypi kernel: [    2.521645] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 18 20:33:27 raspberrypi kernel: [    2.554544] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 18 20:33:27 raspberrypi kernel: [    2.556291] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 18 20:33:27 raspberrypi kernel: [    2.556751] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 18 20:33:27 raspberrypi kernel: [    2.643371] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 18 20:33:27 raspberrypi kernel: [    2.668793] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 18 20:33:27 raspberrypi kernel: [    3.860752] dwc2 20980000.usb: EPs: 8, dedicated fifos, 4080 entries in SPRAM
Jul 18 20:33:27 raspberrypi kernel: [    4.425206] dwc2 20980000.usb: DWC OTG Controller
Jul 18 20:33:27 raspberrypi kernel: [    4.425317] dwc2 20980000.usb: new USB bus registered, assigned bus number 1
Jul 18 20:33:27 raspberrypi kernel: [    4.425414] dwc2 20980000.usb: irq 33, io mem 0x00000000
Jul 18 20:33:27 raspberrypi kernel: [    4.426049] usb usb1: New USB device found, idVendor=1d6b, idProduct=0002
Jul 18 20:33:27 raspberrypi kernel: [    4.426086] usb usb1: New USB device strings: Mfr=3, Product=2, SerialNumber=1
Jul 18 20:33:27 raspberrypi kernel: [    4.426106] usb usb1: Product: DWC OTG Controller
Jul 18 20:33:27 raspberrypi kernel: [    4.426128] usb usb1: Manufacturer: Linux 4.4.34+ dwc2_hsotg
Jul 18 20:33:27 raspberrypi kernel: [    4.426144] usb usb1: SerialNumber: 20980000.usb
Jul 18 20:33:27 raspberrypi kernel: [    4.427491] hub 1-0:1.0: USB hub found
Jul 18 20:33:27 raspberrypi kernel: [    4.427613] hub 1-0:1.0: 1 port detected
Jul 18 20:33:27 raspberrypi kernel: [    4.559411] using random self ethernet address
Jul 18 20:33:27 raspberrypi kernel: [    4.559461] using random host ethernet address
Jul 18 20:33:27 raspberrypi kernel: [    4.561154] usb0: HOST MAC ce:a1:56:39:22:bf
Jul 18 20:33:27 raspberrypi kernel: [    4.561386] usb0: MAC 36:32:08:c0:52:68
Jul 18 20:33:27 raspberrypi kernel: [    4.561480] using random self ethernet address
Jul 18 20:33:27 raspberrypi kernel: [    4.561516] using random host ethernet address
Jul 18 20:33:27 raspberrypi kernel: [    4.561665] g_ether gadget: Ethernet Gadget, version: Memorial Day 2008
Jul 18 20:33:27 raspberrypi kernel: [    4.561694] g_ether gadget: g_ether ready
Jul 18 20:33:27 raspberrypi kernel: [    4.572117] dwc2 20980000.usb: bound driver g_ether
Jul 18 20:33:27 raspberrypi kernel: [    4.599773] dwc2 20980000.usb: new device is high-speed
Jul 18 20:33:27 raspberrypi kernel: [    4.638861] fuse init (API version 7.23)
Jul 18 20:33:27 raspberrypi kernel: [    4.673950] i2c /dev entries driver
Jul 18 20:33:27 raspberrypi kernel: [    4.699559] dwc2 20980000.usb: new address 1
Jul 18 20:33:27 raspberrypi kernel: [    6.177318] bcm2835-wdt 20100000.watchdog: Broadcom BCM2835 watchdog timer
Jul 18 20:33:27 raspberrypi kernel: [    6.305582] gpiomem-bcm2835 20200000.gpiomem: Initialised: Registers at 0x20200000
Jul 18 20:33:27 raspberrypi kernel: [    6.420948] bcm2708_i2c 20804000.i2c: BSC1 Controller at 0x20804000 (irq 77) (baudrate 100000)
Jul 18 20:33:27 raspberrypi kernel: [    6.578893] EXT4-fs (mmcblk0p2): re-mounted. Opts: (null)
Jul 18 20:33:27 raspberrypi kernel: [    8.445544] g_ether gadget: high-speed config #2: RNDIS
Jul 18 20:33:27 raspberrypi kernel: [   15.295673] cfg80211: World regulatory domain updated:
Jul 18 20:33:27 raspberrypi kernel: [   15.295719] cfg80211:  DFS Master region: unset
Jul 18 20:33:27 raspberrypi kernel: [   15.295735] cfg80211:   (start_freq - end_freq @ bandwidth), (max_antenna_gain, max_eirp), (dfs_cac_time)
Jul 18 20:33:27 raspberrypi kernel: [   15.295759] cfg80211:   (2402000 KHz - 2472000 KHz @ 40000 KHz), (N/A, 2000 mBm), (N/A)
Jul 18 20:33:27 raspberrypi kernel: [   15.295778] cfg80211:   (2457000 KHz - 2482000 KHz @ 40000 KHz), (N/A, 2000 mBm), (N/A)
Jul 18 20:33:27 raspberrypi kernel: [   15.295796] cfg80211:   (2474000 KHz - 2494000 KHz @ 20000 KHz), (N/A, 2000 mBm), (N/A)
Jul 18 20:33:27 raspberrypi kernel: [   15.295816] cfg80211:   (5170000 KHz - 5250000 KHz @ 80000 KHz, 160000 KHz AUTO), (N/A, 2000 mBm), (N/A)
Jul 18 20:33:27 raspberrypi kernel: [   15.295836] cfg80211:   (5250000 KHz - 5330000 KHz @ 80000 KHz, 160000 KHz AUTO), (N/A, 2000 mBm), (0 s)
Jul 18 20:33:27 raspberrypi kernel: [   15.295854] cfg80211:   (5490000 KHz - 5730000 KHz @ 160000 KHz), (N/A, 2000 mBm), (0 s)
Jul 18 20:33:27 raspberrypi kernel: [   15.295871] cfg80211:   (5735000 KHz - 5835000 KHz @ 80000 KHz), (N/A, 2000 mBm), (N/A)
Jul 18 20:33:27 raspberrypi kernel: [   15.295888] cfg80211:   (57240000 KHz - 63720000 KHz @ 2160000 KHz), (N/A, 0 mBm), (N/A)
Jul 18 20:33:28 raspberrypi kernel: [   17.909285] Adding 102396k swap on /var/swap.  Priority:-1 extents:3 across:208896k SSFS
Jul 18 20:33:30 raspberrypi kernel: [   20.240719] random: nonblocking pool is initialized
Jul 18 20:33:31 raspberrypi vncserver-x11[429]: ServerManager: Server started
Jul 18 20:33:31 raspberrypi vncserver-x11[429]: ConsoleDisplay: Cannot find a running X server on vt1
Jul 18 20:33:33 raspberrypi vncserver-x11[429]: ConsoleDisplay: Found running X server (pid=522)
Jul 18 20:33:53 raspberrypi kernel: [   42.841809] Bluetooth: Core ver 2.21
Jul 18 20:33:53 raspberrypi kernel: [   42.842017] NET: Registered protocol family 31
Jul 18 20:33:53 raspberrypi kernel: [   42.842038] Bluetooth: HCI device and connection manager initialized
Jul 18 20:33:53 raspberrypi kernel: [   42.842075] Bluetooth: HCI socket layer initialized
Jul 18 20:33:53 raspberrypi kernel: [   42.842105] Bluetooth: L2CAP socket layer initialized
Jul 18 20:33:53 raspberrypi kernel: [   42.842165] Bluetooth: SCO socket layer initialized
Jul 18 20:33:53 raspberrypi kernel: [   42.982035] Bluetooth: BNEP (Ethernet Emulation) ver 1.3
Jul 18 20:33:53 raspberrypi kernel: [   42.982079] Bluetooth: BNEP filters: protocol multicast
Jul 18 20:33:53 raspberrypi kernel: [   42.982124] Bluetooth: BNEP socket layer initialized
Jul 18 20:33:59 raspberrypi org.gtk.Private.AfcVolumeMonitor[675]: Volume monitor alive
Jul 19 08:48:46 raspberrypi kernel: [ 6633.783619] dwc2 20980000.usb: new device is high-speed
Jul 19 08:48:47 raspberrypi kernel: [ 6633.883819] dwc2 20980000.usb: new address 1
Jul 19 08:48:47 raspberrypi kernel: [ 6634.035998] g_ether gadget: high-speed config #2: RNDIS
Jul 19 08:54:19 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 08:54:49 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 09:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 09:17:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 10:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 10:17:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 11:03:00 raspberrypi vncserver-x11[429]: Connections: connected: [fe80::e18f:c38f:61cc:1f1f%usb0]::61489
Jul 19 11:03:00 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 11:03:30 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 11:03:01 raspberrypi vncserver-x11[429]: Connections: authenticated: [fe80::e18f:c38f:61cc:1f1f%usb0]::61489, as pi (f permissions)
Jul 19 11:03:07 raspberrypi kernel: [14694.422858] warning: process `colord-sane' used the deprecated sysctl system call with 8.1.2.
Jul 19 11:07:13 raspberrypi kernel: [14940.184623] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 19 11:07:13 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 11:07:43 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 11:09:09 raspberrypi kernel: [15055.961779] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 19 11:09:09 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 11:09:39 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 11:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 11:17:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 11:23:34 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 11:24:04 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 11:11:25 raspberrypi kernel: [16058.447504] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 19 11:25:25 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 11:25:55 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 12:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 12:17:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 12:52:22 raspberrypi vncserver-x11[429]: Connections: disconnected: [fe80::e18f:c38f:61cc:1f1f%usb0]::61489 ([IdleTimeout] This connection has timed out through inactivity.)
Jul 19 12:52:22 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 12:53:22 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 13:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 13:18:01 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 13:55:24 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 13:56:24 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 14:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 14:18:01 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 15:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 15:18:01 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 16:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 16:18:01 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 17:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 17:18:01 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 18:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 18:18:01 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 19:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 19:18:01 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 20:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 20:18:01 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 21:17:02 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 21:18:32 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 22:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 22:18:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 22:31:27 raspberrypi vncserver-x11[429]: Connections: connected: [fe80::e18f:c38f:61cc:1f1f%usb0]::53136
Jul 19 22:31:27 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Wed Jul 19 22:32:57 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 19 22:31:28 raspberrypi vncserver-x11[429]: Connections: authenticated: [fe80::e18f:c38f:61cc:1f1f%usb0]::53136, as pi (f permissions)
Jul 19 22:32:14 raspberrypi org.gtk.vfs.Daemon[675]: A connection to the bus can't be made
Jul 19 22:32:15 raspberrypi rsyslogd: [origin software="rsyslogd" swVersion="8.4.2" x-pid="375" x-info="http://www.rsyslog.com"] exiting on signal 15.
Jul 19 22:32:32 raspberrypi rsyslogd: [origin software="rsyslogd" swVersion="8.4.2" x-pid="384" x-info="http://www.rsyslog.com"] start
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Booting Linux on physical CPU 0x0
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Initializing cgroup subsys cpuset
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Initializing cgroup subsys cpu
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Initializing cgroup subsys cpuacct
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Linux version 4.4.34+ (dc4@dc4-XPS13-9333) (gcc version 4.9.3 (crosstool-NG crosstool-ng-1.22.0-88-g8460611) ) #930 Wed Nov 23 15:12:30 GMT 2016
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] CPU: ARMv6-compatible processor [410fb767] revision 7 (ARMv7), cr=00c5387d
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] CPU: PIPT / VIPT nonaliasing data cache, VIPT nonaliasing instruction cache
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Machine model: Raspberry Pi ? Rev 1.1
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] cma: Reserved 8 MiB at 0x1b400000
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Memory policy: Data cache writeback
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Built 1 zonelists in Zone order, mobility grouping on.  Total pages: 113680
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Kernel command line: dma.dmachans=0x7f35 bcm2708_fb.fbwidth=1280 bcm2708_fb.fbheight=720 bcm2708.boardrev=0x9000c1 bcm2708.serial=0x14efb6d8 smsc95xx.macaddr=B8:27:EB:EF:B6:D8 bcm2708_fb.fbswap=1 bcm2708.uart_clock=48000000 bcm2708.disk_led_gpio=47 vc_mem.mem_base=0x1ec00000 vc_mem.mem_size=0x20000000  dwc_otg.lpm_enable=0 console=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait modules-load=dwc2,g_ether quiet splash plymouth.ignore-serial-consoles
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] PID hash table entries: 2048 (order: 1, 8192 bytes)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Dentry cache hash table entries: 65536 (order: 6, 262144 bytes)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Inode-cache hash table entries: 32768 (order: 5, 131072 bytes)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Memory: 436516K/458752K available (6059K kernel code, 437K rwdata, 1844K rodata, 380K init, 726K bss, 14044K reserved, 8192K cma-reserved)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] Virtual kernel memory layout:
Jul 19 22:32:32 raspberrypi kernel: [    0.000000]     vector  : 0xffff0000 - 0xffff1000   (   4 kB)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000]     fixmap  : 0xffc00000 - 0xfff00000   (3072 kB)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000]     vmalloc : 0xdc800000 - 0xff800000   ( 560 MB)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000]     lowmem  : 0xc0000000 - 0xdc000000   ( 448 MB)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000]     modules : 0xbf000000 - 0xc0000000   (  16 MB)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000]       .text : 0xc0008000 - 0xc07c0008   (7905 kB)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000]       .init : 0xc07c1000 - 0xc0820000   ( 380 kB)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000]       .data : 0xc0820000 - 0xc088d490   ( 438 kB)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000]        .bss : 0xc088d490 - 0xc0943050   ( 727 kB)
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] SLUB: HWalign=32, Order=0-3, MinObjects=0, CPUs=1, Nodes=1
Jul 19 22:32:32 raspberrypi kernel: [    0.000000] NR_IRQS:16 nr_irqs:16 16
Jul 19 22:32:32 raspberrypi kernel: [    0.000028] sched_clock: 32 bits at 1000kHz, resolution 1000ns, wraps every 2147483647500ns
Jul 19 22:32:32 raspberrypi kernel: [    0.000073] clocksource: timer: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 1911260446275 ns
Jul 19 22:32:32 raspberrypi kernel: [    0.000175] bcm2835: system timer (irq = 27)
Jul 19 22:32:32 raspberrypi kernel: [    0.000487] Console: colour dummy device 80x30
Jul 19 22:32:32 raspberrypi kernel: [    0.000727] console [tty1] enabled
Jul 19 22:32:32 raspberrypi kernel: [    0.000758] Calibrating delay loop... 697.95 BogoMIPS (lpj=3489792)
Jul 19 22:32:32 raspberrypi kernel: [    0.060314] pid_max: default: 32768 minimum: 301
Jul 19 22:32:32 raspberrypi kernel: [    0.060688] Mount-cache hash table entries: 1024 (order: 0, 4096 bytes)
Jul 19 22:32:32 raspberrypi kernel: [    0.060717] Mountpoint-cache hash table entries: 1024 (order: 0, 4096 bytes)
Jul 19 22:32:32 raspberrypi kernel: [    0.061708] Disabling cpuset control group subsystem
Jul 19 22:32:32 raspberrypi kernel: [    0.061760] Initializing cgroup subsys io
Jul 19 22:32:32 raspberrypi kernel: [    0.061798] Initializing cgroup subsys memory
Jul 19 22:32:32 raspberrypi kernel: [    0.061860] Initializing cgroup subsys devices
Jul 19 22:32:32 raspberrypi kernel: [    0.061893] Initializing cgroup subsys freezer
Jul 19 22:32:32 raspberrypi kernel: [    0.061925] Initializing cgroup subsys net_cls
Jul 19 22:32:32 raspberrypi kernel: [    0.062009] CPU: Testing write buffer coherency: ok
Jul 19 22:32:32 raspberrypi kernel: [    0.062087] ftrace: allocating 20645 entries in 61 pages
Jul 19 22:32:32 raspberrypi kernel: [    0.172684] Setting up static identity map for 0x81c0 - 0x81f8
Jul 19 22:32:32 raspberrypi kernel: [    0.174546] devtmpfs: initialized
Jul 19 22:32:32 raspberrypi kernel: [    0.184146] VFP support v0.3: implementor 41 architecture 1 part 20 variant b rev 5
Jul 19 22:32:32 raspberrypi kernel: [    0.184668] clocksource: jiffies: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 19112604462750000 ns
Jul 19 22:32:32 raspberrypi kernel: [    0.186456] pinctrl core: initialized pinctrl subsystem
Jul 19 22:32:32 raspberrypi kernel: [    0.187333] NET: Registered protocol family 16
Jul 19 22:32:32 raspberrypi kernel: [    0.193093] DMA: preallocated 4096 KiB pool for atomic coherent allocations
Jul 19 22:32:32 raspberrypi kernel: [    0.201857] hw-breakpoint: found 6 breakpoint and 1 watchpoint registers.
Jul 19 22:32:32 raspberrypi kernel: [    0.201887] hw-breakpoint: maximum watchpoint size is 4 bytes.
Jul 19 22:32:32 raspberrypi kernel: [    0.202068] Serial: AMBA PL011 UART driver
Jul 19 22:32:32 raspberrypi kernel: [    0.202578] 20201000.uart: ttyAMA0 at MMIO 0x20201000 (irq = 81, base_baud = 0) is a PL011 rev2
Jul 19 22:32:32 raspberrypi kernel: [    0.202970] console [ttyAMA0] enabled
Jul 19 22:32:32 raspberrypi kernel: [    0.203713] bcm2835-mbox 2000b880.mailbox: mailbox enabled
Jul 19 22:32:32 raspberrypi kernel: [    0.247918] bcm2835-dma 20007000.dma: DMA legacy API manager at f2007000, dmachans=0x1
Jul 19 22:32:32 raspberrypi kernel: [    0.248802] SCSI subsystem initialized
Jul 19 22:32:32 raspberrypi kernel: [    0.249152] usbcore: registered new interface driver usbfs
Jul 19 22:32:32 raspberrypi kernel: [    0.249287] usbcore: registered new interface driver hub
Jul 19 22:32:32 raspberrypi kernel: [    0.249500] usbcore: registered new device driver usb
Jul 19 22:32:32 raspberrypi kernel: [    0.252599] raspberrypi-firmware soc:firmware: Attached to firmware from 2016-11-25 16:03
Jul 19 22:32:32 raspberrypi kernel: [    0.280504] clocksource: Switched to clocksource timer
Jul 19 22:32:32 raspberrypi kernel: [    0.333250] FS-Cache: Loaded
Jul 19 22:32:32 raspberrypi kernel: [    0.333657] CacheFiles: Loaded
Jul 19 22:32:32 raspberrypi kernel: [    0.353054] NET: Registered protocol family 2
Jul 19 22:32:32 raspberrypi kernel: [    0.354394] TCP established hash table entries: 4096 (order: 2, 16384 bytes)
Jul 19 22:32:32 raspberrypi kernel: [    0.354498] TCP bind hash table entries: 4096 (order: 2, 16384 bytes)
Jul 19 22:32:32 raspberrypi kernel: [    0.354601] TCP: Hash tables configured (established 4096 bind 4096)
Jul 19 22:32:32 raspberrypi kernel: [    0.354706] UDP hash table entries: 256 (order: 0, 4096 bytes)
Jul 19 22:32:32 raspberrypi kernel: [    0.354746] UDP-Lite hash table entries: 256 (order: 0, 4096 bytes)
Jul 19 22:32:32 raspberrypi kernel: [    0.355090] NET: Registered protocol family 1
Jul 19 22:32:32 raspberrypi kernel: [    0.355701] RPC: Registered named UNIX socket transport module.
Jul 19 22:32:32 raspberrypi kernel: [    0.355729] RPC: Registered udp transport module.
Jul 19 22:32:32 raspberrypi kernel: [    0.355741] RPC: Registered tcp transport module.
Jul 19 22:32:32 raspberrypi kernel: [    0.355754] RPC: Registered tcp NFSv4.1 backchannel transport module.
Jul 19 22:32:32 raspberrypi kernel: [    0.357184] hw perfevents: enabled with armv6_1176 PMU driver, 3 counters available
Jul 19 22:32:32 raspberrypi kernel: [    0.358586] futex hash table entries: 256 (order: -1, 3072 bytes)
Jul 19 22:32:32 raspberrypi kernel: [    0.375245] VFS: Disk quotas dquot_6.6.0
Jul 19 22:32:32 raspberrypi kernel: [    0.375667] VFS: Dquot-cache hash table entries: 1024 (order 0, 4096 bytes)
Jul 19 22:32:32 raspberrypi kernel: [    0.378362] FS-Cache: Netfs 'nfs' registered for caching
Jul 19 22:32:32 raspberrypi kernel: [    0.379742] NFS: Registering the id_resolver key type
Jul 19 22:32:32 raspberrypi kernel: [    0.379866] Key type id_resolver registered
Jul 19 22:32:32 raspberrypi kernel: [    0.379886] Key type id_legacy registered
Jul 19 22:32:32 raspberrypi kernel: [    0.384341] Block layer SCSI generic (bsg) driver version 0.4 loaded (major 252)
Jul 19 22:32:32 raspberrypi kernel: [    0.384781] io scheduler noop registered
Jul 19 22:32:32 raspberrypi kernel: [    0.384824] io scheduler deadline registered (default)
Jul 19 22:32:32 raspberrypi kernel: [    0.385247] io scheduler cfq registered
Jul 19 22:32:32 raspberrypi kernel: [    0.387990] BCM2708FB: allocated DMA memory 5b800000
Jul 19 22:32:32 raspberrypi kernel: [    0.388064] BCM2708FB: allocated DMA channel 0 @ f2007000
Jul 19 22:32:32 raspberrypi kernel: [    0.411193] Console: switching to colour frame buffer device 160x45
Jul 19 22:32:32 raspberrypi kernel: [    1.347485] bcm2835-rng 20104000.rng: hwrng registered
Jul 19 22:32:32 raspberrypi kernel: [    1.347799] vc-cma: Videocore CMA driver
Jul 19 22:32:32 raspberrypi kernel: [    1.347822] vc-cma: vc_cma_base      = 0x00000000
Jul 19 22:32:32 raspberrypi kernel: [    1.347835] vc-cma: vc_cma_size      = 0x00000000 (0 MiB)
Jul 19 22:32:32 raspberrypi kernel: [    1.347847] vc-cma: vc_cma_initial   = 0x00000000 (0 MiB)
Jul 19 22:32:32 raspberrypi kernel: [    1.348273] vc-mem: phys_addr:0x00000000 mem_base=0x1ec00000 mem_size:0x20000000(512 MiB)
Jul 19 22:32:32 raspberrypi kernel: [    1.374337] brd: module loaded
Jul 19 22:32:32 raspberrypi kernel: [    1.386957] loop: module loaded
Jul 19 22:32:32 raspberrypi kernel: [    1.388223] vchiq: vchiq_init_state: slot_zero = 0xdb880000, is_master = 0
Jul 19 22:32:32 raspberrypi kernel: [    1.390977] Loading iSCSI transport class v2.0-870.
Jul 19 22:32:32 raspberrypi kernel: [    1.392308] usbcore: registered new interface driver smsc95xx
Jul 19 22:32:32 raspberrypi kernel: [    1.392428] dwc_otg: version 3.00a 10-AUG-2012 (platform bus)
Jul 19 22:32:32 raspberrypi kernel: [    1.393481] usbcore: registered new interface driver usb-storage
Jul 19 22:32:32 raspberrypi kernel: [    1.394188] mousedev: PS/2 mouse device common for all mice
Jul 19 22:32:32 raspberrypi kernel: [    1.395662] bcm2835-cpufreq: min=700000 max=700000
Jul 19 22:32:32 raspberrypi kernel: [    1.396145] sdhci: Secure Digital Host Controller Interface driver
Jul 19 22:32:32 raspberrypi kernel: [    1.396168] sdhci: Copyright(c) Pierre Ossman
Jul 19 22:32:32 raspberrypi kernel: [    1.396762] sdhost: log_buf @ db810000 (5b810000)
Jul 19 22:32:32 raspberrypi kernel: [    1.450586] mmc0: sdhost-bcm2835 loaded - DMA enabled (>1)
Jul 19 22:32:32 raspberrypi kernel: [    1.451168] sdhci-pltfm: SDHCI platform and OF driver helper
Jul 19 22:32:32 raspberrypi kernel: [    1.452042] ledtrig-cpu: registered to indicate activity on CPUs
Jul 19 22:32:32 raspberrypi kernel: [    1.452333] hidraw: raw HID events driver (C) Jiri Kosina
Jul 19 22:32:32 raspberrypi kernel: [    1.452680] usbcore: registered new interface driver usbhid
Jul 19 22:32:32 raspberrypi kernel: [    1.452705] usbhid: USB HID core driver
Jul 19 22:32:32 raspberrypi kernel: [    1.473788] Initializing XFRM netlink socket
Jul 19 22:32:32 raspberrypi kernel: [    1.473866] NET: Registered protocol family 17
Jul 19 22:32:32 raspberrypi kernel: [    1.474116] Key type dns_resolver registered
Jul 19 22:32:32 raspberrypi kernel: [    1.476373] registered taskstats version 1
Jul 19 22:32:32 raspberrypi kernel: [    1.476726] vc-sm: Videocore shared memory driver
Jul 19 22:32:32 raspberrypi kernel: [    1.476757] [vc_sm_connected_init]: start
Jul 19 22:32:32 raspberrypi kernel: [    1.477829] [vc_sm_connected_init]: end - returning 0
Jul 19 22:32:32 raspberrypi kernel: [    1.478502] of_cfs_init
Jul 19 22:32:32 raspberrypi kernel: [    1.478666] of_cfs_init: OK
Jul 19 22:32:32 raspberrypi kernel: [    1.480221] Waiting for root device /dev/mmcblk0p2...
Jul 19 22:32:32 raspberrypi kernel: [    1.560333] mmc0: host does not support reading read-only switch, assuming write-enable
Jul 19 22:32:32 raspberrypi kernel: [    1.563361] mmc0: new high speed SDHC card at address e624
Jul 19 22:32:32 raspberrypi kernel: [    1.564446] mmcblk0: mmc0:e624 SU08G 7.40 GiB
Jul 19 22:32:32 raspberrypi kernel: [    1.569622]  mmcblk0: p1 p2
Jul 19 22:32:32 raspberrypi kernel: [    1.595067] EXT4-fs (mmcblk0p2): mounted filesystem with ordered data mode. Opts: (null)
Jul 19 22:32:32 raspberrypi kernel: [    1.595172] VFS: Mounted root (ext4 filesystem) readonly on device 179:2.
Jul 19 22:32:32 raspberrypi kernel: [    1.605786] devtmpfs: mounted
Jul 19 22:32:32 raspberrypi kernel: [    1.607113] Freeing unused kernel memory: 380K (c07c1000 - c0820000)
Jul 19 22:32:32 raspberrypi kernel: [    1.918445] random: systemd: uninitialized urandom read (16 bytes read, 8 bits of entropy available)
Jul 19 22:32:32 raspberrypi kernel: [    2.071905] NET: Registered protocol family 10
Jul 19 22:32:32 raspberrypi kernel: [    2.297152] random: systemd-sysv-ge: uninitialized urandom read (16 bytes read, 10 bits of entropy available)
Jul 19 22:32:32 raspberrypi kernel: [    2.301550] uart-pl011 20201000.uart: no DMA platform data
Jul 19 22:32:32 raspberrypi kernel: [    2.506731] random: systemd: uninitialized urandom read (16 bytes read, 12 bits of entropy available)
Jul 19 22:32:32 raspberrypi kernel: [    2.508956] random: systemd: uninitialized urandom read (16 bytes read, 12 bits of entropy available)
Jul 19 22:32:32 raspberrypi kernel: [    2.511672] random: systemd: uninitialized urandom read (16 bytes read, 12 bits of entropy available)
Jul 19 22:32:32 raspberrypi kernel: [    2.544771] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 19 22:32:32 raspberrypi kernel: [    2.546514] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 19 22:32:32 raspberrypi kernel: [    2.546965] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 19 22:32:32 raspberrypi kernel: [    2.633198] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 19 22:32:32 raspberrypi kernel: [    2.658481] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 19 22:32:32 raspberrypi kernel: [    3.840726] dwc2 20980000.usb: EPs: 8, dedicated fifos, 4080 entries in SPRAM
Jul 19 22:32:32 raspberrypi kernel: [    4.411050] dwc2 20980000.usb: DWC OTG Controller
Jul 19 22:32:32 raspberrypi kernel: [    4.411161] dwc2 20980000.usb: new USB bus registered, assigned bus number 1
Jul 19 22:32:32 raspberrypi kernel: [    4.411259] dwc2 20980000.usb: irq 33, io mem 0x00000000
Jul 19 22:32:32 raspberrypi kernel: [    4.411919] usb usb1: New USB device found, idVendor=1d6b, idProduct=0002
Jul 19 22:32:32 raspberrypi kernel: [    4.411949] usb usb1: New USB device strings: Mfr=3, Product=2, SerialNumber=1
Jul 19 22:32:32 raspberrypi kernel: [    4.411969] usb usb1: Product: DWC OTG Controller
Jul 19 22:32:32 raspberrypi kernel: [    4.411992] usb usb1: Manufacturer: Linux 4.4.34+ dwc2_hsotg
Jul 19 22:32:32 raspberrypi kernel: [    4.412009] usb usb1: SerialNumber: 20980000.usb
Jul 19 22:32:32 raspberrypi kernel: [    4.413375] hub 1-0:1.0: USB hub found
Jul 19 22:32:32 raspberrypi kernel: [    4.413494] hub 1-0:1.0: 1 port detected
Jul 19 22:32:32 raspberrypi kernel: [    4.536055] using random self ethernet address
Jul 19 22:32:32 raspberrypi kernel: [    4.536102] using random host ethernet address
Jul 19 22:32:32 raspberrypi kernel: [    4.537640] usb0: HOST MAC 0a:31:9e:ec:19:02
Jul 19 22:32:32 raspberrypi kernel: [    4.537840] usb0: MAC 5e:0a:a3:e4:5f:c8
Jul 19 22:32:32 raspberrypi kernel: [    4.537928] using random self ethernet address
Jul 19 22:32:32 raspberrypi kernel: [    4.537960] using random host ethernet address
Jul 19 22:32:32 raspberrypi kernel: [    4.538102] g_ether gadget: Ethernet Gadget, version: Memorial Day 2008
Jul 19 22:32:32 raspberrypi kernel: [    4.538126] g_ether gadget: g_ether ready
Jul 19 22:32:32 raspberrypi kernel: [    4.548544] dwc2 20980000.usb: bound driver g_ether
Jul 19 22:32:32 raspberrypi kernel: [    4.574178] dwc2 20980000.usb: new device is high-speed
Jul 19 22:32:32 raspberrypi kernel: [    4.617212] fuse init (API version 7.23)
Jul 19 22:32:32 raspberrypi kernel: [    4.652000] i2c /dev entries driver
Jul 19 22:32:32 raspberrypi kernel: [    4.673923] dwc2 20980000.usb: new address 1
Jul 19 22:32:32 raspberrypi kernel: [    6.134848] bcm2835-wdt 20100000.watchdog: Broadcom BCM2835 watchdog timer
Jul 19 22:32:32 raspberrypi kernel: [    6.183106] gpiomem-bcm2835 20200000.gpiomem: Initialised: Registers at 0x20200000
Jul 19 22:32:32 raspberrypi kernel: [    6.502790] EXT4-fs (mmcblk0p2): re-mounted. Opts: (null)
Jul 19 22:32:32 raspberrypi kernel: [    6.613563] bcm2708_i2c 20804000.i2c: BSC1 Controller at 0x20804000 (irq 77) (baudrate 100000)
Jul 19 22:32:32 raspberrypi kernel: [    8.166683] g_ether gadget: high-speed config #2: RNDIS
Jul 19 22:32:32 raspberrypi kernel: [   15.278548] cfg80211: World regulatory domain updated:
Jul 19 22:32:32 raspberrypi kernel: [   15.278592] cfg80211:  DFS Master region: unset
Jul 19 22:32:32 raspberrypi kernel: [   15.278607] cfg80211:   (start_freq - end_freq @ bandwidth), (max_antenna_gain, max_eirp), (dfs_cac_time)
Jul 19 22:32:32 raspberrypi kernel: [   15.278630] cfg80211:   (2402000 KHz - 2472000 KHz @ 40000 KHz), (N/A, 2000 mBm), (N/A)
Jul 19 22:32:32 raspberrypi kernel: [   15.278648] cfg80211:   (2457000 KHz - 2482000 KHz @ 40000 KHz), (N/A, 2000 mBm), (N/A)
Jul 19 22:32:32 raspberrypi kernel: [   15.278665] cfg80211:   (2474000 KHz - 2494000 KHz @ 20000 KHz), (N/A, 2000 mBm), (N/A)
Jul 19 22:32:32 raspberrypi kernel: [   15.278686] cfg80211:   (5170000 KHz - 5250000 KHz @ 80000 KHz, 160000 KHz AUTO), (N/A, 2000 mBm), (N/A)
Jul 19 22:32:32 raspberrypi kernel: [   15.278705] cfg80211:   (5250000 KHz - 5330000 KHz @ 80000 KHz, 160000 KHz AUTO), (N/A, 2000 mBm), (0 s)
Jul 19 22:32:32 raspberrypi kernel: [   15.278722] cfg80211:   (5490000 KHz - 5730000 KHz @ 160000 KHz), (N/A, 2000 mBm), (0 s)
Jul 19 22:32:32 raspberrypi kernel: [   15.278739] cfg80211:   (5735000 KHz - 5835000 KHz @ 80000 KHz), (N/A, 2000 mBm), (N/A)
Jul 19 22:32:32 raspberrypi kernel: [   15.278756] cfg80211:   (57240000 KHz - 63720000 KHz @ 2160000 KHz), (N/A, 0 mBm), (N/A)
Jul 19 22:32:32 raspberrypi kernel: [   16.985148] Adding 102396k swap on /var/swap.  Priority:-1 extents:3 across:208896k SSFS
Jul 19 22:32:33 raspberrypi kernel: [   17.567968] random: nonblocking pool is initialized
Jul 19 22:32:34 raspberrypi vncserver-x11[431]: ServerManager: Server started
Jul 19 22:32:36 raspberrypi vncserver-x11[431]: ConsoleDisplay: Cannot find a running X server on vt1
Jul 19 22:32:37 raspberrypi kernel: [   21.343677] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 19 22:32:39 raspberrypi vncserver-x11[431]: ConsoleDisplay: Found running X server (pid=523)
Jul 19 22:32:59 raspberrypi kernel: [   43.279452] Bluetooth: Core ver 2.21
Jul 19 22:32:59 raspberrypi kernel: [   43.279678] NET: Registered protocol family 31
Jul 19 22:32:59 raspberrypi kernel: [   43.279700] Bluetooth: HCI device and connection manager initialized
Jul 19 22:32:59 raspberrypi kernel: [   43.279742] Bluetooth: HCI socket layer initialized
Jul 19 22:32:59 raspberrypi kernel: [   43.279771] Bluetooth: L2CAP socket layer initialized
Jul 19 22:32:59 raspberrypi kernel: [   43.279837] Bluetooth: SCO socket layer initialized
Jul 19 22:32:59 raspberrypi kernel: [   43.395819] Bluetooth: BNEP (Ethernet Emulation) ver 1.3
Jul 19 22:32:59 raspberrypi kernel: [   43.395861] Bluetooth: BNEP filters: protocol multicast
Jul 19 22:32:59 raspberrypi kernel: [   43.395905] Bluetooth: BNEP socket layer initialized
Jul 19 22:33:07 raspberrypi org.gtk.Private.AfcVolumeMonitor[676]: Volume monitor alive
Jul 19 23:13:58 raspberrypi vncserver-x11[431]: Connections: connected: [fe80::fcbc:db16:eccd:1b8%usb0]::55158
Jul 19 23:13:59 raspberrypi vncserver-x11[431]: Connections: authenticated: [fe80::fcbc:db16:eccd:1b8%usb0]::55158, as pi (f permissions)
Jul 19 23:14:05 raspberrypi kernel: [ 2509.991727] warning: process `colord-sane' used the deprecated sysctl system call with 8.1.2.
Jul 19 23:16:31 raspberrypi kernel: [ 2655.984405] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 19 23:16:41 raspberrypi kernel: [ 2665.947610] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 07:51:08 raspberrypi kernel: [ 2711.633324] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 09:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 09:17:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 09:39:04 raspberrypi kernel: [ 9226.540548] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 09:39:04 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 09:39:34 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 09:53:25 raspberrypi kernel: [10086.636740] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 09:53:25 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 09:53:55 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 10:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 10:17:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 10:23:05 raspberrypi kernel: [11867.188625] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 10:23:05 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 10:23:35 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 10:28:49 raspberrypi kernel: [12211.216196] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 10:28:49 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 10:29:19 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 11:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 11:17:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 11:31:46 raspberrypi kernel: [15988.383089] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 11:31:46 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 11:32:16 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 11:34:39 raspberrypi kernel: [16160.644948] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 11:34:39 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 11:35:09 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 11:57:35 raspberrypi kernel: [17537.358263] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 11:57:35 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 11:58:05 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 11:57:56 raspberrypi kernel: [17557.869353] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 12:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 12:18:01 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 12:37:55 raspberrypi kernel: [19957.624215] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 12:37:55 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 12:38:55 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 13:06:03 raspberrypi kernel: [21644.788414] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 13:06:03 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 13:07:03 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 13:15:48 raspberrypi kernel: [22230.615897] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 13:15:48 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 13:16:48 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 13:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 13:18:01 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 14:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 14:18:01 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 14:22:54 raspberrypi kernel: [26256.653372] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 14:22:54 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 14:23:54 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 14:50:37 raspberrypi vncserver-x11[431]: Connections: disconnected: [fe80::fcbc:db16:eccd:1b8%usb0]::55158 ([System] read: Connection timed out (110))
Jul 20 14:50:37 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 14:51:37 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 15:09:23 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 15:10:23 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 15:09:23 raspberrypi kernel: [29045.502886] dwc2 20980000.usb: new device is high-speed
Jul 20 15:09:23 raspberrypi kernel: [29045.602687] dwc2 20980000.usb: new address 1
Jul 20 15:09:24 raspberrypi kernel: [29045.709247] g_ether gadget: high-speed config #2: RNDIS
Jul 20 15:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 15:18:01 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 15:34:32 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 15:36:02 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 15:34:32 raspberrypi kernel: [30553.924881] dwc2 20980000.usb: new device is high-speed
Jul 20 15:34:32 raspberrypi kernel: [30554.025063] dwc2 20980000.usb: new address 1
Jul 20 15:34:32 raspberrypi kernel: [30554.053508] g_ether gadget: high-speed config #2: RNDIS
Jul 20 15:37:49 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 15:39:19 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 15:38:08 raspberrypi kernel: [30769.752709] dwc2 20980000.usb: new device is high-speed
Jul 20 15:38:08 raspberrypi kernel: [30769.852937] dwc2 20980000.usb: new address 2
Jul 20 15:38:08 raspberrypi kernel: [30769.866718] g_ether gadget: high-speed config #2: RNDIS
Jul 20 15:38:08 raspberrypi kernel: [30769.930193] dwc2 20980000.usb: new device is high-speed
Jul 20 15:38:08 raspberrypi kernel: [30770.029926] dwc2 20980000.usb: new address 1
Jul 20 15:38:08 raspberrypi kernel: [30770.043684] g_ether gadget: high-speed config #2: RNDIS
Jul 20 15:38:08 raspberrypi kernel: [30770.063966] g_ether gadget: high-speed config #2: RNDIS
Jul 20 15:38:42 raspberrypi vncserver-x11[431]: Connections: connected: [fe80::fcbc:db16:eccd:1b8%usb0]::54703
Jul 20 15:38:43 raspberrypi vncserver-x11[431]: Connections: authenticated: [fe80::fcbc:db16:eccd:1b8%usb0]::54703, as pi (f permissions)
Jul 20 15:43:25 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 15:44:55 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 15:57:17 raspberrypi kernel: [31918.944839] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 15:57:17 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 15:58:47 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 16:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 16:18:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 16:18:41 raspberrypi kernel: [33203.002069] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 16:18:41 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 16:20:11 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 17:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 17:18:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 18:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 18:18:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 19:10:01 raspberrypi vncserver-x11[431]: Connections: disconnected: [fe80::fcbc:db16:eccd:1b8%usb0]::54703 ([IdleTimeout] This connection has timed out through inactivity.)
Jul 20 19:10:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 19:11:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 19:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 19:18:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 19:45:39 raspberrypi vncserver-x11[431]: Connections: connected: [fe80::fcbc:db16:eccd:1b8%usb0]::60500
Jul 20 19:45:39 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 19:47:09 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 19:45:40 raspberrypi vncserver-x11[431]: Connections: authenticated: [fe80::fcbc:db16:eccd:1b8%usb0]::60500, as pi (f permissions)
Jul 20 19:55:22 raspberrypi kernel: [46204.252104] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 19:55:22 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 19:56:52 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 20:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 20:18:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 21:03:26 raspberrypi vncserver-x11[431]: Connections: disconnected: [fe80::fcbc:db16:eccd:1b8%usb0]::60500 ([IdleTimeout] This connection has timed out through inactivity.)
Jul 20 21:03:26 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 21:04:56 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 21:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 21:18:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 22:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 22:18:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 22:17:55 raspberrypi vncserver-x11[431]: Connections: connected: [fe80::fcbc:db16:eccd:1b8%usb0]::49638
Jul 20 22:17:56 raspberrypi vncserver-x11[431]: Connections: authenticated: [fe80::fcbc:db16:eccd:1b8%usb0]::49638, as pi (f permissions)
Jul 20 22:48:10 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 22:49:40 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 22:48:10 raspberrypi org.gtk.vfs.Daemon[676]: A connection to the bus can't be made
Jul 20 22:48:11 raspberrypi rsyslogd: [origin software="rsyslogd" swVersion="8.4.2" x-pid="384" x-info="http://www.rsyslog.com"] exiting on signal 15.
Jul 20 22:48:27 raspberrypi rsyslogd: [origin software="rsyslogd" swVersion="8.4.2" x-pid="382" x-info="http://www.rsyslog.com"] start
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Booting Linux on physical CPU 0x0
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Initializing cgroup subsys cpuset
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Initializing cgroup subsys cpu
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Initializing cgroup subsys cpuacct
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Linux version 4.4.34+ (dc4@dc4-XPS13-9333) (gcc version 4.9.3 (crosstool-NG crosstool-ng-1.22.0-88-g8460611) ) #930 Wed Nov 23 15:12:30 GMT 2016
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] CPU: ARMv6-compatible processor [410fb767] revision 7 (ARMv7), cr=00c5387d
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] CPU: PIPT / VIPT nonaliasing data cache, VIPT nonaliasing instruction cache
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Machine model: Raspberry Pi ? Rev 1.1
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] cma: Reserved 8 MiB at 0x1b400000
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Memory policy: Data cache writeback
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Built 1 zonelists in Zone order, mobility grouping on.  Total pages: 113680
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Kernel command line: dma.dmachans=0x7f35 bcm2708_fb.fbwidth=1280 bcm2708_fb.fbheight=720 bcm2708.boardrev=0x9000c1 bcm2708.serial=0x14efb6d8 smsc95xx.macaddr=B8:27:EB:EF:B6:D8 bcm2708_fb.fbswap=1 bcm2708.uart_clock=48000000 bcm2708.disk_led_gpio=47 vc_mem.mem_base=0x1ec00000 vc_mem.mem_size=0x20000000  dwc_otg.lpm_enable=0 console=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait modules-load=dwc2,g_ether quiet splash plymouth.ignore-serial-consoles
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] PID hash table entries: 2048 (order: 1, 8192 bytes)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Dentry cache hash table entries: 65536 (order: 6, 262144 bytes)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Inode-cache hash table entries: 32768 (order: 5, 131072 bytes)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Memory: 436516K/458752K available (6059K kernel code, 437K rwdata, 1844K rodata, 380K init, 726K bss, 14044K reserved, 8192K cma-reserved)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] Virtual kernel memory layout:
Jul 20 22:48:27 raspberrypi kernel: [    0.000000]     vector  : 0xffff0000 - 0xffff1000   (   4 kB)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000]     fixmap  : 0xffc00000 - 0xfff00000   (3072 kB)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000]     vmalloc : 0xdc800000 - 0xff800000   ( 560 MB)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000]     lowmem  : 0xc0000000 - 0xdc000000   ( 448 MB)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000]     modules : 0xbf000000 - 0xc0000000   (  16 MB)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000]       .text : 0xc0008000 - 0xc07c0008   (7905 kB)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000]       .init : 0xc07c1000 - 0xc0820000   ( 380 kB)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000]       .data : 0xc0820000 - 0xc088d490   ( 438 kB)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000]        .bss : 0xc088d490 - 0xc0943050   ( 727 kB)
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] SLUB: HWalign=32, Order=0-3, MinObjects=0, CPUs=1, Nodes=1
Jul 20 22:48:27 raspberrypi kernel: [    0.000000] NR_IRQS:16 nr_irqs:16 16
Jul 20 22:48:27 raspberrypi kernel: [    0.000028] sched_clock: 32 bits at 1000kHz, resolution 1000ns, wraps every 2147483647500ns
Jul 20 22:48:27 raspberrypi kernel: [    0.000072] clocksource: timer: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 1911260446275 ns
Jul 20 22:48:27 raspberrypi kernel: [    0.000175] bcm2835: system timer (irq = 27)
Jul 20 22:48:27 raspberrypi kernel: [    0.000486] Console: colour dummy device 80x30
Jul 20 22:48:27 raspberrypi kernel: [    0.000724] console [tty1] enabled
Jul 20 22:48:27 raspberrypi kernel: [    0.000753] Calibrating delay loop... 697.95 BogoMIPS (lpj=3489792)
Jul 20 22:48:27 raspberrypi kernel: [    0.060315] pid_max: default: 32768 minimum: 301
Jul 20 22:48:27 raspberrypi kernel: [    0.060692] Mount-cache hash table entries: 1024 (order: 0, 4096 bytes)
Jul 20 22:48:27 raspberrypi kernel: [    0.060722] Mountpoint-cache hash table entries: 1024 (order: 0, 4096 bytes)
Jul 20 22:48:27 raspberrypi kernel: [    0.061715] Disabling cpuset control group subsystem
Jul 20 22:48:27 raspberrypi kernel: [    0.061768] Initializing cgroup subsys io
Jul 20 22:48:27 raspberrypi kernel: [    0.061806] Initializing cgroup subsys memory
Jul 20 22:48:27 raspberrypi kernel: [    0.061868] Initializing cgroup subsys devices
Jul 20 22:48:27 raspberrypi kernel: [    0.061902] Initializing cgroup subsys freezer
Jul 20 22:48:27 raspberrypi kernel: [    0.061932] Initializing cgroup subsys net_cls
Jul 20 22:48:27 raspberrypi kernel: [    0.062018] CPU: Testing write buffer coherency: ok
Jul 20 22:48:27 raspberrypi kernel: [    0.062095] ftrace: allocating 20645 entries in 61 pages
Jul 20 22:48:27 raspberrypi kernel: [    0.172610] Setting up static identity map for 0x81c0 - 0x81f8
Jul 20 22:48:27 raspberrypi kernel: [    0.174467] devtmpfs: initialized
Jul 20 22:48:27 raspberrypi kernel: [    0.184062] VFP support v0.3: implementor 41 architecture 1 part 20 variant b rev 5
Jul 20 22:48:27 raspberrypi kernel: [    0.184585] clocksource: jiffies: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 19112604462750000 ns
Jul 20 22:48:27 raspberrypi kernel: [    0.186377] pinctrl core: initialized pinctrl subsystem
Jul 20 22:48:27 raspberrypi kernel: [    0.187255] NET: Registered protocol family 16
Jul 20 22:48:27 raspberrypi kernel: [    0.193013] DMA: preallocated 4096 KiB pool for atomic coherent allocations
Jul 20 22:48:27 raspberrypi kernel: [    0.201762] hw-breakpoint: found 6 breakpoint and 1 watchpoint registers.
Jul 20 22:48:27 raspberrypi kernel: [    0.201792] hw-breakpoint: maximum watchpoint size is 4 bytes.
Jul 20 22:48:27 raspberrypi kernel: [    0.201971] Serial: AMBA PL011 UART driver
Jul 20 22:48:27 raspberrypi kernel: [    0.202476] 20201000.uart: ttyAMA0 at MMIO 0x20201000 (irq = 81, base_baud = 0) is a PL011 rev2
Jul 20 22:48:27 raspberrypi kernel: [    0.202869] console [ttyAMA0] enabled
Jul 20 22:48:27 raspberrypi kernel: [    0.203615] bcm2835-mbox 2000b880.mailbox: mailbox enabled
Jul 20 22:48:27 raspberrypi kernel: [    0.247798] bcm2835-dma 20007000.dma: DMA legacy API manager at f2007000, dmachans=0x1
Jul 20 22:48:27 raspberrypi kernel: [    0.248684] SCSI subsystem initialized
Jul 20 22:48:27 raspberrypi kernel: [    0.249033] usbcore: registered new interface driver usbfs
Jul 20 22:48:27 raspberrypi kernel: [    0.249168] usbcore: registered new interface driver hub
Jul 20 22:48:27 raspberrypi kernel: [    0.249376] usbcore: registered new device driver usb
Jul 20 22:48:27 raspberrypi kernel: [    0.252520] raspberrypi-firmware soc:firmware: Attached to firmware from 2016-11-25 16:03
Jul 20 22:48:27 raspberrypi kernel: [    0.280431] clocksource: Switched to clocksource timer
Jul 20 22:48:27 raspberrypi kernel: [    0.333194] FS-Cache: Loaded
Jul 20 22:48:27 raspberrypi kernel: [    0.333603] CacheFiles: Loaded
Jul 20 22:48:27 raspberrypi kernel: [    0.353021] NET: Registered protocol family 2
Jul 20 22:48:27 raspberrypi kernel: [    0.354363] TCP established hash table entries: 4096 (order: 2, 16384 bytes)
Jul 20 22:48:27 raspberrypi kernel: [    0.354469] TCP bind hash table entries: 4096 (order: 2, 16384 bytes)
Jul 20 22:48:27 raspberrypi kernel: [    0.354571] TCP: Hash tables configured (established 4096 bind 4096)
Jul 20 22:48:27 raspberrypi kernel: [    0.354676] UDP hash table entries: 256 (order: 0, 4096 bytes)
Jul 20 22:48:27 raspberrypi kernel: [    0.354715] UDP-Lite hash table entries: 256 (order: 0, 4096 bytes)
Jul 20 22:48:27 raspberrypi kernel: [    0.355054] NET: Registered protocol family 1
Jul 20 22:48:27 raspberrypi kernel: [    0.355662] RPC: Registered named UNIX socket transport module.
Jul 20 22:48:27 raspberrypi kernel: [    0.355690] RPC: Registered udp transport module.
Jul 20 22:48:27 raspberrypi kernel: [    0.355702] RPC: Registered tcp transport module.
Jul 20 22:48:27 raspberrypi kernel: [    0.355715] RPC: Registered tcp NFSv4.1 backchannel transport module.
Jul 20 22:48:27 raspberrypi kernel: [    0.357141] hw perfevents: enabled with armv6_1176 PMU driver, 3 counters available
Jul 20 22:48:27 raspberrypi kernel: [    0.358545] futex hash table entries: 256 (order: -1, 3072 bytes)
Jul 20 22:48:27 raspberrypi kernel: [    0.375187] VFS: Disk quotas dquot_6.6.0
Jul 20 22:48:27 raspberrypi kernel: [    0.375610] VFS: Dquot-cache hash table entries: 1024 (order 0, 4096 bytes)
Jul 20 22:48:27 raspberrypi kernel: [    0.378293] FS-Cache: Netfs 'nfs' registered for caching
Jul 20 22:48:27 raspberrypi kernel: [    0.379675] NFS: Registering the id_resolver key type
Jul 20 22:48:27 raspberrypi kernel: [    0.379798] Key type id_resolver registered
Jul 20 22:48:27 raspberrypi kernel: [    0.379817] Key type id_legacy registered
Jul 20 22:48:27 raspberrypi kernel: [    0.384281] Block layer SCSI generic (bsg) driver version 0.4 loaded (major 252)
Jul 20 22:48:27 raspberrypi kernel: [    0.384713] io scheduler noop registered
Jul 20 22:48:27 raspberrypi kernel: [    0.384756] io scheduler deadline registered (default)
Jul 20 22:48:27 raspberrypi kernel: [    0.385179] io scheduler cfq registered
Jul 20 22:48:27 raspberrypi kernel: [    0.387921] BCM2708FB: allocated DMA memory 5b800000
Jul 20 22:48:27 raspberrypi kernel: [    0.387998] BCM2708FB: allocated DMA channel 0 @ f2007000
Jul 20 22:48:27 raspberrypi kernel: [    0.411113] Console: switching to colour frame buffer device 160x45
Jul 20 22:48:27 raspberrypi kernel: [    1.344035] bcm2835-rng 20104000.rng: hwrng registered
Jul 20 22:48:27 raspberrypi kernel: [    1.344381] vc-cma: Videocore CMA driver
Jul 20 22:48:27 raspberrypi kernel: [    1.344407] vc-cma: vc_cma_base      = 0x00000000
Jul 20 22:48:27 raspberrypi kernel: [    1.344419] vc-cma: vc_cma_size      = 0x00000000 (0 MiB)
Jul 20 22:48:27 raspberrypi kernel: [    1.344432] vc-cma: vc_cma_initial   = 0x00000000 (0 MiB)
Jul 20 22:48:27 raspberrypi kernel: [    1.344900] vc-mem: phys_addr:0x00000000 mem_base=0x1ec00000 mem_size:0x20000000(512 MiB)
Jul 20 22:48:27 raspberrypi kernel: [    1.370856] brd: module loaded
Jul 20 22:48:27 raspberrypi kernel: [    1.383703] loop: module loaded
Jul 20 22:48:27 raspberrypi kernel: [    1.384860] vchiq: vchiq_init_state: slot_zero = 0xdb880000, is_master = 0
Jul 20 22:48:27 raspberrypi kernel: [    1.387295] Loading iSCSI transport class v2.0-870.
Jul 20 22:48:27 raspberrypi kernel: [    1.388640] usbcore: registered new interface driver smsc95xx
Jul 20 22:48:27 raspberrypi kernel: [    1.388762] dwc_otg: version 3.00a 10-AUG-2012 (platform bus)
Jul 20 22:48:28 raspberrypi kernel: [    1.389783] usbcore: registered new interface driver usb-storage
Jul 20 22:48:28 raspberrypi kernel: [    1.390646] mousedev: PS/2 mouse device common for all mice
Jul 20 22:48:28 raspberrypi kernel: [    1.392289] bcm2835-cpufreq: min=700000 max=700000
Jul 20 22:48:28 raspberrypi kernel: [    1.392769] sdhci: Secure Digital Host Controller Interface driver
Jul 20 22:48:28 raspberrypi kernel: [    1.392792] sdhci: Copyright(c) Pierre Ossman
Jul 20 22:48:28 raspberrypi kernel: [    1.393395] sdhost: log_buf @ db810000 (5b810000)
Jul 20 22:48:28 raspberrypi kernel: [    1.450515] mmc0: sdhost-bcm2835 loaded - DMA enabled (>1)
Jul 20 22:48:28 raspberrypi kernel: [    1.451096] sdhci-pltfm: SDHCI platform and OF driver helper
Jul 20 22:48:28 raspberrypi kernel: [    1.451970] ledtrig-cpu: registered to indicate activity on CPUs
Jul 20 22:48:28 raspberrypi kernel: [    1.452258] hidraw: raw HID events driver (C) Jiri Kosina
Jul 20 22:48:28 raspberrypi kernel: [    1.452593] usbcore: registered new interface driver usbhid
Jul 20 22:48:28 raspberrypi kernel: [    1.452612] usbhid: USB HID core driver
Jul 20 22:48:28 raspberrypi kernel: [    1.473699] Initializing XFRM netlink socket
Jul 20 22:48:28 raspberrypi kernel: [    1.473769] NET: Registered protocol family 17
Jul 20 22:48:28 raspberrypi kernel: [    1.473999] Key type dns_resolver registered
Jul 20 22:48:28 raspberrypi kernel: [    1.476254] registered taskstats version 1
Jul 20 22:48:28 raspberrypi kernel: [    1.476622] vc-sm: Videocore shared memory driver
Jul 20 22:48:28 raspberrypi kernel: [    1.476659] [vc_sm_connected_init]: start
Jul 20 22:48:28 raspberrypi kernel: [    1.477734] [vc_sm_connected_init]: end - returning 0
Jul 20 22:48:28 raspberrypi kernel: [    1.478403] of_cfs_init
Jul 20 22:48:28 raspberrypi kernel: [    1.478570] of_cfs_init: OK
Jul 20 22:48:28 raspberrypi kernel: [    1.480115] Waiting for root device /dev/mmcblk0p2...
Jul 20 22:48:28 raspberrypi kernel: [    1.560240] mmc0: host does not support reading read-only switch, assuming write-enable
Jul 20 22:48:28 raspberrypi kernel: [    1.563282] mmc0: new high speed SDHC card at address e624
Jul 20 22:48:28 raspberrypi kernel: [    1.564377] mmcblk0: mmc0:e624 SU08G 7.40 GiB
Jul 20 22:48:28 raspberrypi kernel: [    1.569545]  mmcblk0: p1 p2
Jul 20 22:48:28 raspberrypi kernel: [    1.594803] EXT4-fs (mmcblk0p2): mounted filesystem with ordered data mode. Opts: (null)
Jul 20 22:48:28 raspberrypi kernel: [    1.594911] VFS: Mounted root (ext4 filesystem) readonly on device 179:2.
Jul 20 22:48:28 raspberrypi kernel: [    1.609510] devtmpfs: mounted
Jul 20 22:48:28 raspberrypi kernel: [    1.610915] Freeing unused kernel memory: 380K (c07c1000 - c0820000)
Jul 20 22:48:28 raspberrypi kernel: [    1.921582] random: systemd: uninitialized urandom read (16 bytes read, 8 bits of entropy available)
Jul 20 22:48:28 raspberrypi kernel: [    2.075136] NET: Registered protocol family 10
Jul 20 22:48:28 raspberrypi kernel: [    2.306714] random: systemd-sysv-ge: uninitialized urandom read (16 bytes read, 11 bits of entropy available)
Jul 20 22:48:28 raspberrypi kernel: [    2.324562] uart-pl011 20201000.uart: no DMA platform data
Jul 20 22:48:28 raspberrypi kernel: [    2.510867] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 20 22:48:28 raspberrypi kernel: [    2.513077] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 20 22:48:28 raspberrypi kernel: [    2.515495] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 20 22:48:28 raspberrypi kernel: [    2.548583] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 20 22:48:28 raspberrypi kernel: [    2.550199] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 20 22:48:28 raspberrypi kernel: [    2.550744] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 20 22:48:28 raspberrypi kernel: [    2.635251] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 20 22:48:28 raspberrypi kernel: [    2.660826] random: systemd: uninitialized urandom read (16 bytes read, 13 bits of entropy available)
Jul 20 22:48:28 raspberrypi kernel: [    3.840614] dwc2 20980000.usb: EPs: 8, dedicated fifos, 4080 entries in SPRAM
Jul 20 22:48:28 raspberrypi kernel: [    4.403538] dwc2 20980000.usb: DWC OTG Controller
Jul 20 22:48:28 raspberrypi kernel: [    4.403638] dwc2 20980000.usb: new USB bus registered, assigned bus number 1
Jul 20 22:48:28 raspberrypi kernel: [    4.403728] dwc2 20980000.usb: irq 33, io mem 0x00000000
Jul 20 22:48:28 raspberrypi kernel: [    4.404175] usb usb1: New USB device found, idVendor=1d6b, idProduct=0002
Jul 20 22:48:28 raspberrypi kernel: [    4.404204] usb usb1: New USB device strings: Mfr=3, Product=2, SerialNumber=1
Jul 20 22:48:28 raspberrypi kernel: [    4.404224] usb usb1: Product: DWC OTG Controller
Jul 20 22:48:28 raspberrypi kernel: [    4.404243] usb usb1: Manufacturer: Linux 4.4.34+ dwc2_hsotg
Jul 20 22:48:28 raspberrypi kernel: [    4.404260] usb usb1: SerialNumber: 20980000.usb
Jul 20 22:48:28 raspberrypi kernel: [    4.405694] hub 1-0:1.0: USB hub found
Jul 20 22:48:28 raspberrypi kernel: [    4.405814] hub 1-0:1.0: 1 port detected
Jul 20 22:48:28 raspberrypi kernel: [    4.523342] using random self ethernet address
Jul 20 22:48:28 raspberrypi kernel: [    4.523396] using random host ethernet address
Jul 20 22:48:28 raspberrypi kernel: [    4.524877] usb0: HOST MAC ce:2b:61:78:61:a6
Jul 20 22:48:28 raspberrypi kernel: [    4.525019] usb0: MAC da:59:e0:7f:40:3f
Jul 20 22:48:28 raspberrypi kernel: [    4.525110] using random self ethernet address
Jul 20 22:48:28 raspberrypi kernel: [    4.525142] using random host ethernet address
Jul 20 22:48:28 raspberrypi kernel: [    4.525293] g_ether gadget: Ethernet Gadget, version: Memorial Day 2008
Jul 20 22:48:28 raspberrypi kernel: [    4.525317] g_ether gadget: g_ether ready
Jul 20 22:48:28 raspberrypi kernel: [    4.535739] dwc2 20980000.usb: bound driver g_ether
Jul 20 22:48:28 raspberrypi kernel: [    4.607146] fuse init (API version 7.23)
Jul 20 22:48:28 raspberrypi kernel: [    4.642691] i2c /dev entries driver
Jul 20 22:48:28 raspberrypi kernel: [    6.250783] bcm2835-wdt 20100000.watchdog: Broadcom BCM2835 watchdog timer
Jul 20 22:48:28 raspberrypi kernel: [    6.303811] gpiomem-bcm2835 20200000.gpiomem: Initialised: Registers at 0x20200000
Jul 20 22:48:28 raspberrypi kernel: [    6.474568] bcm2708_i2c 20804000.i2c: BSC1 Controller at 0x20804000 (irq 77) (baudrate 100000)
Jul 20 22:48:28 raspberrypi kernel: [    6.546966] EXT4-fs (mmcblk0p2): re-mounted. Opts: (null)
Jul 20 22:48:28 raspberrypi kernel: [   15.288158] cfg80211: World regulatory domain updated:
Jul 20 22:48:28 raspberrypi kernel: [   15.288210] cfg80211:  DFS Master region: unset
Jul 20 22:48:28 raspberrypi kernel: [   15.288226] cfg80211:   (start_freq - end_freq @ bandwidth), (max_antenna_gain, max_eirp), (dfs_cac_time)
Jul 20 22:48:28 raspberrypi kernel: [   15.288250] cfg80211:   (2402000 KHz - 2472000 KHz @ 40000 KHz), (N/A, 2000 mBm), (N/A)
Jul 20 22:48:28 raspberrypi kernel: [   15.288274] cfg80211:   (2457000 KHz - 2482000 KHz @ 40000 KHz), (N/A, 2000 mBm), (N/A)
Jul 20 22:48:28 raspberrypi kernel: [   15.288292] cfg80211:   (2474000 KHz - 2494000 KHz @ 20000 KHz), (N/A, 2000 mBm), (N/A)
Jul 20 22:48:28 raspberrypi kernel: [   15.288313] cfg80211:   (5170000 KHz - 5250000 KHz @ 80000 KHz, 160000 KHz AUTO), (N/A, 2000 mBm), (N/A)
Jul 20 22:48:28 raspberrypi kernel: [   15.288339] cfg80211:   (5250000 KHz - 5330000 KHz @ 80000 KHz, 160000 KHz AUTO), (N/A, 2000 mBm), (0 s)
Jul 20 22:48:28 raspberrypi kernel: [   15.288356] cfg80211:   (5490000 KHz - 5730000 KHz @ 160000 KHz), (N/A, 2000 mBm), (0 s)
Jul 20 22:48:28 raspberrypi kernel: [   15.288373] cfg80211:   (5735000 KHz - 5835000 KHz @ 80000 KHz), (N/A, 2000 mBm), (N/A)
Jul 20 22:48:28 raspberrypi kernel: [   15.288395] cfg80211:   (57240000 KHz - 63720000 KHz @ 2160000 KHz), (N/A, 0 mBm), (N/A)
Jul 20 22:48:28 raspberrypi kernel: [   16.944146] Adding 102396k swap on /var/swap.  Priority:-1 extents:3 across:208896k SSFS
Jul 20 22:48:32 raspberrypi kernel: [   20.317466] IPv6: ADDRCONF(NETDEV_UP): usb0: link is not ready
Jul 20 22:48:32 raspberrypi kernel: [   20.644316] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 22:48:49 raspberrypi kernel: [   37.981852] Bluetooth: Core ver 2.21
Jul 20 22:48:49 raspberrypi kernel: [   37.982074] NET: Registered protocol family 31
Jul 20 22:48:49 raspberrypi kernel: [   37.982101] Bluetooth: HCI device and connection manager initialized
Jul 20 22:48:49 raspberrypi kernel: [   37.982140] Bluetooth: HCI socket layer initialized
Jul 20 22:48:49 raspberrypi kernel: [   37.982174] Bluetooth: L2CAP socket layer initialized
Jul 20 22:48:49 raspberrypi kernel: [   37.982271] Bluetooth: SCO socket layer initialized
Jul 20 22:48:49 raspberrypi kernel: [   38.043784] random: nonblocking pool is initialized
Jul 20 22:48:49 raspberrypi kernel: [   38.111444] Bluetooth: BNEP (Ethernet Emulation) ver 1.3
Jul 20 22:48:49 raspberrypi kernel: [   38.111483] Bluetooth: BNEP filters: protocol multicast
Jul 20 22:48:49 raspberrypi kernel: [   38.111531] Bluetooth: BNEP socket layer initialized
Jul 20 22:48:49 raspberrypi vncserver-x11[433]: ServerManager: Server started
Jul 20 22:48:51 raspberrypi vncserver-x11[433]: ConsoleDisplay: Found running X server (pid=512)
Jul 20 22:48:52 raspberrypi kernel: [   40.857078] dwc2 20980000.usb: new device is high-speed
Jul 20 22:48:52 raspberrypi kernel: [   41.021492] dwc2 20980000.usb: new device is high-speed
Jul 20 22:48:52 raspberrypi kernel: [   41.122796] dwc2 20980000.usb: new address 1
Jul 20 22:48:55 raspberrypi org.gtk.Private.AfcVolumeMonitor[626]: Volume monitor alive
Jul 20 22:48:56 raspberrypi kernel: [   44.332973] g_ether gadget: high-speed config #2: RNDIS
Jul 20 22:48:56 raspberrypi kernel: [   44.333249] IPv6: ADDRCONF(NETDEV_CHANGE): usb0: link becomes ready
Jul 20 22:50:48 raspberrypi vncserver-x11[433]: Connections: connected: [fe80::65e3:189e:64ee:e47f%usb0]::50696
Jul 20 22:50:50 raspberrypi vncserver-x11[433]: Connections: authenticated: [fe80::65e3:189e:64ee:e47f%usb0]::50696, as pi (f permissions)
Jul 20 22:51:05 raspberrypi kernel: [  173.775413] warning: process `colord-sane' used the deprecated sysctl system call with 8.1.2.
Jul 20 23:09:23 raspberrypi kernel: [ 1272.045142] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 23:09:44 raspberrypi kernel: [ 1292.440688] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 05:14:09 raspberrypi kernel: [ 1332.115302] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 05:14:33 raspberrypi kernel: [ 1356.739484] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 05:16:55 raspberrypi kernel: [ 1497.804750] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 05:50:38 raspberrypi kernel: [ 3521.360629] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 05:51:46 raspberrypi kernel: [ 3589.233882] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 06:08:13 raspberrypi kernel: [ 4576.251603] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 06:08:13 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 06:08:43 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 06:09:10 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 06:09:40 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 06:11:00 raspberrypi kernel: [ 4743.247074] gpiomem-bcm2835 20200000.gpiomem: gpiomem device opened.
Jul 20 06:11:00 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 06:11:30 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 06:17:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 06:17:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 06:25:01 raspberrypi rsyslogd-2007: action 'action 17' suspended, next retry is Thu Jul 20 06:25:31 2017 [try http://www.rsyslog.com/e/2007 ]
Jul 20 06:25:19 raspberrypi rsyslogd: [origin software="rsyslogd" swVersion="8.4.2" x-pid="382" x-info="http://www.rsyslog.com"] rsyslogd was HUPed
