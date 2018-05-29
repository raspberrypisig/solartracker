import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from steppercontrollermanager import StepperControllerManager


class StepperControllerHandler(object):

    def __init__(self, builder):
        self.builder = builder
        self.manager = StepperControllerManager()

    def getTravelDistance(self):
        travelTextBox = self.builder.get_object("travel")
        return float(travelTextBox.get_text())

    def unitsChanged(self, widget, data=None):
        pass

    def move(self, widget, data=None):
        distance = self.getTravelDistance()
        direction = Gtk.Buildable.get_name(widget)
        unit_step = self.builder.get_object("steps-radiobutton")
        if unit_step.get_active():
            units = "step"
        else:
            units = "mm"
        self.manager.move(distance, direction, units)


if __name__ == '__main__':
    builder = Gtk.Builder()
    builder.add_from_file("steppercontroller.glade")

    window = builder.get_object("mainwindow")
    window.connect("destroy", Gtk.main_quit)

    handler = StepperControllerHandler(builder)
    builder.connect_signals(handler)

    window.show_all()
    Gtk.main()
