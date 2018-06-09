import pigpio
import sys
from time import sleep
import RPi.GPIO as GPIO

AZIMUTH_STEP_PIN = 22  # board pin number 32
AZIMUTH_DIR_PIN = 17  # board pin number 33

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(AZIMUTH_DIR_PIN, GPIO.OUT)
if sys.argv[2] == "1":
  GPIO.output(AZIMUTH_DIR_PIN, GPIO.HIGH )
else:
  GPIO.output(AZIMUTH_DIR_PIN, GPIO.LOW )


HIGH=1
LOW=0

PWM_FREQUENCY = int(sys.argv[1])
EFFECTIVE_DUTY_CYCLE = 0.5
MAX_DUTY_CYCLE = 1000000
DUTY_CYCLE = int(EFFECTIVE_DUTY_CYCLE * MAX_DUTY_CYCLE)

pi = pigpio.pi()
pi.set_PWM_dutycycle(AZIMUTH_STEP_PIN, 127)
pi.set_PWM_frequency(AZIMUTH_STEP_PIN, PWM_FREQUENCY)
#sleep(20)
#pi.hardware_PWM(ELEVATION_STEP, PWM_FREQUENCY, DUTY_CYCLE)
#pi.hardware_PWM(PWM_PIN2_GPIO, PWM_FREQUENCY, DUTY_CYCLE)
