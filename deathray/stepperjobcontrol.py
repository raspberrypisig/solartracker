import threading
from time import sleep


class StepperJobControl(threading.Thread):

    def __init__(self, receiveQueue, sendQueue):
        threading.Thread.__init__(self)
        self.receiveQueue = receiveQueue
        self.sendQueue = sendQueue

    def run(self):
        azimuth = 0
        elevation = 0
        print("StepperJobControl running...")
        while True:
            data = self.receiveQueue.get()
            distance = data['distance']
            arrow = data['arrow']
            if arrow == 'uparrow':
                elevation = elevation - distance

            elif arrow == 'downarrow':
                elevation = elevation + distance

            elif arrow == 'leftarrow':
                azimuth = azimuth + distance

            elif arrow == 'rightarrow':
                azimuth = azimuth - distance

            self.sendQueue.put({
                'azimuth': azimuth,
                'elevation': elevation
            })
