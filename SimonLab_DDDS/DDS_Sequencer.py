"""
Last modified 3/23/2016
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

LEDADDRESS              =0x40000030    #address in FPGA memory map to control RP LEDS

maxevents=64
#DDS addresses (for writing)
DDSftw_IF_A_OFFSET      = 1076887552+4*(8)         #address in memory map for the initial/final FTW for the A channel
DDSftw_IF_B_OFFSET      = 1076887552+4*(12)        #address in memory map for the initial/final FTW for the B channel

DDSsamplesA_OFFSET          = 1076887552+4*(16)        #address in memory map for # of A samples
DDSsamplesB_OFFSET          = 1076887552+4*(20)        #address in memory map for # of B samples

DDSawaittrigger_OFFSET      = 1076887552+4*(24)        #address in memory map where we write ANYTHING to tell system to reset and await trigger

DDSsoftwaretrigger_OFFSET   = 1076887552+4*(36)        #address in memory map where we write ANYTHING to give the system a software trigger!

#EXPECT LOW WORD AT LOWER MEMORY ADDRESS FOR FREQS (FTW) RAMS!
DDSfreqsA_OFFSET            = 1076887552+4*(80)                                #address in memory map for the first element of the A freq list
DDSfreqsB_OFFSET            = DDSfreqsA_OFFSET+4*( 4*maxevents*2) #address in memory map for the first element of the B freq list
DDScyclesA_OFFSET           = DDSfreqsB_OFFSET+4*(  4*maxevents*2) #address in memory map for the first element of the A cyc. list
DDScyclesB_OFFSET           = DDScyclesA_OFFSET+4*( 4*maxevents*1) #address in memory map for the first element of the B cyc. list
DDScyclesBlast_OFFSET       = DDScyclesB_OFFSET+4*( 4*maxevents*1) #address in memory map for the last  element of the B cyc. list

maxsendlen=31*512  #most FIR coefficients we can send at a time
fclk_Hz=125*(10**6) #redpitaya clock frequency

def sendpitayaarray (addr, dats): #WRITE THE FIR COEFFICIENTS IN THE LARGEST BLOCKS POSSIBLE, TO SPEED THE WRITING
    thelen=len(dats)
    startind=0
    endind=min(thelen,startind+maxsendlen-1)
    while(startind<thelen):
        JSocket.write_msg (sock,FIRCOEFFSADDRESSOFFSET,startind*4) #since we don't have enough address bits, this is an offset
        JSocket.writeS_msg(sock, addr,dats[startind:endind])
        startind=endind+1
        endind=min(thelen-1,startind+maxsendlen)

def HzToFTW ( freq_hz ): #take a frequency in Hz, and convert it to a RP FTW FLOAT, to minimize rounding error down the line! NO BITSHIFTS FOR NOW!
    return freq_hz*(2.0**32)/fclk_Hz
def SecToCycles ( t_sec ): #take a time in seconds and convert it to RP timesteps in cycles, without rounding, so we can do it later when we compute deltas!
    return t_sec*fclk_Hz

def sendsequence (IFfreqA_hz,IFfreqB_hz, timesA_sec, freqsA_hz, timesB_sec,freqsB_hz): #convert freqs and times to FTW/dFTWs, and cycles, and send to RP!
    if (len(timesA_sec)>maxevents):
        print bcolors.FAIL + "TOO MANY EDGES ON CHANNEL A-- EXCEEDS RED PITAYA RAM SPACE OF " + str(maxevents) + bcolors.ENDC
        exit()
    if (len(timesB_sec)>maxevents):
        print bcolors.FAIL + "TOO MANY EDGES ON CHANNEL B-- EXCEEDS RED PITAYA RAM SPACE OF " + str(maxevents) + bcolors.ENDC
        exit()    

    #compute Freqs in Hz to FTWs
    IF_A_FTW=HzToFTW(IFfreqA_hz)
    IF_B_FTW=HzToFTW(IFfreqB_hz)
    
    freqsA_FTW=map(HzToFTW,freqsA_hz)
    freqsB_FTW=map(HzToFTW,freqsB_hz)
    #print freqsA_hz
    #print freqsA_FTW
    #================================================#
    #compute freq deltas as FTWs
    deltasA_FTW=[(freqsA_FTW[i+1]-freqsA_FTW[i]) for i in range(len(timesA_sec)-1)]
    deltasB_FTW=[(freqsB_FTW[i+1]-freqsB_FTW[i]) for i in range(len(timesB_sec)-1)]
    #prepend the first one!
    deltasA_FTW.insert(0,freqsA_FTW[0]-IF_A_FTW)
    deltasB_FTW.insert(0,freqsB_FTW[0]-IF_B_FTW)
    #================================================#
    #================================================#    
    #compute ramp start/end times in cycles    
    timesA_cyc=map(SecToCycles,timesA_sec)
    timesB_cyc=map(SecToCycles,timesB_sec)
    
    #compute ramp times in cycles-- round to integers, and have each ramp be at least one cycle!
    dtA_cyc=[max(1,int(round(timesA_cyc[i+1]-timesA_cyc[i]))) for i in range(len(timesA_sec)-1)]
    dtB_cyc=[max(1,int(round(timesB_cyc[i+1]-timesB_cyc[i]))) for i in range(len(timesB_sec)-1)]
    
    #prepend the first one!
    dtA_cyc.insert(0,max(1,int(round(timesA_cyc[0]))))
    dtB_cyc.insert(0,max(1,int(round(timesB_cyc[0]))))
    #================================================#
    #================================================#

    #compute step sizes for each ramp!
    dfA_FTW=[int(round((2.0**32)*deltasA_FTW[i]/dtA_cyc[i])) for i in range(len(dtA_cyc))]
    dfB_FTW=[int(round((2.0**32)*deltasB_FTW[i]/dtB_cyc[i])) for i in range(len(dtB_cyc))]
    #================================================#
    #================================================#

    print dtA_cyc
    print dfA_FTW
    
    if(DEBUGMODE==False):
        print "Length of dtA_cyc: " + str(len(dtA_cyc))
        print "Length of dBA_cyc: " + str(len(dtB_cyc))
        print "Length of dfA_FTW: " + str(len(dfA_FTW))
        print "Length of dfB_FTW: " + str(len(dfB_FTW))
        
        #send the number of samples on each channel
        JSocket.write_msg(sock,DDSsamplesA_OFFSET,len(timesA_sec))
        JSocket.write_msg(sock,DDSsamplesB_OFFSET,len(timesB_sec))

        #send step sizes for each ramp!
        for i in range(len(dtA_cyc)): #data must be sent as dftw, and corresponding cycles, as the latter is when all are written into the memory!
            sendpitaya_long(DDSfreqsA_OFFSET+8*i,dfA_FTW[i]) #these must be sent as 2's complement 64 bit numbers
            JSocket.write_msg(sock,DDScyclesA_OFFSET+4*i,dtA_cyc[i]) #these must be sent as unsigned 32 bit numbers
        for i in range(len(dtB_cyc)):
            sendpitaya_long(DDSfreqsB_OFFSET+8*i,dfB_FTW[i]) #these must be sent as 2's complement 64 bit numbers
            JSocket.write_msg(sock,DDScyclesB_OFFSET+4*i,dtB_cyc[i]) #these must be sent as unsigned 32 bit numbers

        #send the I/F values of the two channels!
        JSocket.write_msg(sock,DDSftw_IF_A_OFFSET, int(IF_A_FTW)) #these must be sent as unsigned 32 bit numbers
        JSocket.write_msg(sock,DDSftw_IF_B_OFFSET, int(IF_B_FTW)) #these must be sent as unsigned 32 bit numbers
    
        print "IF A FTW:" + str(int(IF_A_FTW))
        
        #reset the RP FSM and prepare it for a trigger!
        JSocket.write_msg(sock,DDSawaittrigger_OFFSET,0) #value sent doesn't affect anything
    
        #for now, give it a software trigger, for testing!
        #input()
        if SWTrigger:
            JSocket.write_msg(sock,DDSsoftwaretrigger_OFFSET,0) #value sent doesn't affect anything

def SendSequenceSimple (A_dat,B_dat): #dummy that takes data in the form A_dat=[IF_A_hz,[[t1_A_sec,f1_A_hz],[t2_A_sec_,f2_A_hz]...]], and then the same thing for B_dat
    IFfreqA_hz=A_dat[0]
    timesA_sec=[d[0] for d in A_dat[1]]
    freqsA_hz= [d[1] for d in A_dat[1]]

    IFfreqB_hz=B_dat[0]
    timesB_sec=[d[0] for d in B_dat[1]]
    freqsB_hz= [d[1] for d in B_dat[1]]
    
    sendsequence (IFfreqA_hz,IFfreqB_hz, timesA_sec, freqsA_hz, timesB_sec,freqsB_hz)

#todo
#test hardware triggers!
def SendDataToRP(REDPITAYA_IP, SOFTWARETRIGGER, CH1_DATA, CH2_DATA):

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
        JSocket.write_msg(sock, LEDADDRESS, 0)               #DAC/ADC behave better with LEDS off! WEIRD!

    SendSequenceSimple(CH1_DATA,CH2_DATA)
    
    if(DEBUGMODE==False):
        JSocket.write_done(sock)
        sock.close()



##############################################################################################
##############################################################################################
#####################################END OF SETUP CODE########################################
