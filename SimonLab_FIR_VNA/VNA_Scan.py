"""
Last modified 7/8/2016
Written by Jon
Send to RP
"""

from struct import pack, unpack
import math

from math import *

import parser
import sys
import os
import numpy as np

import re
import csv
import time

import JSocket
import socket

def convert_2c(val, bits): #take a signed integer and return it in 2c form
    if (val>=0):
        return val
    return ((1 << bits)+val)

def convert_back(val, bits): #take a signed integer and return it in 2c form
    if (val>=2**(bits-1)):
        return (val-2**bits)
    return val

#IMPLEMENT CONVERSION FROM/TO TWOS COMPLEMENT!

def extract_2c(val, bits):
    if val >= 1<<(bits-1): val -= 1<<bits
    return val

def convertsimple(val):
    numbits=32
    return convert_2c(val,numbits)

def extractsimple(val):
    numbits=32
    return extract_2c(val,numbits)

#######################################################################4###################################!!!!!

#ADDRESSES IN THE MEMORY MAPPED ADDRESS SPACE

LEDADDRESS              = 0x40000030
OUTPUTBITSHIFTADDRESS   = 0x40300000
FIRCOEFFSADDRESS        = 1076887552+4*(32)
FIRCOEFFSADDRESSOFFSET  = 1076887552+4*(4)

VNAftwADDRESS           = 1076887552+4*(8)         ;#address of the VNA frequency tuning word
VNAampOUTADDRESS        = 1076887552+4*(12)        ;#address of the VNA amplitude, which is the number of bits to shift the sine-wave to the right before outputting it! larger value means smaller amplitude!
VNAavgcoeffADDRESS      = 1076887552+4*(16)        ;#address of the VNA coefficient for averaging (ynew=yold-yold>>VNAAvgCoeff+xnew)
VNAinputprescalerADDRESS= 1076887552+4*(20)        ;#address of the VNA input prescaler (number of bits to right-shift input signal before putting into deconvolver/averager!)
VNAiomodeADDRESS        = 1076887552+4*(24)        ;#address of the VNA mode:
                                                    #XX1: VNA output goes into FIR input
                                                    #XX0: VNA output goes into FIR output
                                                    #00X: VNA input comes from FIR input  BEFORE VNA output terminal
                                                    #01X: VNA input comes from FIR input  AFTER  VNA output terminal
                                                    #10X: VNA input comes from FIR output BEFORE VNA output terminal
                                                    #11X: VNA input comes from FIR output AFTER  VNA output terminal
                                              #XXXX0: VNA output goes into FIR output
                                              #XXXX1: VNA output goes into FIR input
                                              #XX00X: VNA input A comes from FIR input  BEFORE VNA output terminal
                                              #XX01X: VNA input A comes from FIR input  AFTER  VNA output terminal
                                              #XX10X: VNA input A comes from FIR output BEFORE VNA output terminal
                                              #XX11X: VNA input A comes from FIR output AFTER  VNA output terminal
                                              #00XXX: VNA input B comes from FIR input  BEFORE VNA output terminal
                                              #01XXX: VNA input B comes from FIR input  AFTER  VNA output terminal
                                              #10XXX: VNA input B comes from FIR output BEFORE VNA output terminal
                                              #11XXX: VNA input B comes from FIR output AFTER  VNA output terminal

VNAiahADDRESS           = 1076887552+4*(4)
VNAialADDRESS           = 1076887552+4*(8)
VNAqahADDRESS           = 1076887552+4*(12)
VNAqalADDRESS           = 1076887552+4*(16)

VNAibhADDRESS           = 1076887552+4*(20)
VNAiblADDRESS           = 1076887552+4*(24)
VNAqbhADDRESS           = 1076887552+4*(28)
VNAqblADDRESS           = 1076887552+4*(32)

ChBRdADDRESS            = 1076887552+4*(36)

####THESE ARE THE ROUTINES FOR INTERACTING WITH THE RPs!

def sendpitaya (addr, val):
    numbits=32
    JSocket.write_msg(sock, addr,convert_2c(val,numbits))

