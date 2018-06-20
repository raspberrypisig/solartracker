#!/usr/bin/env python

import time
import pigpio

def tx_pulses(pi, GPIO, hertz, num, pulse_len=1):
   assert hertz < 500000
   length_us = int(1000000/hertz)
   assert int(pulse_len) < length_us
   assert num < 65536

   num_low = num % 256
   num_high = num // 256

   wf = []

   
   #Mohan
   pulse_length = length_us/2
   
   wf.append(pigpio.pulse(1<<GPIO, 0, pulse_len))
   wf.append(pigpio.pulse(0, 1<<GPIO, length_us - pulse_len))

   pi.wave_add_generic(wf)

   wid = pi.wave_create()

   if wid >= 0:
      pi.wave_chain([255, 0, wid, 255, 1, num_low, num_high])
      while pi.wave_tx_busy():
         time.sleep(0.01)
      pi.wave_delete(wid)

pi = pigpio.pi()
if not pi.connected:
   exit()

GPIO=19

pi.set_mode(GPIO, pigpio.OUTPUT)

#tx_pulses(pi, GPIO, 100, 25) # 25 pulses @ 100 Hz

#tx_pulses(pi, GPIO, 1000, 250) # 250 pulses @ 1000 Hz

#tx_pulses(pi, GPIO, 5000, 2391, pulse_len=50) # 2391 pulses @ 5000 Hz

tx_pulses(pi, GPIO, 650 ,200) # 200 steps at 650Hz
 
pi.stop()
