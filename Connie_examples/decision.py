# Before beginning, must execute:
# ssh root@rp-f06b95.local "nohup systemctl start redpitaya_scpi &"

# Acquires a (square) signal from in1, averages over height. Outputs from out2
# square pulse of height 0.25V if in1 was >0.5V, or a square pulse of height
# 0.75V if in1 was <0.5V.

import redpitaya_scpi as scpi
import sys
import math
from scipy.signal import gaussian
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import time

rp = scpi.scpi('rp-f06b95.local')

# ======================================================
# Assuming buff contains the heights for a square wave,
# determine where the square wave is and average over it,
# return the height.
def findSqHeight(buff):
    sumHeight = 0
    avgCounter = 0
    for i in range(1,len(buff)):
        # dy = buff[i] - buff[i-1]
        # if dy < -0.01*buff[i]: break # downward slope
        # if dy < 0.01*buff[i] and buff[i]>0.0001:
        if buff[i]>0.0001:
            sumHeight += buff[i]
            avgCounter += 1
    return sumHeight/avgCounter

# ======================================================

# in secs
decToTimeScale = {1:131.072E-6,
        8:1.049E-3,
        64:8.389E-3,
        1024:134.218E-3,
        8192:1.074,
        65536:8.590}

# ========= parameters =========
# inVoltThresh = 0.5 # IF SPLITTING INPUTS, NEED TO DIVIDE THRESH BY 2
inVoltThresh = 0.25
trigVolt = 0.01

freq = 10000
outVoltLo = 0.25
outVoltHi = 0.75
dec = 8

startPgmTime = time.time()

rp.tx_txt('OUTPUT1:STATE OFF')
rp.tx_txt('OUTPUT2:STATE OFF')
rp.tx_txt('GEN:RST')
rp.tx_txt('ACQ:RST')

# ========= set up acquisition trigger =========
rp.tx_txt('ACQ:DEC ' + str(dec))
rp.tx_txt('ACQ:TRIG:LEV ' + str(trigVolt)) # centers point where voltage = level
rp.tx_txt('ACQ:TRIG:DLY 0') # number of samples delayed from center (max = 16384)
# rp.tx_txt('ACQ:AVG ON')
rp.tx_txt('ACQ:TRIG CH1_NE') # negative edge of input 1

# ========= set up out2 parameters =========
rp.tx_txt('SOUR2:FUNC SQUARE')
rp.tx_txt('SOUR2:FREQ:FIX ' + str(freq))
# SOUR2 VOLT SPECIFIED LATER ON AFTER DECISION
rp.tx_txt('SOUR2:BURS:NCYC 1') # num periods (CYCles) in burst
# rp.tx_txt('SOUR2:BURS:NOR 1') # num repeated bursts
rp.tx_txt('SOUR2:BURS:STAT ON') # turn on burst mode
rp.tx_txt('SOUR2:TRIG:SOUR EXT') #  start out2 burst based on in1

finishSetupTime = time.time()
print("Setup time: %f sec" % (finishSetupTime-startPgmTime))

# ========= acquire =========
rp.tx_txt('ACQ:START') # need to wait 1 sec after starting acq to clear buffer
time.sleep(1)

print("Waiting for trigger.")
trigStartTime = time.time()
while True: # wait up to 5 sec for buffer to fill
    rp.tx_txt('ACQ:TRIG:STAT?')
    if rp.rx_txt() == 'TD':
        trigAcqTime = time.time()
        break
#     if time.time()-trigStartTime > 5:
#         print("Failed to trigger, exiting.")
#         exit(0)
print("Triggered in %f sec" % (trigAcqTime-trigStartTime))
# rp.tx_txt('ACQ:TRIG:LEV?') # returns what level was actually acquired at
# print("level: " + rp.rx_txt())
# rp.tx_txt('ACQ:TRIG:DLY?') # returns what dly was actually acquired at
# print("delay: " + rp.rx_txt())


# ========= make decision and output =========
rp.tx_txt('ACQ:SOUR1:DATA?')
buff_acq = rp.rx_txt()
buff_acq = buff_acq.strip('{}\n\r').replace("  ", "").split(',')
buff_acq = list(map(float, buff_acq))
# print("len buff acq "+str(len(buff_acq)))

voltIn = findSqHeight(buff_acq)
print("Volt in: %f " % voltIn)
if voltIn < inVoltThresh:
    voltOut = outVoltHi
    print("Sending hi (0.75V)")
else:
    voltOut = outVoltLo
    print("Sending lo (0.25V)")
rp.tx_txt('SOUR2:VOLT ' + str(voltOut))
rp.tx_txt('OUTPUT2:STATE ON')

# time.sleep(2)
# rp.tx_txt('OUTPUT2:STATE OFF')

