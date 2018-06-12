import json
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from solartrackercontroller import SolarTrackerController


class StepperControllerHandler(object):

    def __init__(self, builder):
        self.builder = builder
        self.controller = SolarTrackerController()
        config = self.load_data_from_config("config.json")
        self.config = config
        self.initialiseApp()

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
                "name": "demo_pause_interval",
                "key": "demo",
                "subkey": "pauseInterval"
            },
            {
                "name": "jogging_distance",
                "key": "jogging",
                "subkey": "distance"
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
            else:
                positioning_frame.set_visible(True)

    def stop(self, widget):
        moving = self.builder.get_object("moving_indicator")
        self.controller.stop()

    def joggingDistance(self):
        travelTextBox = self.builder.get_object("jogging_distance")
        return float(travelTextBox.get_text())

    def home_azimuth(self, widget, data=None):
        print("home azimuth")

    def home_elevation(self, widget, data=None):
        print("home elevation")

    def limit_azimuth(self, widget, data=None):
        print("limit azimuth")

    def limit_elevation(self, widget, data=None):
        print("limit elevation")

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
        self.controller.arrowPressed(arrow, distance)

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

if __name__ == '__main__':
    builder = Gtk.Builder()
    builder.add_from_file("demo.glade")

    window = builder.get_object("mainwindow")
    window.connect("destroy", Gtk.main_quit)

    handler = StepperControllerHandler(builder)
    builder.connect_signals(handler)

    window.show_all()
    Gtk.main()