def getVNAdat():
    dat=[]

    U=JSocket.read_mem(sock,VNAiahADDRESS)*(2**32) #order matters. running this memory call freezes the data until the next call to this address!
    V=JSocket.read_mem(sock,VNAialADDRESS)
    dat.append(extract_2c(U+V,64)) #Ai

    U=JSocket.read_mem(sock,VNAqahADDRESS)*(2**32)
    V=JSocket.read_mem(sock,VNAqalADDRESS)
    dat.append(extract_2c(U+V,64)) #Aq
    
    U=JSocket.read_mem(sock,VNAibhADDRESS)*(2**32)
    V=JSocket.read_mem(sock,VNAiblADDRESS)
    dat.append(extract_2c(U+V,64)) #Bi

    U=JSocket.read_mem(sock,VNAqbhADDRESS)*(2**32)
    V=JSocket.read_mem(sock,VNAqblADDRESS)
    dat.append(extract_2c(U+V,64)) #Bq

    return(dat)

def freqscan( rp_ip, freqstart, freqstop, npts, pdBm, drivelocation, swpmode):
    ClockFreqHz=125000000.
    
    if (swpmode=="linear"):
        df=(freqStop-freqStart)/float(npts-1.0)
        freqs=np.arange(freqStart,freqStop+.00001,df)
        print "Sweep Mode: linear"
    else: #swpmode=="log"
        freqs=np.exp(np.arange(np.log(freqstart),np.log(freqstop)+.00001,np.log(freqstop/freqstart)/(npts-1.0)))
        print "Sweep Mode: log"

    p0dBm=-32.0 #calibration power for 0 bit shift!
    logampbits=np.floor((int(pdBm)-p0dBm)*(np.log(10.0)/np.log(2.0))/20.0)
    logamp = int(logampbits)

    print "npts: " + str(npts)
    print "freqStart: " + str(freqStart)
    print "freqStop: " + str(freqStop)
    print "amp shift: " + str(logamp)
    
    print "Connecting to Red Pitaya at IP address " + REDPITAYA_IP + " ......."

    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket to the port where the server is listening
    server_address = (REDPITAYA_IP, 10000)
    print >>sys.stderr, 'connecting to %s port %s' % server_address
    sock.connect(server_address)
    print "Connected!"

    JSocket.write_msg(sock,LEDADDRESS, 0)               #DAC/ADC behave better with LEDS off! WEIRD!
    sendpitaya(VNAampOUTADDRESS, logamp)
    JSocket.write_msg(sock,VNAiomodeADDRESS, drivelocation)

    dats=[]
    xdat=[]
    ydat=[]
    zdat=[]

    CHBVoltage=convert_back(JSocket.read_mem(sock,ChBRdADDRESS),14)

    for ii in range(len(freqs)):
        curFreqHz=freqs[ii]
        if ii<len(freqs)-1:
            adjFreqHz=freqs[ii+1]
        else:
            adjFreqHz=freqs[ii-1]
        print curFreqHz
        df=abs(curFreqHz-adjFreqHz)
        avgbits=int(np.log(ClockFreqHz/df)/np.log(2.0))
        JSocket.write_msg(sock,VNAavgcoeffADDRESS, avgbits)
        JSocket.write_msg(sock,VNAftwADDRESS, int(curFreqHz/(125000000.0)*(2.0**32.)))
        
        if ii==0:
            time.sleep(10.0/df)#wait long enough that the system can settle -- this is ~ 18 1/e times!!
        else:
            time.sleep(0.5/df)#wait long enough that the system can settle -- this is ~ 3 1/e times!!
        
        dat=getVNAdat()
        scaleddat=[(1.0/((2.0**logamp)*(2.0**avgbits)))*dd for dd in dat]
        dats.append([curFreqHz,scaleddat,CHBVoltage])

    JSocket.write_msg(sock,VNAftwADDRESS, 0)
    sendpitaya(VNAampOUTADDRESS, -10) #more bits than DAC SINE table depth!

    print "Voltage B:  " + str(CHBVoltage)

    return dats

def getparmval(strIn,parmname,defaultval):
    strlist=re.findall(parmname+"=([\w\a\.-]*)",strIn)
    if(len(strlist)>0):
        return strlist[0]
    else:
        return defaultval

def ConvertExciteLocation( locstr ):
    if locstr=="PreFIR":
        return 1
    else:
        return 0

def ConvertMeasLocation( locstr ):
    if locstr=="PreFIRPreDrive":
        return 0
    elif locstr=="PreFIRPostDrive":
        return 1
    elif locstr=="PostFIRPreDrive":
        return 2
    else:
        return 3

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
   
