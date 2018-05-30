import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from steppercontrollermanager import StepperControllerManager


class StepperControllerHandler(object):

    def __init__(self, builder):
        self.builder = builder
        self.manager = StepperControllerManager()
        self.addMarksToSlider()
        # keycodes
        # https://gitlab.gnome.org/GNOME/gtk/raw/master/gdk/gdkkeysyms.h
        key, mods = Gtk.accelerator_parse('u')
        print(key, mods)
        accelgroup = self.builder.get_object("mainaccel")

        accelgroup.connect(
            key,
            mods,
            Gtk.AccelFlags.VISIBLE, self.up)
        #accelmap = Gtk.AccelMap.get()
        # accelmap.change_entry(
        #    "<Actions>/mainaccel/up",
        #    key,
        #    mods,
        #    True)
        # accelmap.save("accelmap.txt")

    def addMarksToSlider(self):
        slider = builder.get_object("slider")
        for mark in range(600, 3000, 100):
            slider.add_mark(mark, Gtk.PositionType.LEFT)

    def getTravelDistance(self):
        travelTextBox = self.builder.get_object("travel")
        return float(travelTextBox.get_text())

    def unitsChanged(self, widget, data=None):
        pass

    def up(self, a, b, c, d):
        print("up")

    def move(self, widget, data=None):
        contstep = self.builder.get_object("contstep")
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

    def stop(self, widget):
        print("stop!")

    def sliderMoved(self, widget, data=None):
        print(widget.get_value())

    def reset(self, widget):
        slider = self.builder.get_object("slider")
        slider.set_value(650)


if __name__ == '__main__':
    builder = Gtk.Builder()
    builder.add_from_file("steppercontroller.glade")

    window = builder.get_object("mainwindow")
    window.connect("destroy", Gtk.main_quit)

    handler = StepperControllerHandler(builder)
    builder.connect_signals(handler)

    window.show_all()
    Gtk.main()
