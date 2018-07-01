import threading
from time import sleep
from solartrackercontroller import SolarTrackerController


class StepperJobControl(threading.Thread):

    def __init__(self, receiveQueue, sendQueue):
        threading.Thread.__init__(self)
        self.receiveQueue = receiveQueue
        self.sendQueue = sendQueue
        self.controller = SolarTrackerController()

    def run(self):
        azimuth = 0
        elevation = 0
        print("StepperJobControl running...")
        while True:
            data = self.receiveQueue.get()
            command = data['command']
            if command == 'position':
                azimuth = data['azimuth']
                elevation = data['elevation']
            elif command == 'move':
                distance = data['distance']
                arrow = data['arrow']
                PWMfreq = data['PWMfreq']
                direction = 0
                stepper = ''

                if arrow == 'uparrow':
                    elevation = elevation - distance
                    direction = 0
                    stepper = 'elevation'

                elif arrow == 'downarrow':
                    elevation = elevation + distance
                    direction = 1
                    stepper = 'elevation'

                elif arrow == 'leftarrow':
                    azimuth = azimuth + distance
                    direction = 0
                    stepper = 'elevation'

                elif arrow == 'rightarrow':
                    azimuth = azimuth - distance
                    direction = 1
                    stepper = 'elevation'

                self.controller.move(stepper, distance, direction, PWMfreq)

                self.sendQueue.put({
                    'azimuth': azimuth,
                    'elevation': elevation
                })
            elif command == 'home':
                action = data['action']
                PWMfreq = data['PWMfreq']
                getattr(self.controller, action)(PWMfreq)

            elif command == 'stop':
                self.controller.stop()
