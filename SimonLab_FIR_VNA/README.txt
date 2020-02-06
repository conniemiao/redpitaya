######################Updated February 1, 2017######################
######################### by the SimonLab ##########################
This is the readme for the RedPitaya (RP) realtime FIR (finite impulse response) filter with built-in VNA (vector network analyzer), as described in the simonlab publication: http://aip.scitation.org/doi/10.1063/1.4973470.

Included in this package are the following files:

CLIENT-SIDE (COMPUTER) FILES:
>>SendFIR.py              ---- Python 2.7 script to send  FIR filter to the RP FPGA
>>VNAScan.py                 ---- Python 2.7 script for simultaneous RP VNA
>>JSocket.py                 ---- Python 2.7 helper library for the preceding codes
>>installscript              ---- Shell script (written for a macOS shell) that sends the necessary files to the RP, turns off unnecessary services, and starts the server
>>GenerateFilter.nb          ---- Sample Mathematica code for generating an FIR filter for sending to the RP.
>>MakePlot.nb                ---- Sample code for plotting the output of the VNA
>>time_coefficients_unit.csv ---- Sample FIR filter that produces a delta-function at time zero; this is the default that should be employed for initial testing!
>>time_coefficients.csv      ---- Sample FIR filter that produces the complex spectrum featured in the aforementioned publication; for debugging purposes.

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

==To test out the FIR filter, we will set it to act as an impulse response with zero time delay. In the shell (in the directory of the unzipped files), run (with rpIP replaced with the actual IP address, as above):
"python SendFIR.py FIR_coeffs=time_coefficients_unit.csv RP_IP=rpIP Outputshift=17 FIR_prescale=-91500"

Now send a 500mVpp sinusoid (with no DC offset) at a few kHz into IN1 of the RP using a synthesizer, and measure OUT1 on an oscilloscope; you should see a sinusoid of amplitude 640mVpp. Alternatively, connect IN1 and OUT1 up to a commercial VNA and measure the flat frequency response with delay of ~2.6uS, up to ~125kHz.

==Next we will implement a fancier impulse response function. Run (with rpIP replaced with the actual IP address, as above):
"python SendFIR.py FIR_coeffs=time_coefficients.csv RP_IP=rpIP Outputshift=17 FIR_prescale=-91500"

Now send a 100mVpp sinusoid (with no DC offset) into IN1 of the RP using a synthesizer, and measure OUT1 on an oscilloscope; you should see a maximum response (pole) of ~610mVpp for a frequency of 3.340kHz, with a bandwidth (FWHM) of ~150Hz. Similarly, there should be a zero near 5.46kHz, and the next pole near 6.01kHz, with a bandwidth of 80Hz.Alternatively, connect IN1 and OUT1 up to a commercial VNA and measure the frequency and phase response, reproducing the data from the paper mentioned at the top of this README.


==To test the VNA functionality, preconfigure the FIR filter as above, and now measure the 3.340kHz resonance of the FIR filter using one of the many modes of the VNA (with rpIP replaced with the actual IP address, as above):
"python VNA_Scan.py RP_IP=rpIP Fstart_Hz=3000 Fstop_Hz=3600 ScanPts=100 DrivedBm=-48 ExcitePos=PreFIR MeasPosB=PreFIRPostDrive MeasPosA=PostFIRPostDrive SweepMode=linear Outfile=VNA_output.csv"

Now VNA_output.csv contains the measured spectrum, in the form of the real and imaginary parts of the the measured signal at both MeasurementPositionA (before the FIR filter but after the noise injection point, in this case), and Measurement Position B (after the FIR filter, in this case). To read this data most conveniently, open and run "MakeVNAPlot.nb" in Mathematica (tested in Mathematica 11, but presumably broadly compatible.)

If you would like to generate your own FIR filters, look in GenerateFilter.nb for sample code that produces a filter "tsequence.csv" which may be sent to the RP via the command (with rpIP replaced with the actual IP address, as above):

"python SendFIR.py FIR_coeffs=tsequence.csv RP_IP=rpIP Outputshift=17 FIR_prescale=-91500"

NOTES:
==FURTHER DOCUMENTATION FOR EACH OF THE PYTHON SCRIPTS IS AVAILABLE BY RUNNING IT WITHOUT PROVIDING ANY INPUTS
==The TCPIP server running on the RP is not terribly robust-- if you can no longer connect properly please power down the RP, power it back up, and try again.
==installscript.sh disables all web-server functionality for the memory card in RP, and replaces all FPGA functionality; if you would like to use the standard configuration (oscilloscope, signal generator, AWG, etc...) prepare a separate memory card for this purpose.
==The plotting routine in the python VNA is not operational. please use the mathematica code to plot.
