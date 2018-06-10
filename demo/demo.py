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
        print(config)
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
        print([self.builder.get_object(i['name']).set_text(
            str(self.config[i['key']][i['subkey']])) for i in data])
        '''
        azimuth_speed = self.builder.get_object("azimuth_speed")
        elevation_speed = self.builder.get_object("elevation_speed")
        azimuth_speed.set_text(str(self.config["speed"]["azimuth"]))
        elevation_speed.set_text(str(self.config["speed"]["elevation"]))
        '''

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

    def arrowPressed(self, widget, data=None):
        arrow = Gtk.Buildable.get_name(widget)
        distance = self.joggingDistance()
        self.controller.arrowPressed(arrow, distance)

    def statusClicked(self, widget, data=None):
        # widget.set_active(False)
        widget.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("green"))
        widget.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse("blue"))
        widget.modify_base(Gtk.StateFlags.NORMAL, Gdk.color_parse("red"))
        return True

    def enterPressed(self, widget, data):
        if data.keyval == self.enterKey:
            print("enter pressed")
            grid = self.builder.get_object("slider")
            grid.grab_focus()
            widget.grab_remove()
        return False

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

    def contstep_toggled(self, widget):
        box = self.builder.get_object("manualmovement")
        if widget.get_active():
            widget.get_image().set_from_file("greencircle.png")
            box.set_sensitive(False)
        else:
            widget.get_image().set_from_file("redcircle.png")
            box.set_sensitive(True)

    def sliderMoved(self, widget, data=None):
        print(widget.get_value())

    def reset(self, widget):
        slider = self.builder.get_object("slider")
        slider.set_value(650)

    def keyPressed(self, widget, event):
        if event.keyval in self.arrowKeys:
            # print(Gtk.Buildable.get_name(widget))
            # print(event.keyval)
            self.arrowPressed(event.keyval)
            return True
        return False


if __name__ == '__main__':
    builder = Gtk.Builder()
    builder.add_from_file("demo.glade")

    window = builder.get_object("mainwindow")
    window.connect("destroy", Gtk.main_quit)

    handler = StepperControllerHandler(builder)
    builder.connect_signals(handler)

    window.show_all()
    Gtk.main()
