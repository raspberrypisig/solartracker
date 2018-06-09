import RPi.GPIO as GPIO
from time import sleep


ELEVATION_DIR_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(ELEVATION_DIR_PIN, GPIO.OUT)
GPIO.output(ELEVATION_DIR_PIN, GPIO.HIGH )
sleep(2)
