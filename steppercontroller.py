import pigpio
from time import sleep


class StepperController(object):
    EFFECTIVE_DUTY_CYCLE = 0.5
    MAX_DUTY_CYCLE = 1000000
    DUTY_CYCLE = int(EFFECTIVE_DUTY_CYCLE * MAX_DUTY_CYCLE)
    CLOCKWISE = 0
    ANTICLOCKWISE = 1
    PI = pigpio.pi()

    def __init__(self, step_pin, dir_pin):
        self.step_pin = step_pin
        self.dir_pin = dir_pin

    def hardware_pwm(self, PWMfreq=650):
        StepperController.PI.hardware_pwm(
            self.step_pin,
            PWMfreq,
            StepperController.DUTY_CYCLE)

    def move(self, length):
        pulsetime = 0.2 * length
        self.hardware_pwm()
        sleep(pulsetime)
        self.stop()

    def setDirection(self, direction):
        StepperController.PI.write(self.step_pin, direction)

    def moveForward(self, length):
        self.setDirection(StepperController.CLOCKWISE)
        move(length)

    def moveBackwards(self, length):
        self.setDirection(StepperController.ANTICLOCKWISE)
        move(length)

    def stop(self):
        self.hardware_pwm(self.step_pin, 0)
