import DDSMulti_Sequencer
import re
import sys

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
REDPITAYA_IP = getparmval(cmdstr, "RP_IP","192.168.1.100") #IF THE CALL TO DDS_SEQUENCER CONTAINS CMD LINE ARGUMENT "RP_IP=XXX.XXX.XXX.XXX" THAT IS USED INSTEAD OF THE DEFAULT AT RIGHT
SOFTWARETRIGGER = getparmval(cmdstr, "SOFTWARETRIGGER","1")

#the next line of code generates the data for each of the 10 simultaneous DDS outputs. The format, for each channel, is:
#[[f_initial in Hz, Amp_initial as fraction of max amplitude],[[time of end of first ramp, freq to ramp to, amplitude to ramp to],[time of end of second ramp, freq to ramp to, amplitude to ramp to],...]]
CHs_DATA=[[[(2*k)*10.0**6.0,0.05],[[4.0,(4*k)*10.0**6.0,0.05*(((k-4.5)**2)/25.0)],[8.0,(2*k)*10.0**6.0,0.05]]] for k in range(NUMCHANNELS)]

DDSMulti_Sequencer.SendDataToRP(REDPITAYA_IP, SOFTWARETRIGGER=="1", CHs_DATA)

