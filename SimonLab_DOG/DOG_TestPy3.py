import DOG_SequencerPy3
import re
import sys
from random import randint
import math

############################################# HELPER FUNCTIONS #############################################
def getparmval(strIn,parmname,defaultval):
    strlist=re.findall(parmname+"=([\w\a\.-]*)",strIn)
    if(len(strlist)>0):
        outval=strlist[0]
    else:
        outval=defaultval
    print(parmname+": "+outval)
    return outval

def thue_morse_digits(digits): #FOR FUN NOT NECESSARY
    return  [bin(n).count('1') % 2 for n in range(digits)]

def funseq(digits):
    return [math.floor(math.log(j+1))%2 for j in range(digits)]

def funseq2(digits):
    return [math.floor(math.sqrt(j)*2)%512 for j in range(digits)]

############################################# MAIN ROUTINE #################################################
cmdstr=""
for tARG in sys.argv:
    cmdstr=cmdstr+" "+tARG
REDPITAYA_IP = getparmval(cmdstr, "RP_IP","192.168.1.100") #IF THE CALL TO DDS_SEQUENCER CONTAINS CMD LINE ARGUMENT "RP_IP=XXX.XXX.XXX.XXX" THAT IS USED INSTEAD OF THE DEFAULT AT RIGHT
SOFTWARETRIGGER = getparmval(cmdstr, "SOFTWARETRIGGER","1")

#the next line of code generates the data for each of the 10 simultaneous DDS outputs. The format, for each channel, is:
#[[f_initial in Hz, Amp_initial as fraction of max amplitude],[[time of end of first ramp, freq to ramp to, amplitude to ramp to],[time of end of second ramp, freq to ramp to, amplitude to ramp to],...]]
numevents=12000
#CHs_DATA=[randint(0,255) for j in range(numevents)]
#CHs_DATA=[randint(0,255) for j in range(numevents)]
CHs_DATA= funseq2(numevents)
#CHs_DATA=[255 if j==10 else 0 for j in range(numevents)]
#CHs_DATA=[0 for j in range(numevents)]
#CHs_DATA=[255 for j in range(numevents)]


DOG_Sequencer.SendDataToRP(REDPITAYA_IP, SOFTWARETRIGGER=="1", CHs_DATA)

