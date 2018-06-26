import pigpio


class StepperWaveTransmission(object):
    MICROSECONDS = 1000000

    def __init__(self, pi, stepPin, PWMfreq):
        self.pi = pi
        self.stepPin = stepPin
        self.PWMfreq = PWMfreq
        dutyCycle = 0.5

        timeperiodInMicroseconds = StepperWaveTransmission.MICROSECONDS / PWMfreq
        self.pulseOnTime = int(timeperiodInMicroseconds * dutyCycle)
        self.pulseOffTime = timeperiodInMicroseconds - self.pulseOnTime

        self.wf = []
        self.wid = -1
        self.waiting = []

    def clear_wave(self):
        self.wf = []
        if self.wid >= 0:
            self.pi.wave_delete(self.wid)
            self.wid = -1

    def create_wave(self):
        if len(self.wf) > 0:
            pulses = self.pi.wave_add_generic(self.wf)
            self.wid = self.pi.wave_create()

    def send_wave(self):
        if self.wid >= 0 and self.wid != 9999:
            self.pi.wave_send_using_mode(
                self.wid, pigpio.WAVE_MODE_ONE_SHOT_SYNC)

    def add_wave(self, steps):
        self.wf = [pigpio.pulse(0, 0, self.pi.wave_get_micros())]

        for x in range(steps):
            self.wf.append(
                pigpio.pulse(
                    1 << self.stepPin,
                    0,
                    self.pulseOnTime))
            self.wf.append(
                pigpio.pulse(
                    0,
                    1 << self.stepPin,
                    self.pulseOffTime))

    def _next_wave(self):
        if len(self.waiting):  # waves ready to be sent
            at = pi.wave_tx_at()
            if (at == 9999) or (at == self.wid):
                if self.previous is not None:
                    pi.wave_delete(self.previous)

                self.previous = self.wid
                self.pi.wave_add_generic(self.waiting.pop(0))
                self.wid = pi.wave_create()
                self.pi.wave_send_using_mode(
                    self.wid, pigpio.WAVE_MODE_ONE_SHOT_SYNC)

                print(at, self.previous, self.wid, len(self.waiting),
                      time.time() - self.t)

if __name__ == '__main__':
    pi = pigpio.pi()
    tx = StepperWaveTransmission(pi, stepPin=17, PWMfreq=650)
    tx.clear_wave()
    tx.add_wave(steps=200)
    tx.create_wave()
    tx.send_wave()
    tx.clear_wave()
    pi.stop()
