import socket
import struct

RP_BASEADDRESS = 0x40000000

def int2base(x,b,alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    'convert an integer to its string representation in a given base'
    if b<2 or b>len(alphabet):
        if b==64: # assume base64 rather than raise error
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        else:
            raise AssertionError("int2base base out of range")
    if isinstance(x,complex): # return a tuple
        return ( int2base(x.real,b,alphabet) , int2base(x.imag,b,alphabet) )
    if x<=0:
        if x==0:
            return alphabet[0]
        else:
            return  '-' + int2base(-x,b,alphabet)
    # else x is non-negative real
    rets=''
    while x>0:
        x,idx = divmod(x,b)
        rets = alphabet[idx] + rets
    return rets

def read_mem( s, addr ):
    s.sendall('r'+struct.pack('<I',addr))
    message=rcv_msg(s)
    return struct.unpack('<I',message[2])[0]

def write_msg( s, addr, val ): #write one word (4 bytes)
    s.sendall('w'+struct.pack('<I',addr)+struct.pack('<I',val))

def writeS_msg( s, addr, vals ): #write N words (4N bytes)-- vals is an array of words
    v1='W'+struct.pack('<I',addr)+struct.pack('<I',4*len(vals))+struct.pack('<'+('I' * len(vals)), *vals)
    s.sendall(v1)

def write_done( s ): 
    s.sendall('Q    ')

def recv_len(s,l): #receive data of length l from socket s
    data="";
    lremaining=l;
    while(lremaining>0):
        newdat=s.recv(lremaining)
        if newdat=="":
            print "disconnected!"
            raise Exception('Socket Closed!')
        data+=newdat
        lremaining=l-len(data)
    return(data)

def rcv_msg( s ):
    #DO THESE THINGS BLOCK PROPERLY!?!
    addrLEN   =4 #four-byte address should be more than enough!
    valLEN    =4 #all values are four bytes, because that is our address step anyway!
    listlenLEN=4 #four bytes to describe length of list (in bytes) to follow!
    datatype=recv_len(s,1)[0]
    dataADDR,=struct.unpack('<I',recv_len(s,addrLEN))
    print "dataADDR is: 0x" + int2base(dataADDR,16)
    dataADDR-= RP_BASEADDRESS
    print "datatype is: " + str(datatype)
    if (datatype=='w'): #write (one address, and then one value)
        dataVAL=recv_len(s,valLEN)
        return ['w',dataADDR,dataVAL]
    elif (datatype=='r'): #read (one address)
        return ['r',dataADDR]
    elif (datatype=='W'): #write (start address, numbytes, bytelist)
        dataLEN,=struct.unpack('<I',recv_len(s,listlenLEN))
        dataLIST=recv_len(s,dataLEN)
        return ['W',dataADDR,dataLIST]
    elif (datatype=='R'): #read (start address, numbytes)
        dataLEN,=struct.unpack('<I',recv_len(s,listlenLEN))
        return ['R',dataADDR,dataLEN]
    elif (datatype=='Q'):
        return ['Q']
    else:
        print "FAIL"