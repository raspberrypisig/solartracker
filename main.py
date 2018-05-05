from tracksun import TrackSun
from datetime import datetime

LATITUDE = -37.94514
LONGITUDE = 145.07791
current_time = datetime.utcnow()

tracker = TrackSun()
azimuth, altitude = tracker.calculatePositionOfSun(
    current_time, LATITUDE, LONGITUDE)
print("Azimuth: {0}".format(azimuth))
print("Altitude: {0}".format(altitude))
