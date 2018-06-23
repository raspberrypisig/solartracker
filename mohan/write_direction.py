import pigpio
import sys
#import RPi.GPIO as GPIO

'''
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17, GPIO.OUT)
if int(sys.argv[1]) == 0:
  GPIO.output(17, GPIO.LOW)
else:
  GPIO.output(17, GPIO.HIGH)
'''

pi = pigpio.pi()
pi.set_mode(17, pigpio.OUTPUT)
if int(sys.argv[1]) == 0:
  pi.write(17, 0)
else:
  pi.write(17, 1)
pi.stop()
