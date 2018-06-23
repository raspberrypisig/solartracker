import pigpio

pi = pigpio.pi()
pi.set_mode(17, pigpio.OUTPUT)
level = pi.read(17)
pi.stop()
print(level)
