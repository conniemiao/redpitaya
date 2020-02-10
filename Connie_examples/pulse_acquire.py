# Before beginning, must execute:
# ssh root@rp-f06b95.local "nohup systemctl start redpitaya_scpi &"
# Send a guassian pulse from out1, acquire the pulse from in1, plot both
import redpitaya_scpi as scpi
import sys
import math
from scipy.signal import gaussian
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import time

rp = scpi.scpi('rp-f06b95.local')

# in secs
decToTimeScale = {1:131.072E-6,
        8:1.049E-3,
        64:8.389E-3,
        1024:134.218E-3,
        8192:1.074,
        65536:8.590}

# ========= parameters =========
gaussAmpl = 0.5
freq = 3000
volt = 0.5 
dec = 8
totalAmpl = gaussAmpl*volt

# ========= pulse =========
rp.tx_txt('OUTPUT1:STATE OFF')
rp.tx_txt('GEN:RST')
rp.tx_txt('ACQ:RST')
rp.tx_txt('ACQ:BUF:SIZE?')
BUFF_SIZE = int(rp.rx_txt())
data = ''
gauss = gaussAmpl*gaussian(BUFF_SIZE, std = BUFF_SIZE/7)
for i in range(BUFF_SIZE-1):
    data += str(gauss[i]) + ', '
data += str(gauss[BUFF_SIZE-1])
rp.tx_txt('SOUR1:FREQ:FIX ' + str(freq))
rp.tx_txt('SOUR1:VOLT ' + str(volt))
rp.tx_txt('SOUR1:FUNC ARBITRARY')
rp.tx_txt('SOUR1:TRAC:DATA:DATA ' + data)
rp.tx_txt('SOUR1:TRAC:DATA:DATA?')
buff_sent = rp.rx_txt()
buff_sent = buff_sent.strip('{}\n\r').replace("  ", "").split(',')
buff_sent = list(map(float, buff_sent))
print("len buff sent "+str(len(buff_sent)))
rp.tx_txt('SOUR1:BURS:STAT ON')
rp.tx_txt('SOUR1:BURS:NCYC 1')
rp.tx_txt('OUTPUT1:STATE ON')

# ========= acquire =========
rp.tx_txt('ACQ:DEC ' + str(dec))
rp.tx_txt('ACQ:TRIG:LEV ' + str(totalAmpl)) # centers point where voltage = level
rp.tx_txt('ACQ:TRIG:DLY 0') # number of samples delayed from center (max = 16384)
# rp.tx_txt('ACQ:AVG ON')
rp.tx_txt('ACQ:START')
time.sleep(1)
# ========= trigger =========
rp.tx_txt('ACQ:TRIG CH1_PE') # positive edge of input 1
rp.tx_txt('SOUR1:TRIG:IMM') #  start source 1 burst
while True:
    rp.tx_txt('ACQ:TRIG:STAT?')
    if rp.rx_txt() == 'TD': break

rp.tx_txt('ACQ:TRIG:LEV?')
print("level: " + rp.rx_txt())
rp.tx_txt('ACQ:TRIG:DLY?')
print("delay: " + rp.rx_txt())

# ========= plot =========
rp.tx_txt('ACQ:SOUR1:DATA?')
buff_acq = rp.rx_txt()
buff_acq = buff_acq.strip('{}\n\r').replace("  ", "").split(',')
buff_acq = list(map(float, buff_acq))
print("len buff acq "+str(len(buff_acq)))

buffTime = decToTimeScale[dec]
numPeriodsInBuf = freq*buffTime
print("num periods in buffer %i" % numPeriodsInBuf)
x = np.arange(buffTime, step=buffTime/BUFF_SIZE)
plt.plot(x, totalAmpl*gaussian(BUFF_SIZE, std = BUFF_SIZE/(7*numPeriodsInBuf)))
plt.plot(x, buff_acq, marker='o', markersize=0.1)

plt.ylabel('Voltage (V)')
plt.xlabel('Time (s)')
plt.gca().xaxis.set_major_formatter(mtick.FormatStrFormatter('%.0e')) # gca=get current axis
plt.show()
