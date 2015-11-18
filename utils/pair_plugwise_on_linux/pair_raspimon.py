# Following this document:
# http://www.maartendamen.com/wp-content/uploads/downloads/2010/08/Plugwise-unleashed-0.1.pdf
from CrcMoose import *
import serial
import getopt, sys, os
import struct, math
from time import sleep

import raspi_mon_sys.Utils as Utils

SOURCE_MAC = "Source MAC: "
DESTINATION_MAC = "Destination MAC: "
HEADER = '\x05\x05\x03\x03'
ENDLINE = '\x0d\x0a'
CIRCLE_PLUS_MARK = '\x83'
RESPONSEMac = '0019'
RESPONSEVar = '00'
RESPONSEStick = 'A'
RESPONSEMaster = '00'
DEVICE_FILE = "/dev/ttyUSB0"

def Take(array,n):
    return (array[0:n],array[n:])

def GetCRC16(value):
    value = CRC16X.calcString(value)
    format = ("%%0%dX" % ((CRC16X.width + 3) // 4))
    return format % value

def SendCommandNoCRC(s, cmd):
    print "\t","CMD:",cmd[0:-4],cmd[-4:]
    s.write(HEADER + cmd + ENDLINE)

def SendCommand(s, cmd):
    SendCommandNoCRC(s, cmd + GetCRC16(cmd))

def ReadMark(s, mark):
    assert s.read(1) == mark

def Read(s, n):
    result = []
    while n>0:
        c = s.read(1)
        if c != chr(131) and c != chr(165)  and c != chr(135):
            result.append(c)
            n -= 1
    return ''.join(result)

def ReadLine(s, n):
    header = Read(s, len(HEADER))
    assert header == HEADER
    
    line = Read(s, n)
    crc16 = Read(s, 4)
    print "\t\t","REP:",line,crc16
    assert crc16 == GetCRC16(line)
    assert Read(s, 2) == ENDLINE
    
    return line

def ReadAndCheckACK(s):
    ack = ReadLine(s,12)
    start = ack[:4]
    message_number = ack[4:8]
    ack_code = ack[8:12]
    assert start == "0000"
    assert ack_code == "00C1"

class Plugwise:
    def __init__(self, port, macaddressidentity):
        self.macaddressidentity = macaddressidentity


    def InitialisationCircle(self):
        self.SendCommandInit("0008014068")
        self.GetResult(self.RESPONSEVar)

    def PairCircle(self):
        self.SendCommand("000701" + self.macaddressidentity)
        self.GetResult(self.RESPONSEVar)
        self.SendCommand("0023"+ self.macaddressidentity)
        self.GetResult(self.RESPONSEVar)

    def NetworkInfo(self):
        i = ['00','01','02','03','04','05','06','07','08','09','0A','0B','0C','0D','0E','0F','10','11','12','13','14','15','16','17','18','19','1A','1B','1C','1D','1E','1F','20','21','22','23','24','25','26','27','28','29','2A','2B','2C','2D','2E','2F','30','31','32','33','34','35','36','37','38','39','3A','3B','3C','3D','3E','3F']
	prise = ''
        for x in i :
            self.SendCommand("0018" + self.macaddressidentity + x)
            result = self.GetResult(self.RESPONSEMac)
            var = result[11]+result[12]+result[13]+result[14]+result[15]
	    if var in self.macaddressidentity:
                prise = 1
        if prise == 1:
	    return 0
	else:
	    return 1



    def SendCommand(self, command):
        self.serial.write(self.HEADER + command + self.GetCRC16(command) + self.ENDLINE)

def InitStick(s, stick, circle_plus):
    # Init command
    SendCommandNoCRC(s, "000AB43C") # 000A is the command B43C is the CRC16
    
    ReadAndCheckACK(s)
    
    response = ReadLine(s,28)
    ReadMark(s,chr(131))
    
    code,response = Take(response,4)
    message_number,response = Take(response,4)
    MC,response = Take(response,16)
    UNK1,response = Take(response,2)
    is_online,response = Take(response,2)
    # NC,response = Take(response,16)
    # network_id,UNK2 = Take(response,4)
    
    # assert len(UNK2) == 2
    assert code == "0011"
    assert MC == stick
    # assert NC == circle_plus
    # assert UNK2 == "FF"

    SendCommandNoCRC(s, "0001CAAB")

    ReadAndCheckACK(s)
    
    response = ReadLine(s,80)
    assert response[0:4] == "0002"
    response = ReadLine(s,12)
    assert response[0:4] == "0003"
    assert response[8:12] == "00CE"

def CirclePlusLink(s, stick, circle_plus):
    SendCommand(s, "000400000000000000000000" + circle_plus)
    #SendCommand(s, "000400010000000000000000" + circle_plus)
    
    ReadAndCheckACK(s)
    
    response = ReadLine(s,24)
    code1,response = Take(response,4)
    code2,response = Take(response,4)
    MC,response = Take(response,16)
    assert code1 == "0061"
    assert code2 == "FFFD"
    assert MC == stick
    
    response = ReadLine(s,12)
    code,response = Take(response,4)
    message_number,response = Take(response,4)
    UNK,response = Take(response,4)
    assert code == "0005"
    assert UNK == "0001"
    
def GetInfoCommand(s, stick, circle_plus):
    SendCommand(s, "0023"+ circle_plus)
    ReadAndCheckACK(s)
    response = s.read(110)
    print "\t\t",response.replace("\r\n","").replace("#","\n#")[:-1]
    
    idx = response.find(SOURCE_MAC)
    assert idx != -1
    start = idx+len(SOURCE_MAC)
    source_mac = response[start:(start+16)]
    assert source_mac == stick

    idx = response.find(DESTINATION_MAC)
    assert idx != -1
    start = idx+len(DESTINATION_MAC)+2
    dest_mac = response[start:(start+16)]
    assert dest_mac == circle_plus

def CirclePlusConnect(s, stick, circle_plus):
    SendCommand(s, "000401010000000000000000" + circle_plus)
    ReadLine(s,12)
    ReadMark(s,chr(131))

    GetInfoCommand(s, stick, circle_plus)

def PairCirclePlus(device, stick, circle_plus):
    print
    print "Installation Circle+"
    print "Attention: In case of failure you would need to reset your Circle+"
    print "Stick macaddress: ",stick
    print "Circle+ macaddress: ",circle_plus
    print "Dialog sequence"
    s = serial.Serial(DEVICE_FILE, "115200")
    
    InitStick(s, stick, circle_plus)

    CirclePlusLink(s, stick, circle_plus)
    print "Linking to Circle+... you should hear some noise..."
    sleep(35)
    print "Noise should be heared before this message ;)"
    
    CirclePlusConnect(s, stick, circle_plus)
    print "Connected to Circle+" 

def pair_circles(slaves, device):
    print 
    print "Installation Circle"
    print "Circles list :",slaves
    for circle in slaves:
        print "Pairing Circle :",circle
        plugwise = Plugwise(device, circle)
        print "Initialisation..."
        plugwise.InitialisationCircle()
        print "Linking to your Circle..."
        plugwise.PairCircle()
        print "Checking network..."
        plugwise.NetworkInfo()
        while plugwise.NetworkInfo() == 1:
            plugwise.InitialisationCircle()
            plugwise.PairCircle()
            plugwise.NetworkInfo()
        print "Your plug has been paired to the network successfully"
        print

def main():
    config  = Utils.getconfig("plugwise", None)
    stick   = config["stick"]
    pairing = config["pairing"]
    device  = "/dev/ttyUSB0"

    print
    print "**************************************************************"
    print "*                          Menu :                            *"
    print "*                                                            *"
    print "*  m  : Pair your Circle+ (Master) devices with USB stick    *"
    print "*  s  : Pair your Circle (Slave) devices with Circle+        *"
    print "*  q  : Exit                                                 *"
    print "*                                                            *"
    print "**************************************************************"
    print
    print "Enter a letter from the menu above :"
    arg = raw_input()
    print
    opts, args = getopt.getopt(sys.argv[1:], "m:s:q:",
                               ['master', 'slave', 'quit'])
    
    if arg == "m":
        for circle_plus in pairing.keys():
            PairCirclePlus(device, stick, circle_plus)
    elif arg == "s":
        for master,slaves in pairing.iteritems():
            pair_circles(slaves, device)
    elif arg == "q":
	sys.exit(0)
    else:
	print "Command Error ! Select only one letter below !"

def init():
    print
    print "**************************************************************"
    print "*                                                            *"
    print "*                 Pair Plugwise On Linux                     *"
    print "*              http://hackstuces.blogspot.com                *"
    print "*              contact : hackstuces@gmail.com                *"
    print "*                                                            *"
    print "*              Francisco Zamora-Martinez (2015)              *"
    print "*    francisco (dot) zamora (at) uch (dot) ceu (dot) es      *"
    print "*                                                            *"
    print "**************************************************************"
    print
	
init()
while True: main()
