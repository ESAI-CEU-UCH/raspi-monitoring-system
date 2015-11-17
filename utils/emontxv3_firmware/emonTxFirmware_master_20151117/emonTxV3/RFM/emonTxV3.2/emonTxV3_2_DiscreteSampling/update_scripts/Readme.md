# emonTx V3.2 Update 

Update your emonTx V3.2 to latest firmware using Raspberry Pi. 

See change log in emonTx code for version info:
https://github.com/openenergymonitor/emonTxFirmware/blob/master/emonTxV3/RFM/emonTxV3.2/emonTxV3_2_DiscreteSampling/emonTxV3_2_DiscreteSampling.ino

Plug USB to UART adatper into Raspberry Pi and emonTx: http://shop.openenergymonitor.com/programmer-usb-to-serial-uart/

![programmer_emontx](http://openenergymonitor.org/emon/sites/default/files/emontxv3_USBtoUART.jpg)

Update script assumes USB to UART programmer is linked to /dev/ttyUSB0, you can check this by running dmesg after plugging in programmer. Adjust script if different tty is used. 

	$ dmesg

Clone this repo:

	$ git clone https://github.com/openenergymonitor/emonTxFirmware.git

or if you have cloned before pull in latest updates 

	$ git pull

	$ cd /home/pi/emonTxFirmware/emonTxV3/RFM/emonTxV3.2/emonTxV3_2_DiscreteSampling/update_scripts

Run the correct update script for your emonTx RF module frequeny. All emonTx V3.2's will have RFM12B Radio
See here for help identify RF module frequency: http://openenergymonitor.org/emon/buildingblocks/which-radio-module

Run update script e.g:

	$ ./Update_emonTx_V3_2_RFM12B_433.sh

Check update has worked by viewing serial output of emonTx at statup:
Open up serial window, with minicom. Install if required

	$ sudo apt-get install minicom -y

	$ minicom -D /dev/ttyUSB0 -b 6900
