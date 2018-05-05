import suncalc
from math import pi


class TrackSun:

    def __init__(self):
        pass

    def calculatePositionOfSun(self, current_time, latitude, longitude):
        position = suncalc.solarPosition(current_time, latitude, longitude)
        azimuth = 180 + (position['azimuth'] * 180.0 / pi)
        altitude = position['altitude'] * 180.0 / pi
        return azimuth, altitude
