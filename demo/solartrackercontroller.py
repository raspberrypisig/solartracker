from time import sleep
import pigpio
import RPi.GPIO as GPIO


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
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.dirPin, GPIO.OUT)

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
            GPIO.output(self.dirPin, StepperMotor.FORWARD)

        else:
            print("moving in reverse...")
            GPIO.output(self.dirPin, StepperMotor.REVERSE)

    def moveForever(self, direction, PWMfreq):
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

    def demo_first_quarter(self):
        self.elevationStepper.moveForever(StepperMotor.REVERSE)
        self.azimuthStepper.moveForever(StepperMotor.FORWARD)

    def demo_second_quarter(self):
        self.elevationStepper.moveForever(StepperMotor.FORWARD)
        self.azimuthStepper.moveForever(StepperMotor.FORWARD)

    def demo_third_quarter(self):
        self.elevationStepper.moveForever(StepperMotor.REVERSE)
        self.azimuthStepper.moveForever(StepperMotor.REVERSE)

    def demo_fourth_quarter(self):
        self.elevationStepper.moveForever(StepperMotor.FORWARD)
        self.azimuthStepper.moveForever(StepperMotor.REVERSE)

    def demo_start(self, pauseInterval):
        print("demo starting...")
        # self.demo_first_quarter()
        # sleep(pauseInterval)
        # self.demo_second_quarter()
        # sleep(pauseInterval)
        # self.demo_third_quarter()
        # sleep(pauseInterval)
        # self.demo_fourth_quarter()

    def home_azimuth(self, PWMfreq):
        self.azimuthStepper.moveForever(
            direction=StepperMotor.REVERSE, PWMfreq=PWMfreq)

    def home_elevation(self, PWMfreq):
        self.elevationStepper.moveForever(
            direction=StepperMotor.FORWARD, PWMfreq=PWMfreq)

    def limit_azimuth(self, PWMfreq):
        self.azimuthStepper.moveForever(
            direction=StepperMotor.FORWARD, PWMfreq=PWMfreq)

    def limit_elevation(self, PWMfreq):
        self.elevationStepper.moveForever(
            direction=StepperMotor.REVERSE, PWMfreq=PWMfreq)

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
