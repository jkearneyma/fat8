#! /usr/bin/python3

"""
Configure the MCP2221A with the fat8 configuration
"""

import argparse
import atexit
import time
import hid

VID = 0x04d8
PID = 0x00dd

MCP2221_HID_DELAY = float(0)

# if the device can't be opened, it's one of these:
# 1. not connected or device has different ID (lsusb)
# 2. i2c driver loaded (sudo rmmod hid_mcp2221)
# 3. no permissions (sudo chmod a+rw /dev/hidrawXXX, where XXX is most recent)

# Chip Settings: clock output 6MHz, power 400 mA
# @TODO get our own VID:PID
conf0 = [ 0xb1, 0x00, 0x7c, 0x13, 0x88, 0x6f, 0xd8, 0x04, 0xdd, 0x00, 0x80, 0xc8 ]
# GP Settings: GP0 = LED_URx, GP1 = clock out, GP2 = output init=0, GP3 = output init=0
conf1 = [ 0xb1, 0x01, 0x01, 0x01, 0x00, 0x00 ]
# Manufacturer Description: "kearney.dev"
conf2 = [ 0xb1, 0x02, 24, 0x03, 0x6b, 0, 0x65, 0, 0x61, 0, 0x72, 0, 0x6e, 0, 0x65, 0, 0x79, 0, 0x2e, 0, 0x64, 0, 0x65, 0, 0x76, 0 ]
# Product Description: "fat8"
conf3 = [ 0xb1, 0x03, 10, 0x03, 0x66, 0, 0x61, 0, 0x74, 0, 0x38, 0 ]

parser = argparse.ArgumentParser(
    description='configure USB interface on fat8',
    epilog='')
parser.add_argument('--cfg0', action="store_true", help='set cfg0 = 1')
parser.add_argument('--cfg1', action="store_true", help='set cfg1 = 1')
args = parser.parse_args()

if args.cfg0:
    conf1[4] |= 0x10
if args.cfg1:
    conf1[5] |= 0x10

dev = hid.device()

dev.open(VID, PID)
atexit.register(dev.close)

def dev_xfer(report, response=True):
    dev.write(report + b"\0" * (64 - len(report)))
    time.sleep(MCP2221_HID_DELAY)
    if response:
        return dev.read(64)
    return None

def print_config(register):
    report = dev_xfer(register)
    print('[', ', '.join('0x{:02x}'.format(x) for x in report), ']')
    return report

print("--- Write Chip Settings ---")
dev_xfer(bytes(conf0))
print_config(b"\xb0\x00")
print("--- Write GP Settings ---")
dev_xfer(bytes(conf1))
print_config(b"\xb0\x01")
print("--- Write Manufacturer Descriptor ---")
dev_xfer(bytes(conf2))
print_config(b"\xb0\x02")
print("--- Write Product Discriptor ---")
dev_xfer(bytes(conf3))
print_config(b"\xb0\x03")
