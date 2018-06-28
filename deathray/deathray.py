import json
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject
from solartrackercontroller import SolarTrackerController
from suncalc import getFinalSolarPosition
import threading
from time import sleep
from datetime import datetime
import pytz
from stepperjobcontrol import StepperJobControl
from queue import Queue


class StepperControllerHandler(object):

    def __init__(self, builder, sendQueue, receiveQueue):
        self.builder = builder
        self.sendQueue = sendQueue
        self.receiveQueue = receiveQueue

        self.controller = SolarTrackerController()
        config = self.load_data_from_config("config.json")
        self.config = config
        self.initialiseApp()
        self.position = {
            'azimuth': 0,
            'elevation': 0
        }
        builder.get_object("position_azimuth").set_text(str(0))
        builder.get_object("position_elevation").set_text(str(0))

        ampm = builder.get_object("ampm")
        ampm.append_text("AM")
        ampm.append_text("PM")
        ampm.set_active(0)

    def load_data_from_config(self, configFile):
        configHandle = open(configFile, 'r')
        config = json.loads(configHandle.read())
        configHandle.close()
        # print(config)
        return config

    def initialiseApp(self):
        data = [
            {
                "name": "azimuth_speed",
                "key": "speed",
                "subkey": "azimuth"
            },
            {
                "name": "elevation_speed",
                "key": "speed",
                "subkey": "elevation"
            },
            {
                "name": "homing_speed",
                "key": "speed",
                "subkey": "homing"
            },
            {
                "name": "jogging_speed",
                "key": "speed",
                "subkey": "jogging"
            },
            {
                "name": "jogging_distance",
                "key": "jogging",
                "subkey": "distance"
            },
            {
                "name": "sunposition_latitude",
                "key": "sunposition",
                "subkey": "latitude"
            },
            {
                "name": "sunposition_longitude",
                "key": "sunposition",
                "subkey": "longitude"
            }
        ]
        [self.builder.get_object(i['name']).set_text(
            str(self.config[i['key']][i['subkey']])) for i in data]

    def operationSelected(self, widget, data=None):
        if widget.get_active():
            operation = Gtk.Buildable.get_name(widget)
            homing_frame = self.builder.get_object("homing_frame")
            positioning_frame = self.builder.get_object("positioning_frame")
            jogging_frame = self.builder.get_object("jogging_frame")
            homing_frame.set_visible(False)
            positioning_frame.set_visible(False)
            jogging_frame.set_visible(False)
            if operation == 'jogging':
                jogging_frame.set_visible(True)
            elif operation == 'homing':
                homing_frame.set_visible(True)
            elif operation == 'positioning':
                positioning_frame.set_visible(True)
            else:
                positioning_frame.set_visible(True)

    def stop(self, widget):
        moving = self.builder.get_object("moving_indicator")
        self.controller.stop()

    def joggingDistance(self):
        travelTextBox = self.builder.get_object("jogging_distance")
        return float(travelTextBox.get_text())

    def home(self, widget, data=None):
        widgetname = Gtk.Buildable.get_name(widget)
        PWMfreqTextBox = self.builder.get_object("homing_speed")
        PWMfreq = int(PWMfreqTextBox.get_text())
        if widgetname == 'home_azimuth':
            self.controller.home_azimuth(PWMfreq)
        elif widgetname == 'home_elevation':
            self.controller.home_elevation(PWMfreq)
        elif widgetname == 'limit_elevation':
            self.controller.limit_elevation(PWMfreq)
        elif widgetname == 'limit_azimuth':
            self.controller.limit_azimuth(PWMfreq)

    def arrowPressed(self, widget, data=None):
        arrow = Gtk.Buildable.get_name(widget)
        distance = self.joggingDistance()
        PWMfreqTextBox = self.builder.get_object("jogging_speed")
        PWMFreq = PWMfreqTextBox.get_text()
        self.controller.arrowPressed(arrow, distance, PWMFreq)
        self.sendQueue.put({
            'arrow': arrow,
            'distance': distance,
            'PWMFreq': PWMFreq})

    def sunposition_calculate(self, widget, data=None):
        latitudeTextBox = self.builder.get_object("sunposition_latitude")
        longitudeTextBox = self.builder.get_object("sunposition_longitude")
        latitude = float(latitudeTextBox.get_text())
        longitude = float(longitudeTextBox.get_text())
        day = int(self.builder.get_object("day").get_text())
        month = int(self.builder.get_object("month").get_text())
        year = int(self.builder.get_object("year").get_text())
        hour = int(self.builder.get_object("hour").get_text())
        minute = int(self.builder.get_object("minute").get_text())
        ampm = self.builder.get_object("ampm")
        if ampm.get_active_text() == 'PM':
            if hour != 12:
                hour = hour + 12
        localtz = pytz.timezone('Australia/Melbourne')
        enteredTime = datetime(
            year, month, day, hour, minute)
        utcTime = localtz.localize(enteredTime).astimezone(pytz.utc)
        print(utcTime.year,
              utcTime.month,
              utcTime.day,
              utcTime.hour,
              utcTime.minute)
        adjustedTime = datetime(
            utcTime.year,
            utcTime.month,
            utcTime.day,
            utcTime.hour,
            utcTime.minute)
        print(adjustedTime)
        position = getFinalSolarPosition(latitude, longitude, adjustedTime)
        azimuthLabel = self.builder.get_object("sunposition_azimuth")
        azimuthLabel.set_text(str(position['azimuth']))
        elevationLabel = self.builder.get_object("sunposition_elevation")
        elevationLabel.set_text(str(position['elevation']))

    def startTimer(self):
        GObject.timeout_add_seconds(1, self.updateGUI)

    def updateGUI(self):
        data = None
        while not self.receiveQueue.empty():
            data = self.receiveQueue.get()
            azimuth = str(data['azimuth'])
            elevation = str(data['elevation'])
            positionAzimuthLabel = self.builder.get_object(
                "position_azimuth")
            positionAzimuthLabel.set_text(azimuth)
            positionElevationLabel = self.builder.get_object(
                "position_elevation")
            positionElevationLabel.set_text(elevation)
        return True

    def changeTab(self, notebook, paned, tab):
        # sunposition tab
        if tab == 2:
            now = datetime.now()
            self.builder.get_object("day").set_text(str(now.day))
            self.builder.get_object("month").set_text(str(now.month))
            self.builder.get_object("year").set_text(str(now.year))
            self.builder.get_object("minute").set_text(
                '{d:02}'.format(d=now.minute))
            if now.hour > 12:
                hour = now.hour - 12
                self.builder.get_object("ampm").set_active(1)
            else:
                hour = now.hour
                self.builder.get_object("ampm").set_active(0)
            self.builder.get_object("hour").set_text(str(hour))


def app_main():
    builder = Gtk.Builder()
    builder.add_from_file("deathray.glade")

    window = builder.get_object("mainwindow")
    window.connect("destroy", Gtk.main_quit)
    window.show_all()

    sendQueue = Queue()
    receiveQueue = Queue()

    handler = StepperControllerHandler(builder, sendQueue, receiveQueue)
    builder.connect_signals(handler)

    updateTimer = threading.Thread(target=handler.startTimer)
    updateTimer.daemon = True
    updateTimer.start()

    jobControl = StepperJobControl(sendQueue, receiveQueue)
    jobControl.daemon = True
    jobControl.start()

if __name__ == '__main__':
    app_main()
    Gtk.main()
