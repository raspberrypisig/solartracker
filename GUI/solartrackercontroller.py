class StepperMotor:
    HIGH = 1
    LOW = 0

    def __init__(self, stepPin, dirPin):
        self.stepPin = stepPin
        self.dirPin = dirPin
        self.position = 0

    def stop(self):
        print("stop")

    def move(self, distance, direction, speed=650):
        print(distance, direction, speed)
        self.position = self.position + distance

    def getPosition(self):
        return self.position


class SolarTrackerController(object):
    ELEVATION_STEP_PIN = 12
    ELEVATION_DIR_PIN = 4
    AZIMUTH_STEP_PIN = 13
    AZIMUTH_DIR_PIN = 5

    def __init__(self):
        self.elevationStepper = StepperMotor(
            SolarTrackerController.ELEVATION_STEP_PIN, SolarTrackerController.ELEVATION_DIR_PIN)
        self.azimuthStepper = StepperMotor(
            SolarTrackerController.AZIMUTH_STEP_PIN,
            SolarTrackerController.AZIMUTH_DIR_PIN)

    def stop(self):
        self.elevationStepper.stop()
        self.azimuthStepper.stop()

    def arrowPressed(self, arrow, distance):
        if arrow == 'uparrow':
            self.elevationStepper.move(
                distance=distance, direction=StepperMotor.HIGH)

        elif arrow == 'downarrow':
            self.elevationStepper.move(
                distance=distance, direction=StepperMotor.LOW)

        elif arrow == 'leftarrow':
            self.azimuthStepper.move(
                distance=distance, direction=StepperMotor.LOW)
        else:
            self.azimuthStepper.move(
                distance=distance, direction=StepperMotor.LOW)
