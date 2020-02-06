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

LEDADDRESS              =0x40000030    #address in FPGA memory map to control RP LEDS

maxevents                  =   64*16

DDS_CHANNEL_OFFSET          = 1076887552+4*0                  #offset in WORDS (4 bytes) to the channel that we are currently writing to!
DDSawaittrigger_OFFSET      = 1076887552+4*24                 #offset in WORDS (4 bytes) to address where we write ANYTHING to tell system to reset and await trigger
DDSsoftwaretrigger_OFFSET   = 1076887552+4*25                 #offset in WORDS (4 bytes) to address where we write ANYTHING to give the system a software trigger!
DDSftw_IF_OFFSET            = 1076887552+4*1                  #offset in WORDS (4 bytes) to the initial/final FTW for the current channel
DDSamp_IF_OFFSET            = 1076887552+4*3                  #offset in WORDS (4 bytes) to the initial/final amp for the current channel
DDSsamples_OFFSET           = 1076887552+4*2                  #offset in WORDS (4 bytes) to # of samples for the current channel

####EXPECT LOW WORD AT LOWER MEMORY ADDRESS FOR FREQS (FTW) RAMS! ###
DDSfreqs_OFFSET            = 1076887552+4*40                      #offset in WORDS to the first element of the current freq list
DDScycles_OFFSET           = DDSfreqs_OFFSET  + 4*maxevents*2     #offset in WORDS to the first element of the current cyc. list
DDSamps_OFFSET             = DDScycles_OFFSET + 4*maxevents*1     #offset in WORDS to the first element of the current cyc. list
DDSamps_last_OFFSET        = DDScycles_OFFSET + 4*maxevents*2 - 1 #offset in WORDS to the last  element of the current cyc. list

maxsendlen=31*512  #most FIR coefficients we can send at a time
fclk_Hz=125*(10**6) #redpitaya clock frequency
DDSamp_fracbits = 14 #number of DDS bits to the right of the decimal point (all of them, of course!)
DDSchannels = 10 #number of DDS freqs we can simultaneously output!

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

def SendSeqToChannel (channel, IFfreq_hz, IFamp_frac,times_sec, freqs_hz, amps_frac ):
    if (len(times_sec)>maxevents):
        print bcolors.FAIL + "TOO MANY EDGES ON CHANNEL-- EXCEEDS RED PITAYA RAM SPACE OF " + str(maxevents) + bcolors.ENDC
        exit()

    IFamp_frac_c=min(IFamp_frac,1.0-2.0**(-DDSamp_fracbits)) #make sure we don't overflow the amplitude!
    IF_ATW=int(IFamp_frac_c*(2.0**DDSamp_fracbits))
    
    amps_frac_c=[min(amps_frac[i],1.0-2.0**(-DDSamp_fracbits)) for i in range(len(amps_frac))] #make sure we don't overflow the amplitude!
    deltas_amp_frac=[(amps_frac_c[i+1]-amps_frac_c[i]) for i in range(len(times_sec)-1)]
    deltas_amp_frac.insert(0,amps_frac_c[0]-IFamp_frac_c)

    IF_FTW=HzToFTW(IFfreq_hz)
    freqs_FTW=map(HzToFTW,freqs_hz)

    deltas_FTW=[(freqs_FTW[i+1]-freqs_FTW[i]) for i in range(len(times_sec)-1)]
    deltas_FTW.insert(0,freqs_FTW[0]-IF_FTW)

    times_cyc=map(SecToCycles,times_sec)
    
    dt_cyc=[max(2,int(round(times_cyc[i+1]-times_cyc[i]))) for i in range(len(times_sec)-1)] #we use two cycles min, as the RAM might not be fast enough otherwise :(
    dt_cyc.insert(0,max(1,int(round(times_cyc[0]))))
    
    df_FTW=[int(round((2.0**32)                  *deltas_FTW     [i]/dt_cyc[i])) for i in range(len(dt_cyc))]
    da_ATW=[int(round((2.0**(32+DDSamp_fracbits))*deltas_amp_frac[i]/dt_cyc[i])) for i in range(len(dt_cyc))]
    
    if(DEBUGMODE==False):
        #print "Length of dt_cyc: " + str(len(dt_cyc))
        #print "Length of df_FTW: " + str(len(df_FTW))
        #print "IFamp: " +str(IFamp_frac)
        
        #set the channel that we are writing to!
        JSocket.write_msg(sock, DDS_CHANNEL_OFFSET,channel)

        #send the number of samples on each channel
        JSocket.write_msg(sock, DDSsamples_OFFSET,len(times_sec))
        #print "listlen: " + str(len(times_sec))

        #send step sizes for each ramp!
        print "[cycles,df,da]:"
        for i in range(len(dt_cyc)): #data must be sent as dFTW,dAMP, and corresponding cycles, as the last is when all are written into the memory!
            sendpitaya_long(DDSfreqs_OFFSET  + 8*i,df_FTW[i] )  #these must be sent as 2's complement 64 bit numbers
            sendpitaya_long(DDSamps_OFFSET   + 8*i,da_ATW[i]  ) #these must be sent as 2's complement 64 bit numbers            
            JSocket.write_msg(sock, DDScycles_OFFSET+4*i,dt_cyc[i] )#these must be sent as unsigned 32 bit numbers
            print "["+str(dt_cyc[i])+","+str(df_FTW[i])+","+str(da_ATW[i])+"]"
        #send the I/F values of the  channel
        JSocket.write_msg(sock, DDSftw_IF_OFFSET,int(IF_FTW))#these must be sent as unsigned 32 bit numbers
        JSocket.write_msg(sock, DDSamp_IF_OFFSET,int(IF_ATW))#these must be sent as unsigned 32 bit numbers
        #print "IF_ATW: " +str(IF_ATW)

