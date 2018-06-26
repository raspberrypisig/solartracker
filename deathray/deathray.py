import json
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject
from solartrackercontroller import SolarTrackerController
from suncalc import getFinalSolarPosition
import threading
from time import sleep


class StepperControllerHandler(object):

    def __init__(self, builder):
        self.builder = builder
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

    def demo_start(self, widget, data=None):
        azimuthTextBox = self.builder.get_object("azimuth_speed")
        elevationTextBox = self.builder.get_object("elevation_speed")
        self.controller.setAzimuthSpeed(int(azimuthTextBox.get_text()))
        self.controller.setElevationSpeed(int(elevationTextBox.get_text()))

        widgetname = Gtk.Buildable.get_name(widget)
        if widgetname == 'demo_start':
            pauseInterval = int(self.builder.get_object(
                "demo_pause_interval").get_text())
            self.controller.demo_start(pauseInterval)
        elif widgetname == 'demo_first_quarter':
            self.controller.demo_first_quarter()
        elif widgetname == 'demo_second_quarter':
            self.controller.demo_second_quarter()
        elif widgetname == 'demo_third_quarter':
            self.controller.demo_third_quarter()
        elif widgetname == 'demo_fourth_quarter':
            self.controller.demo_fourth_quarter()

    def arrowPressed(self, widget, data=None):
        arrow = Gtk.Buildable.get_name(widget)
        distance = self.joggingDistance()
        joggingPWMfreqTextBox = self.builder.get_object("jogging_speed")
        joggingPWMFreq = joggingPWMfreqTextBox.get_text()
        self.controller.arrowPressed(arrow, distance, joggingPWMFreq)

    '''
    def move(self, widget, data=None, direction=None):
        print(widget)
        contstep = self.builder.get_object("contstep")
        if direction is None:
            direction = Gtk.Buildable.get_name(widget)
        if contstep.get_active():
            self.manager.moveForever(direction)
        else:
            distance = self.getTravelDistance()
            unit_step = self.builder.get_object("steps-radiobutton")
            if unit_step.get_active():
                units = "step"
            else:
                units = "mm"
            self.manager.move(distance, direction, units)
    '''

    def sunposition_calculate(self, widget, data=None):
        latitudeTextBox = self.builder.get_object("sunposition_latitude")
        longitudeTextBox = self.builder.get_object("sunposition_longitude")
        latitude = float(latitudeTextBox.get_text())
        longitude = float(longitudeTextBox.get_text())
        position = getFinalSolarPosition(latitude, longitude)
        azimuthLabel = self.builder.get_object("sunposition_azimuth")
        azimuthLabel.set_text(str(position['azimuth']))
        elevationLabel = self.builder.get_object("sunposition_elevation")
        elevationLabel.set_text(str(position['elevation']))

    def startTimer(self):
        GObject.timeout_add_seconds(1, self.updateGUI)

    def updateGUI(self):
        positionAzimuthLabel = self.builder.get_object("position_azimuth")
        positionElevationLabel = self.builder.get_object("position_elevation")
        positionElevation = self.position['elevation'] + 1
        self.position['elevation'] = positionElevation
        positionElevationLabel.set_text(str(positionElevation))
        return True


def app_main():
    builder = Gtk.Builder()
    builder.add_from_file("deathray.glade")

    window = builder.get_object("mainwindow")
    window.connect("destroy", Gtk.main_quit)
    window.show_all()

    def updateGUI():
        print("hello")

    def startTimer():
        GObject.timeout_add_seconds(1, updateGUI)
        sleep(2)

    # GObject.threads_init()

    handler = StepperControllerHandler(builder)
    builder.connect_signals(handler)
    thread = threading.Thread(target=handler.startTimer)
    thread.daemon = True
    thread.start()


if __name__ == '__main__':
    app_main()
    Gtk.main()
