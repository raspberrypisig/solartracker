# python pwmtest.py 650
# python pwmtest.py 0

import pigpio
import sys

PWM_PIN1_GPIO = 12  # board pin number 32
PWM_PIN2_GPIO = 13  # board pin number 33

PWM_FREQUENCY = int(sys.argv[1])
EFFECTIVE_DUTY_CYCLE = 0.5
MAX_DUTY_CYCLE = 1000000
DUTY_CYCLE = int(EFFECTIVE_DUTY_CYCLE * MAX_DUTY_CYCLE)

pi = pigpio.pi()


pi.hardware_PWM(PWM_PIN1_GPIO, PWM_FREQUENCY, DUTY_CYCLE)
pi.hardware_PWM(PWM_PIN2_GPIO, PWM_FREQUENCY, DUTY_CYCLE)

