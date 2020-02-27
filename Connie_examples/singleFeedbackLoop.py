# Before beginning, must execute:
# ssh root@rp-f06b95.local "nohup systemctl start redpitaya_scpi &"
#
# Acquires a (square) signal from in2, outputs from out1 to in1 lo/hi if receives 
# hi/lo. Then, outputs from out2 to in2 lo/hi if receives hi/lo.

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
rp.tx_txt('ACQ:BUF:SIZE?')
BUFF_SIZE = int(rp.rx_txt())

# ========= parameters =========
# inVoltThresh = 0.5 # IF SPLITTING INPUTS, NEED TO DIVIDE THRESH BY 2
inVoltThresh = 0.25

freq = 3000
outVoltLo = 0.4
outVoltHi = 0.8
dec = 8

trigVolt = outVoltLo-0.01
buffTime = decToTimeScale[dec]

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

# ========= set up out1 parameters =========
rp.tx_txt('SOUR1:FUNC SQUARE')
rp.tx_txt('SOUR1:FREQ:FIX ' + str(freq))
# SOUR2 VOLT SPECIFIED LATER ON AFTER DECISION
rp.tx_txt('SOUR1:BURS:NCYC 1') # num periods (CYCles) in burst
# rp.tx_txt('SOUR2:BURS:NOR 1') # num repeated bursts
rp.tx_txt('SOUR1:BURS:STAT ON') # turn on burst mode
rp.tx_txt('SOUR1:TRIG:SOUR EXT') #  start out1 burst based on in2

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
while True: # completes an entire cycle starting from AWG input
    rp.tx_txt('OUTPUT1:STATE OFF')
    rp.tx_txt('OUTPUT2:STATE OFF')

    # ========= trig from in2  =========
    rp.tx_txt('ACQ:TRIG CH2_PE') # positive edge of in2 (this also resets acq state)
    rp.tx_txt('ACQ:START') # need to wait after starting acq to clear buffer
    time.sleep(buffTime)
    print("Waiting for trigger.")
    trigStartTime = time.time()
    while True:
        rp.tx_txt('ACQ:TRIG:STAT?')
        if rp.rx_txt() == 'TD':
            trigAcqTime = time.time()
            break
    print("Triggered from in2 in %f sec" % (trigAcqTime-trigStartTime))
    # rp.tx_txt('ACQ:TRIG:LEV?') # returns what level was actually acquired at
    # print("level: " + rp.rx_txt())
    # rp.tx_txt('ACQ:TRIG:DLY?') # returns what dly was actually acquired at
    # print("delay: " + rp.rx_txt())
    
    
    # ========= decision for output1 =========
    rp.tx_txt('ACQ:SOUR2:DATA?') # take input data from in2
    buff_acq = rp.rx_txt()
    buff_acq = buff_acq.strip('{}\n\r').replace("  ", "").split(',')
    buff_acq = list(map(float, buff_acq))
    # print("len buff acq "+str(len(buff_acq)))

    # x = np.arange(buffTime, step=buffTime/BUFF_SIZE)
    # plt.plot(x, buff_acq, 'bo', markersize=0.1)
    # plt.show()
    
    voltIn = findSqHeight(buff_acq)
    print("Volt in: %f " % voltIn)
    if voltIn < inVoltThresh:
        voltOut = outVoltHi
        print("Sending hi (%.2fV) to out1" %outVoltHi)
    else:
        voltOut = outVoltLo
        print("Sending lo (%.2fV) to out1" %outVoltLo)
    rp.tx_txt('SOUR1:VOLT ' + str(voltOut))

    # time.sleep(5)

    # ========= trig from in1 =========
    rp.tx_txt('ACQ:TRIG CH1_PE') # positive edge of in1 (this also resets acq state)
    rp.tx_txt('ACQ:START') # need to wait after starting acq to clear buffer
    time.sleep(buffTime)

    rp.tx_txt('OUTPUT1:STATE ON')

    print("Waiting for trigger.")
    trigStartTime = time.time()
    while True:
        rp.tx_txt('ACQ:TRIG:STAT?')
        if rp.rx_txt() == 'TD':
            trigAcqTime = time.time()
            break
    print("Triggered from in1 in %f sec" % (trigAcqTime-trigStartTime))
    
    # ========= decision for output2 =========
    rp.tx_txt('ACQ:SOUR1:DATA?') # take input data from in1
    buff_acq = rp.rx_txt()
    buff_acq = buff_acq.strip('{}\n\r').replace("  ", "").split(',')
    buff_acq = list(map(float, buff_acq))
    
    voltIn = findSqHeight(buff_acq)
    print("Volt in: %f " % voltIn)
    if voltIn < inVoltThresh:
        voltOut = outVoltHi
        print("Sending hi (%.2fV) to out1" %outVoltHi)
    else:
        voltOut = outVoltLo
        print("Sending lo (%.2fV) to out1" %outVoltLo)
    rp.tx_txt('SOUR2:VOLT ' + str(voltOut))

    rp.tx_txt('OUTPUT2:STATE ON')

    # time.sleep(2)
    # rp.tx_txt('ACQ:TRIG:STAT?')
    # print(rp.rx_txt())
    print()

