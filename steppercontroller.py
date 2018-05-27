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

    def pwm(self, PWMfreq=650):
        StepperController.PI.hardware_PWM(self.step_pin,PWMfreq,StepperController.DUTY_CYCLE)

    def move(self, length):
        pulsetime = 0.2 * length
        self.pwm()
        sleep(pulsetime/1000)
        self.stop()

    def setDirection(self, direction):
        StepperController.PI.write(self.step_pin, direction)

    def moveForward(self, length):
        self.setDirection(StepperController.CLOCKWISE)
        self.move(length)

    def moveBackwards(self, length):
        self.setDirection(StepperController.ANTICLOCKWISE)
        self.move(length)

    def stop(self):
        self.pwm(0)
