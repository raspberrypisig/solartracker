import pigpio


AZIMUTH_STEP_PIN = 22  # board pin number 32
AZIMUTH_DIR_PIN = 17  # board pin number 33
ELEVATION_STEP_PIN = 11


pi = pigpio.pi()
pi.set_mode(AZIMUTH_STEP_PIN, pigpio.OUTPUT)
pi.write(AZIMUTH_STEP_PIN, 0)
pi.set_mode(ELEVATION_STEP_PIN, pigpio.OUTPUT)
pi.write(ELEVATION_STEP_PIN, 0)

