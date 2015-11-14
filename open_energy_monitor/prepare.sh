#!/bin/bash
if [[ ! -e rpi-serial-console ]]; then
    wget https://raw.github.com/lurch/rpi-serial-console/master/rpi-serial-console
    chmod +x rpi-serial-console
fi
sudo ./rpi-serial-console disable
echo "Remember, this software needs to reboot raspimon"
