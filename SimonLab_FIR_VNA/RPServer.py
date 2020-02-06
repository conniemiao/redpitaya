import mmap
import struct
import os
import time
import socket
import sys
from JSocket import *

RP_BASEADDRESS = 0x40000000
RP_FPGARAMSIZE = 0x00800000

RPVERSION=True

#THIS SCRIPT ASSUMES THAT NGINX AND WYLIODRIN HAVE BEEN DISABLED, AND THE .bit file installed!
#http://wiki.redpitaya.com/tmp/RedPitaya_HDL_memory_map.pdf

bitfileloaded=False

if RPVERSION:

    fd = os.open('/dev/mem', os.O_RDWR)
    m = mmap.mmap(fileno=fd, length=RP_FPGARAMSIZE, offset=RP_BASEADDRESS)

    #ALL ADDRESSES SHOULD BE SENT LITTLE-ENDIAN!
    #DATA WILL BE WRITTEN INTO MEMORY EXACTLY AS SENT, SO IT IS INCUMENT ON WRITE COMMANDS TO GET THIS CORRECT
        
#  built on https://docs.python.org/2/howto/sockets.html

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind the socket to the port
if RPVERSION:
    server_address = (socket.gethostname()+".local", 10000)
else:
    server_address = ("127.0.0.1", 10000)

print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)
# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print >>sys.stderr, 'waiting for a connection'
    connection, client_address = sock.accept()
    
    if bitfileloaded==False:
        os.system('cat /root/SimonLab_FIRVNA.bit > /dev/xdevcfg')
        bitfileloaded=True
    try:
        print >>sys.stderr, 'connection from', client_address
        # Receive the data in small chunks and retransmit it
        while True:
            msg=rcv_msg(connection)
            print "the message is:",
            print msg
            if (msg[0]=='Q'):
                    break
            if RPVERSION:
                if (msg[0]=='w') or (msg[0]=='W'):
                    for kk in range(len(msg[2])/4):
                        m[msg[1]+4*kk:msg[1]+4*kk+4]=msg[2][4*kk:4*kk+4]
#                    m[msg[1]:msg[1]+len(msg[2])]=msg[2]
                elif(msg[0]=='r'):
                    write_msg(connection,0,struct.unpack('<I',m[msg[1]:msg[1]+4])[0])
                    print "the value is:"+str(struct.unpack('<I',m[msg[1]:msg[1]+4])[0])
                else:
                    print "not implemented!"
            print ""
        print "\n\nclosing"
    except Exception:
        print "Socket Closed Abruptly by Peer"
    finally:
        # Clean up the connection
        connection.close()
