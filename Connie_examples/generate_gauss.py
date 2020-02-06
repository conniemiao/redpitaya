# Before beginning, must execute:
# ssh root@rp-f06b95.local "nohup systemctl start redpitaya_scpi &"
import redpitaya_scpi as scpi
import sys
import math
from scipy.signal import gaussian
import matplotlib.pyplot as plt

rp = scpi.scpi('rp-f06b95.local')
rp.tx_txt('OUTPUT1:STATE OFF')
rp.tx_txt('GEN:RST')

rp.tx_txt('ACQ:BUF:SIZE?')
BUFF_SIZE = int(rp.rx_txt())

data = ''

gauss = gaussian(BUFF_SIZE, std = BUFF_SIZE/7)
for i in range(BUFF_SIZE-2):
    data += str(gauss[i]) + ', '
data += str(gauss[BUFF_SIZE-1])

freq = 3000
ampl = 0.5
rp.tx_txt('SOUR1:FREQ:FIX ' + str(freq))
rp.tx_txt('SOUR1:VOLT ' + str(ampl))

rp.tx_txt('SOUR1:FUNC ARBITRARY')
rp.tx_txt('SOUR1:TRAC:DATA:DATA ' + data)

rp.tx_txt('OUTPUT1:STATE ON')

rp.tx_txt('SOUR1:TRAC:DATA:DATA?')
buff_str = rp.rx_txt()
buff_str = buff_str.strip('{}\n\r').replace("  ", "").split(',')
buff = list(map(float, buff_str))
plt.plot(buff)
plt.show()

