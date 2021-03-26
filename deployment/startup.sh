#!/bin/bash

# new persmission to usb printer
FILE = "/etc/udev/rules.d/00-usb-persmissions.rules"
touch $FILE
echo "1 SUBSYSTEM=="usb", ATTRS{idVendor}=="0dd4", ATTRS{idProduct}=="015d", MODE="0664", GROUP="dialout" > $FILE
