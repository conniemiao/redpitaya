"""
Last modified 3/23/2016
Written by Jon
Send to RP
"""

from struct import pack, unpack
import math
from math import *
import parser
import sys
import re
import os
import numpy as np
import time
import JSocket
import socket

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

if len(sys.argv)<2:
    print ""
    print ""
    print ""
    print bcolors.OKBLUE + "proper usage: " + bcolors.ENDC + "python SendFIR.py FIR_coeffs=THE_FILE_NAME_HERE RP_IP=RP.IP.ADDRESS.HERE OutputShift=SHIFTBITS FIR_prescale=ScaleFact"
    print bcolors.OKBLUE + "example:      " + bcolors.ENDC + "python SendFIR.py FIR_coeffs=FIRcoeffs.csv RP_IP=192.168.0.1 OutputShift=12 FIR_prescale=22400"
    print ""
    print bcolors.HEADER + bcolors.BOLD + "----------PARAMETER DESCRIPTIONS----------" + bcolors.ENDC
    print bcolors.FAIL + "FIR_coeffs (DEFAULT: FIRcoeffs.csv)" + bcolors.ENDC + "-- the csv file containing the time series of FIR coefficients, on an (assumed) 4.1uS clock. Coefficients are stored as 18-bit fixed pt #s."
    print ""
    print bcolors.FAIL + "RP_IP (DEFAULT: 192.168.0.100)" + bcolors.ENDC + "     -- the IP address of the Red Pitaya Board. This may be ascertained using discovery.redpitaya.com and entering the board's MAC address, or through your router settings."
    print ""
    print bcolors.FAIL + "OutputShift (DEFAULT: 12)" + bcolors.ENDC + "          -- the number of bits to right-shift the FIR final output before sending it to the 14-bit DAC (intermediate computations are 50-bits)"
    print ""
    print bcolors.FAIL + "FIR_prescale (DEFAULT: 12345)" + bcolors.ENDC + "        -- a prescalar applied to the FIR coefficients in FIR_coeff, employed to make optimal use of the 18bit storage of the coefficients."
    print ""
    print bcolors.HEADER + bcolors.BOLD + "========GUIDANCE ON PROPER VALUES=========" + bcolors.ENDC
    print "FIRcoeffs and FIR_prescale should work together to ensure that the 'maximum value' output is near, but less than or equal to, 2^17-1=131071; this maximizes the dynamic range of the FILTER on the FPGA"
    print ""
    print "OutputShift should be chosen to ensure that for the maximum ADC input (which is ~+/-1V), we achieve the maximum DAC output-- this is of course freq. dependent, so for lockboxes I suggest this at DC/low freq."
    print ""
    print "This sets the total Red Pitaya gain at DC to near unity-- the signal should be conditioned (amplifier and anti-aliasing filter @ ~125kHz) before the RP to fill the full input range, and then post-filtered (amplitude, and LPF) to get size right again!"
    print ""
    print ""
    print ""
    exit()


def convert_2c(val, bits): #take a signed integer and return it in 2c form
    if (val>=0):
        return val
    return ((1 << bits)+val)

numbits=32


def convertsimple(val):
    return convert_2c(val,numbits)


def sendpitaya (addr, val):
    JSocket.write_msg(sock, addr,convert_2c(val,numbits))

##########################################

def get_CSV_data(fileDirectory, columns):
    data = np.loadtxt(fileDirectory, delimiter=',', usecols=columns, unpack=True)
    return data


#This is the file that contains the time coefficients of the impulse response function, in ~2.5us steps!

def getparmval(strIn,parmname,defaultval):
    strlist=re.findall(parmname+"=([\w\a\.-]*)",strIn)
    if(len(strlist)>0):
        outval=strlist[0]
    else:
        outval=defaultval
    print parmname+": "+outval
    return outval

def getparmval_int(strIn,parmname,defaultval):
    strlist=re.findall(parmname+"=([\w\a\.-]*)",strIn)
    if(len(strlist)>0):
        outval=int(strlist[0])
    else:
        outval=int(defaultval)
    print parmname+": "+str(outval)
    return outval
        
cmdstr=""
for tARG in sys.argv:
    cmdstr=cmdstr+" "+tARG

#Extract Control Parameters    
REDPITAYA_IP = getparmval(cmdstr, "RP_IP","192.168.0.100")
theshift = getparmval_int(cmdstr, "Outputshift","12")
theprefactor = getparmval_int(cmdstr, "FIR_prescale","12345")
filePath = getparmval(cmdstr, "FIR_coeffs","FIRcoeffs.csv")


coefficients = get_CSV_data(filePath,[0])


##########################################################################################################!!!!!


#ADDRESSES IN THE MEMORY MAPPED ADDRESS SPACE
LEDADDRESS              =0x40000030    #address in FPGA memory map to control RP LEDS
OUTPUTBITSHIFTADDRESS   =0x40300000    #address in FPGA memory map to control outputbitshift
FIRCOEFFSADDRESS        =1076887552+4*(32) #address in memory map where the FIR coefficients start
FIRCOEFFSADDRESSOFFSET  =1076887552+4*(4)  #address in memory map where the FIR coefficient offset lives, since we have too many coeffs for the memory map!
VNAftwADDRESS           = 1076887552+4*(8)         ;#address of the VNA frequency tuning word
VNAampOUTADDRESS        = 1076887552+4*(12)        ;#address of the VNA amplitude, which is the number of bits to shift the sine-wave to the right before outputting it! larger value means smaller amplitude!


maxsendlen=31*512  #most FIR coefficients we can send at a time


def sendpitayaarray (addr, dats): #WRITE THE FIR COEFFICIENTS IN THE LARGEST BLOCKS POSSIBLE, TO SPEED THE WRITING

    thelen=len(dats)
    startind=0
    endind=min(thelen,startind+maxsendlen-1)
    while(startind<thelen):
        JSocket.write_msg (sock,FIRCOEFFSADDRESSOFFSET,startind*4) #since we don't have enough address bits, this is an offset
        JSocket.writeS_msg(sock, addr,dats[startind:endind])
        startind=endind+1
        endind=min(thelen-1,startind+maxsendlen)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect the socket to the port where the server is listening
server_address = (REDPITAYA_IP, 10000)
print >>sys.stderr, 'connecting to %s port %s' % server_address
sock.connect(server_address)


JSocket.write_msg(sock, LEDADDRESS, 0)               #DAC/ADC behave better with LEDS off! WEIRD!
sendpitaya(OUTPUTBITSHIFTADDRESS,theshift)   #right-shift by 15 bits before outputting result!


nels=512   #this is the number of elements per ram
nrams=60   #and this is the number of rams!

thearray=[];
maxval=0.
numarray=[]

for x in range (nrams*nels): #first we build up the array
    theval=int(round(theprefactor*coefficients[x]))
    maxval=max(maxval,abs(theval))
    thearray.append(convertsimple(theval))
    numarray.append(theval)

sendpitayaarray(FIRCOEFFSADDRESS,thearray)
JSocket.write_msg(sock, VNAftwADDRESS, 0)
sendpitaya(VNAampOUTADDRESS, -10) #more bits than DAC

print "maximum value: ",maxval, "\n"
JSocket.write_done(sock)
sock.close()