def SendSequenceSimple (A_dat,B_dat): #dummy that takes data in the form A_dat=[IF_A_hz,[[t1_A_sec,f1_A_hz],[t2_A_sec_,f2_A_hz]...]], and then the same thing for B_dat
    IFfreqA_hz=A_dat[0][0]
    IFampA_frac=A_dat[0][1]
    timesA_sec = [d[0] for d in A_dat[1]]
    freqsA_hz  = [d[1] for d in A_dat[1]]
    ampsA_frac = [d[2] for d in A_dat[1]]

    IFfreqB_hz  = B_dat[0][0]
    IFampB_frac = B_dat[0][1]
    timesB_sec  = [d[0] for d in B_dat[1]]
    freqsB_hz   = [d[1] for d in B_dat[1]]
    ampsB_frac  = [d[2] for d in B_dat[1]]
    
    #SendSeqToChannel (1,IFfreqB_hz, timesB_sec, freqsB_hz)

    SendSeqToChannel (1,IFfreqB_hz,IFampB_frac, timesB_sec, freqsB_hz, ampsB_frac)
    SendSeqToChannel (0,IFfreqA_hz,IFampA_frac, timesA_sec, freqsA_hz, ampsA_frac)

    #reset the RP FSM and prepare it for a trigger!
    JSocket.write_msg(sock, DDSawaittrigger_OFFSET,0)#value sent doesn't affect anything
    

    if SWTrigger:  #if enabled, give it a software trigger!
        JSocket.write_msg(sock, DDSsoftwaretrigger_OFFSET,0)#value sent doesn't affect anything

def SendFullSeqs( AllSeqs ):
    #the data for each channel is an element of AllSeqs, sent as follows:
        #[[IFfreq_Hz,IFamp_frac],[[time_sec,freq_Hz,amp_frac]]]
    if (len(AllSeqs)>DDSchannels):
        print "TOO MANY CHANNELS FOR FPGA! FAIL!"
        exit()
    for chan in range(DDSchannels):
        if (chan<len(AllSeqs)):
            curdat=AllSeqs[chan]
        else:
            curdat=[[0.0,0.0],[[.0001,0.0,0.0]]]

        IFfreq_Hz  = curdat[0][0]
        IFamp_frac = curdat[0][1]
        times_sec  = [curdat[1][k][0] for k in range(len(curdat[1]))]
        freqs_Hz   = [curdat[1][k][1] for k in range(len(curdat[1]))]
        amps_frac  = [curdat[1][k][2] for k in range(len(curdat[1]))]
        
        SendSeqToChannel (chan,IFfreq_Hz,IFamp_frac,times_sec,freqs_Hz,amps_frac)

    #reset the RP FSM and prepare it for a trigger!
    JSocket.write_msg(sock, DDSawaittrigger_OFFSET,0)#value sent doesn't affect anything
    
    if SWTrigger:  #if enabled, give it a software trigger!    
        JSocket.write_msg(sock, DDSsoftwaretrigger_OFFSET,0)#value sent doesn't affect anything



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
        JSocket.write_msg(sock, LEDADDRESS, 0)               #DAC/ADC behave better with LEDS off! WEIRD!

    SendFullSeqs(CHs_DATA)

    if(DEBUGMODE==False):
        JSocket.write_done(sock)
        sock.close()
