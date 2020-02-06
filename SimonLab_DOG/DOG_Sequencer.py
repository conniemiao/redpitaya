"""
Last modified 2/19/2017
Written by Jon
Send to RP
"""

import socket
import JSocket
from struct import pack, unpack
import math
from math import *

import parser
import sys
import re
import os
import numpy as np
import time

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def convert_2c(val, bits): #take a signed integer and return it in 2c form
    if (val>=0):
        return val
    return ((1 << bits)+val)
numbits=32

def convertsimple(val):
    return convert_2c(val,numbits)

def sendpitaya (addr, val):
    JSocket.write_msg(sock, addr,convert_2c(val,numbits))

def sendpitaya_long(addr, val): #addr is the address low word. addr+4*4 is where the high word goes!
                                #val is a float, that should be sent in 2c form!
    vali=int(val)
    val2c=convert_2c(val,64)
    val2cH=val2c>>32
    val2cL=val&(0xffffffff)
    JSocket.write_msg(sock, addr,val2cL)
    JSocket.write_msg(sock, addr+4,val2cH)

def sendpitaya_long_u(addr, val): #addr is the address low word. addr+4*4 is where the high word goes!
                                  #val is a unsigned
    vali=int(val)
    val2c=val
    val2cH=val2c>>32
    val2cL=val&(0xffffffff)
    JSocket.write_msg(sock, addr,val2cL)
    JSocket.write_msg(sock, addr+4,val2cH)
##########################################
def get_CSV_data(fileDirectory, columns):
    data = np.loadtxt(fileDirectory, delimiter=',', usecols=columns, unpack=True)
    return data
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

##########################################################################################################!!!!!
#ADDRESSES IN THE MEMORY MAPPED ADDRESS SPACE

DOGMAXSAMPLES               =  65536*2

LEDADDRESS              =0x40000030    #address in FPGA memory map to control RP LEDS

DOGnsamples_OFFSET          = 1076887552+4*2                  #number of samples
DOGawaittrigger_OFFSET      = 1076887552+4*24                 #offset in WORDS (4 bytes) to address where we write ANYTHING to tell system to reset and await trigger
DOGsoftwaretrigger_OFFSET   = 1076887552+4*25                 #offset in WORDS (4 bytes) to address where we write ANYTHING to give the system a software trigger!
DOGsamples_OFFSET            = 1076887552+4*30                #offset in WORDS (4 bytes) to the zeroeth sample

maxsendlen=31*512  #most FIR coefficients we can send at a time
fclk_Hz=125*(10**6) #redpitaya clock frequency


# def sendpitayaarray (addr, dats): #WRITE THE FIR COEFFICIENTS IN THE LARGEST BLOCKS POSSIBLE, TO SPEED THE WRITING
#     thelen=len(dats)
#     startind=0
#     endind=min(thelen,startind+maxsendlen-1)
#     while(startind<thelen):
#         JSocket.write_msg (sock,FIRCOEFFSADDRESSOFFSET,startind*4) #since we don't have enough address bits, this is an offset
#         JSocket.writeS_msg(sock, addr,dats[startind:endind])
#         startind=endind+1
#         endind=min(thelen-1,startind+maxsendlen)
        
# def HzToFTW ( freq_hz ): #take a frequency in Hz, and convert it to a RP FTW FLOAT, to minimize rounding error down the line! NO BITSHIFTS FOR NOW!
#     return freq_hz*(2.0**32)/fclk_Hz
# def SecToCycles ( t_sec ): #take a time in seconds and convert it to RP timesteps in cycles, without rounding, so we can do it later when we compute deltas!
#     return t_sec*fclk_Hz

def SendFullSeqs( AllSeqs ):
    #the data for each channel is an element of AllSeqs, sent as follows:
        #[[IFfreq_Hz,IFamp_frac],[[time_sec,freq_Hz,amp_frac]]]
    if (len(AllSeqs)>DOGMAXSAMPLES):
        print "TOO MANY SAMPLES FOR FPGA!"
        exit()
    JSocket.write_msg(sock, DOGnsamples_OFFSET,len(AllSeqs))#these must be sent as unsigned 32 bit numbers

    for sampIND in range(len(AllSeqs)):
        JSocket.write_msg(sock, DOGsamples_OFFSET+sampIND*4,AllSeqs[sampIND])#these must be sent as unsigned 32 bit numbers
        #print AllSeqs[sampIND]

    #reset the RP FSM and prepare it for a trigger!
    JSocket.write_msg(sock, DOGawaittrigger_OFFSET,0)#value sent doesn't affect anything
    
    if SWTrigger:  #if enabled, give it a software trigger!    
        JSocket.write_msg(sock, DOGsoftwaretrigger_OFFSET,0)#value sent doesn't affect anything



##############################################################################################
##############################################################################################
#####################################END OF SETUP CODE########################################

SWTrigger=True
DEBUGMODE=False
sock = 0

def SendDataToRP(REDPITAYA_IP, SOFTWARETRIGGER, CHs_DATA):

    global DEBUGMODE
    global sock
    global SWTrigger

    SWTrigger=SOFTWARETRIGGER
        
    DEBUGMODE=False #IF TRUE, THE DATA DOESN'T GET SENT TO THE RED PITAYA!
    
    if(DEBUGMODE==False):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (REDPITAYA_IP, 10000)
        print >>sys.stderr, 'connecting to %s port %s' % server_address
        sock.connect(server_address)
        #JSocket.write_msg(sock, LEDADDRESS, 0)               #DAC/ADC behave better with LEDS off! WEIRD!

    SendFullSeqs(CHs_DATA)

    if(DEBUGMODE==False):
        JSocket.write_done(sock)
        sock.close()
