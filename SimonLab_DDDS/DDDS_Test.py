import DDS_Sequencer
import re
import sys
from math import sin

NUMCHANNELS=10 #hard-coded into the VERILOG. CANNOT BE CHANGED FOR NOW

############################################# HELPER FUNCTIONS #############################################
def getparmval(strIn,parmname,defaultval):
    strlist=re.findall(parmname+"=([\w\a\.-]*)",strIn)
    if(len(strlist)>0):
        outval=strlist[0]
    else:
        outval=defaultval
    print parmname+": "+outval
    return outval


############################################# MAIN ROUTINE #################################################
cmdstr=""
for tARG in sys.argv:
    cmdstr=cmdstr+" "+tARG
REDPITAYA_IP = getparmval(cmdstr, "RP_IP","192.168.0.42") #IF THE CALL TO DDS_SEQUENCER CONTAINS CMD LINE ARGUMENT "RP_IP=XXX.XXX.XXX.XXX" THAT IS USED INSTEAD OF THE DEFAULT AT LEFT
SOFTWARETRIGGER = getparmval(cmdstr, "SOFTWARETRIGGER","1")

sinesweep=[[0.02*float(kk),(10**6.0)*(3.0+0.5*sin(20.*kk*0.02))] for kk in range(64)]

#CH1_DATA=[(3.005)*10.0**6.,sinesweep]

CH1_DATA=[30.0*10**6,[[0.1,30.0*10**6],[3.0, 1.0*10**6]]]
CH2_DATA=[1.0 *10**6,[[0.1, 1.0*10**6],[3.0,30.0*10**6]]]

DDS_Sequencer.SendDataToRP(REDPITAYA_IP,SOFTWARETRIGGER=="1",CH1_DATA,CH2_DATA)