######################Updated February 1, 2017######################
######################### by the SimonLab ##########################
This is the readme for the RedPitaya (RP) realtime MDDS.

Included in this package are the following files:

CLIENT-SIDE (COMPUTER) FILES:
>>SendFIR.py                 ---- Python 2.7 script to send DDS data to RP
>>VNAScan.py                 ---- Python 2.7 script for simultaneous RP VNA
>>JSocket.py                 ---- Python 2.7 helper library for the preceding codes
>>installscript              ---- Shell script (written for a macOS shell) that sends the necessary files to the RP, turns off unnecessary services, and starts the server

SERVER-SIDE (RP) FILES:
>>JSocket.py                 ---- Same as above, but used on the RP for communication as well.
>>RPServer.py                ---- The TCP-IP server that runs on the RP to process requests from the client (computer).
>>SimonLab_FIRVNA.bit        ---- This is the .bit file which is the heart of the device, and acts to configure the reconfigurable hardware of the FPGA within the RP.
>>rc.local                   ---- This is the rc.local file that helps with usage reporting
>>FPGAreporter.py            ---- This is the pythonscript that performs the usage reporting


###########################     SETUP  & TESTING   ###########################
==The RP should be configured to run the 0.96 RC1 stable build-- newer builds might be ok, but no guarantees. For information on preparing a memory card for the RP see: https://redpitaya.readthedocs.io/en/latest/

==The RP must be connected up to the same router as the computer that you intend to use to communicate with it. (This isn't strictly true, but otherwise the communication will require properly routing packets through the router).

==The next step is to be certain that you can communicate between your computer and the redpitaya. Find the redpitaya's MAC address written on the ethernet port of the board. The IP address, called rpIP, is given by rpIP=rp-XXXXXX.local, where XXXXXX is the last six digits of the MAC address (ex: rp-F01E60.local for MAC address 00:26:32:F0:1E:60). To test the communication, ssh into the RP: in the shell, type "ssh root@rpIP", and enter "root" as your password. Remember to replace rpIP with the actual IP address ascertained above. If you can login, move on to the next step. If you cannot, we're sorry :)

==Next, go to the directory where you have unzipped these files, and in the shell, type "./installscript.sh rpIP" (where rpIP is replaced with the IP/hostname ascertained above) This will send the necessary files and reconfigure the RedPitaya to act as the FIR filter and VNA. You will have to enter the password ("root") several times unless you have set up passwordless ssh with keygen. The RP is now configured and will load the correct bitfile and all relevant servers and status reporting programs on boot. Please power it down by unplugging it, and plug it back in (then wait a minute for it to boot) before proceeding.

==To test out the MDDS, we will send it a test-script, and watch the output on a spectrum analyzer with START freq 0 MHz, and STOP freq 40 MHz. Connect OUT1 of the RP to your spectrum analyzer, and in the shell (in the directory of the unzipped files), run (with rpIP replaced with the actual IP address, as above):
"python MDDS_Test.py RP_IP=rpIP SOFTWARETRIGGER=1"

This should induce the RP to output 10 frequencies simultaneously (f_n=2*n MHz @ t=0), ramping to (f_n=4*n MHz @ t=4 seconds), and back @ t=8 seconds); the amplitudes should sweep as well.

==To build your own script, simply copy MDDS_Test.py into a new file and modify it; the format of the data to be sent to the MDDS is explained within the .py file!

==To use the hardware triggering, simply replace "SOFTWARETRIGGER=1" with "SOFTWARETRIGGER=0", and supply a TTL trigger to the extension connector "DIO0_P" ("exp_p_in[0]" in the old RP notation) as defined in "http://redpitaya.readthedocs.io/en/latest/developerGuide/125-14/extent.html"
NOTES:
==The TCPIP server running on the RP is not terribly robust-- if you can no longer connect properly please power down the RP, power it back up, and try again.
==installscript.sh disables all web-server functionality for the memory card in RP, and replaces all FPGA functionality; if you would like to use the standard configuration (oscilloscope, signal generator, AWG, etc...) prepare a separate memory card for this purpose
