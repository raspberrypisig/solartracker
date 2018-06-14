import RPi.GPIO as GPIO

HOME_LIMIT_SWITCH_PIN = 5

def boo(channel):
  print(channel)
  

GPIO.add_event_detect(HOME_LIMIT_SWITCH_PIN, GPIO.FALLING, callback=boo)