if __name__ == "__main__":
    if len(sys.argv)<2:
        print ""
        print ""
        print ""
        print bcolors.OKBLUE + "proper usage: " + bcolors.ENDC + "python FreqScan.py RP_IP=X.X.X.X Fstart_Hz=X Fstop_Hz=X ScanPts=X drivedBm=X ExcitePos=X MeasPosA=X MeasPosB=X SweepMode=X Outfile=X.csv"
        print bcolors.OKBLUE + "example :     " + bcolors.ENDC + "python FreqScanNameVer.py RP_IP=192.168.1.142 Fstart_Hz=1000 Fstop_Hz=20000 ScanPts=500 DrivedBm=-32 ExcitePos=PreFIR MeasPosA=PreFIRPostDrive MeasPosB=PostFIRPreDrive SweepMode=log Outfile=outputdata.csv PlotMode=true"
        print bcolors.OKBLUE + "DEFAULTS:     " + bcolors.ENDC + "RP_IP:192.168.0.100 Fstart_Hz=1000 Fstop_Hz=20000 ScanPts=100 DrivedBm=-32 ExcitePos=PreFIR MeasAPos=PreFIRPostDrive MeasBPos=PostFIRPreDrive SweepMode=log Outfile=outputdata.csv PlotMode=true"
        print "RBW is set automatically to the allowed value closest to (fi-fi+1), for each datapoint"
        print ""
        print bcolors.OKBLUE + bcolors.BOLD + "ALLOWED INPUTS -- Descriptions" + bcolors.ENDC
        print bcolors.FAIL + "ScanPts:" + bcolors.ENDC + "             10 to 10000  -- number of points in the scan"
        print bcolors.FAIL + "Fstart_Hz, Fstop_Hz:" + bcolors.ENDC + " 10 to 100000 -- self explanatory"
        print bcolors.FAIL + "DrivedBm:" + bcolors.ENDC + "            -56 to 8     -- -32dBm is the DDS internal amplitude"
        print bcolors.FAIL + "SweepMode:" + bcolors.ENDC + "           linear or log"
        print bcolors.FAIL + "ExcitePos:" + bcolors.ENDC + "           PreFIR, PostFIR"
        print bcolors.FAIL + "MeasPosA/B:" + bcolors.ENDC + "          PreFIRPreDrive, PreFIRPostDrive, PostFIRPreDrive, PostFIRPostDrive"
        print bcolors.FAIL + "OutFile:" + bcolors.ENDC + "             is the name of the file in the local directory where the output data goes!"
        print bcolors.FAIL + "PlotMode:" + bcolors.ENDC + "            true, false; true means plot (B channel, I and Q) at the end"
        print ""
        print ""
        print ""
        exit()

    print ""
    print ""
    print "Preparing to Scan!"
    cmdstr=""
    for tARG in sys.argv:
        cmdstr=cmdstr+" "+tARG
    
    #Extract Control Parameters    
    REDPITAYA_IP = getparmval(cmdstr, "RP_IP","192.168.0.100")
    freqStart= int(getparmval(cmdstr, "Fstart_Hz","1000"))
    freqStop= int(getparmval(cmdstr, "Fstop_Hz","20000"))
    npts     = int(getparmval(cmdstr, "ScanPts","100"))
    pdBm     = int(getparmval(cmdstr, "DrivedBm","-32"))
    drivelocation = ConvertExciteLocation(getparmval(cmdstr, "ExcitePos","PreFIR"))+ConvertMeasLocation(getparmval(cmdstr, "MeasPosA","PreFIRPostDrive"))*2+ConvertMeasLocation(getparmval(cmdstr, "MeasPosB","PostFIRPreDrive"))*2*4
    outfilename = getparmval(cmdstr, "Outfile","outputdata.csv")
    sweepmode = getparmval(cmdstr, "SweepMode","log")
    plotmode = getparmval(cmdstr, "PlotMode","false")


    print "Drive/Measure Control Param: " + str(drivelocation)
    print "Output Filename: " + outfilename
    print "Plot Mode: " + plotmode
    
    jdats=freqscan( REDPITAYA_IP, freqStart, freqStop, npts, pdBm, drivelocation, sweepmode)
 
    JSocket.write_done(sock)
    sock.close()

    out=open(outfilename,"wb")
    output=csv.writer(out)

    for row in jdats:
        output.writerow(row)
    out.close()