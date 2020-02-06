#!/bin/sh
echo "argument is RedPitaya IP, of the form rp-XXXXXX.local, where XXXXXX are the last six digits of the RP MAC address, written on the device's ethernet port"
echo "this code assumes that the login is root, which is essential for many of these operations. You will have to repeatedly enter the password (default is root)"

scp RPServer.py SimonLab_MDDS.bit JSocket.py root@$1:~
scp rc.local root@$1:/etc/rc.local
scp FPGAreporter.py root@$1:/usr/bin/FPGAreporter.py

ssh root@$1 "systemctl disable redpitaya_nginx;systemctl disable redpitaya_wyliodrin;systemctl disable redpitaya_scpi"
ssh root@$1 "nohup python RPServer.py </dev/null >/dev/null 2>&1 &"
ssh root@$1 "nohup python /usr/bin/FPGAreporter.py </dev/null >/dev/null 2>&1 &"
