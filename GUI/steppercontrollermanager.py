#from steppercontroller import StepperController


class StepperControllerManager(object):

    def __init__(self):
        pass

    def move(self, distance, direction, units):
        print(distance, direction, units)

    def moveForever(self, direction):
        print(direction)
