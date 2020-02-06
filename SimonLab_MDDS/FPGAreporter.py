import time
import datetime
from time import sleep
import os;
from uuid import getnode as get_mac

if __name__ == '__main__':
        mac = get_mac()
        macstr=':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
        print "Started:"
        while True:
                os.system("curl simonlab.uchicago.edu:5000/data/MDDS_V1p0:"+macstr)
#                sleep(60.0*60.0) # Here the time delay can be tuned-- currently reports once per hour- YIKES!
                sleep(24*3600.0) # Here the time delay can be tuned-- currently reports once per day!
        print "Exit"