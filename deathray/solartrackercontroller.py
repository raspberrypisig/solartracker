from time import sleep
import pigpio
#import RPi.GPIO as GPIO


class StepperMotor:
    FORWARD = 1
    REVERSE = 0
    DUTY_CYCLE = 128
    STEPS_PER_REV = 200.0

    def __init__(self, stepPin, dirPin):
        self.stepPin = stepPin
        self.dirPin = dirPin
        self.position = 0
        self.pi = pigpio.pi()
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setwarnings(False)
        #GPIO.setup(self.dirPin, GPIO.OUT)

    def stop(self):
        print("stop")
        self.pi.set_mode(self.stepPin, pigpio.OUTPUT)
        self.pi.write(self.stepPin, level=0)

    def move(self, distance, direction, PWMfreq):
        print(distance, "mm", direction, PWMfreq, "hz")
        self.position = self.position + distance
        #self.pi.set_PWM_dutycycle(self.stepPin, 128)
        #self.pi.set_PWM_frequency(self.stepPin, PWMfreq)
        #sleep(distance * STEPS_PER_REV / PWMfreq)
        # self.stop()

    def setSpeed(self, PWMfreq):
        self.PWMfreq = PWMfreq

    def setDirection(self, direction):
        if direction == StepperMotor.FORWARD:
            print("moving forward...")
            self.pi.set_mode(self.stepPin, pigpio.OUTPUT)
            self.pi.write(self.stepPin, 1)
            #GPIO.output(self.dirPin, StepperMotor.FORWARD)

        else:
            print("moving in reverse...")
            self.pi.set_mode(self.stepPin, pigpio.OUTPUT)
            self.pi.write(self.stepPin, 0)
            #GPIO.output(self.dirPin, StepperMotor.REVERSE)

    def moveForever(self, direction, PWMfreq=None):
        if PWMfreq is None:
            PWMfreq = self.PWMfreq
        self.setDirection(direction)
        print("Step Pin:", self.stepPin)
        print("Moving forever...")
        print("PWMfreq", PWMfreq, "Hz")
        self.pi.set_PWM_dutycycle(self.stepPin, 128)
        self.pi.set_PWM_frequency(self.stepPin, PWMfreq)

    def getPosition(self):
        return self.position


class SolarTrackerController(object):
    ELEVATION_STEP_PIN = 11
    ELEVATION_DIR_PIN = 27
    AZIMUTH_STEP_PIN = 22
    AZIMUTH_DIR_PIN = 17

    def __init__(self):
        self.elevationStepper = StepperMotor(
            SolarTrackerController.ELEVATION_STEP_PIN, SolarTrackerController.ELEVATION_DIR_PIN)
        self.azimuthStepper = StepperMotor(
            SolarTrackerController.AZIMUTH_STEP_PIN,
            SolarTrackerController.AZIMUTH_DIR_PIN)

    def stop(self):
        self.elevationStepper.stop()
        self.azimuthStepper.stop()

    def setAzimuthSpeed(self, PWMfreq):
        self.azimuthStepper.setSpeed(PWMfreq)

    def setElevationSpeed(self, PWMfreq):
        self.elevationStepper.setSpeed(PWMfreq)

    def home_azimuth(self, PWMfreq):
        self.azimuthStepper.moveForever(
            direction=StepperMotor.FORWARD, PWMfreq=PWMfreq)

    def home_elevation(self, PWMfreq):
        self.elevationStepper.moveForever(
            direction=StepperMotor.REVERSE, PWMfreq=PWMfreq)

    def limit_azimuth(self, PWMfreq):
        self.azimuthStepper.moveForever(
            direction=StepperMotor.REVERSE, PWMfreq=PWMfreq)

    def limit_elevation(self, PWMfreq):
        self.elevationStepper.moveForever(
            direction=StepperMotor.FORWARD, PWMfreq=PWMfreq)

    '''
    def arrowPressed(self, arrow, distance, PWMfreq):
        if arrow == 'uparrow':
            self.elevationStepper.move(
                distance=distance, direction=StepperMotor.FORWARD, PWMfreq=PWMfreq)

        elif arrow == 'downarrow':
            self.elevationStepper.move(
                distance=distance, direction=StepperMotor.REVERSE, PWMfreq=PWMfreq)

        elif arrow == 'leftarrow':
            self.azimuthStepper.move(
                distance=distance, direction=StepperMotor.REVERSE, PWMfreq=PWMfreq)
        else:
            self.azimuthStepper.move(
                distance=distance, direction=StepperMotor.FORWARD, PWMfreq=PWMfreq)
    '''

    def tx_pulses(pi, GPIO, hertz, num, pulse_len=1):
        assert hertz < 500000
        length_us = int(1000000 / hertz)
        assert int(pulse_len) < length_us
        assert num < 65536

        num_low = num % 256
        num_high = num // 256

        wf = []
        pulse_length = length_us / 2
        wf.append(pigpio.pulse(1 << GPIO, 0, pulse_len))
        wf.append(pigpio.pulse(0, 1 << GPIO, length_us - pulse_len))

        pi.wave_add_generic(wf)
        wid = pi.wave_create()

        if wid >= 0:
            pi.wave_chain([255, 0, wid, 255, 1, num_low, num_high])
            while pi.wave_tx_busy():
                time.sleep(0.01)
            pi.wave_delete(wid)
