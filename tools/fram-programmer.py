#! /usr/bin/python3

"""
Convert an i8008 binary file to openocd JTAG commands that will
bit-bang the contents to the fat8 "core" memory

IMPORTANT
The 8008 must not be installed when this is done

N.b. this is specific to the ATF1504AS in 100-pin TQFP package type
and the FM1808 connections in the fat8 schematic.
"""

import sys, argparse
from bitstring import options, Bits, BitArray
from intelhex import IntelHex

# BSDL bit order
options.lsb0 = True

# Mapping of memory pins to ATF1504AS TQFP100 CPLD
# format is name:[pin,in_cell,control_cell,out_cell]
# n.b. the lists below are derived from this table and
# must be updated if there are changes here.
fm1808 = {
    "D0" : [  8, 52, 170, 171],
    "D1" : [100, 54, 176, 177],
    "D2" : [ 98, 56, 180, 181],
    "D3" : [ 96, 58, 184, 185],
    "D4" : [ 93, 60, 188, 189],
    "D5" : [ 84,  3,  66,  67],
    "D6" : [ 81,  5,  70,  71],
    "D7" : [ 79,  7,  74,  75],
    "A0" : [ 68, 12,  86,  87],
    "A1" : [ 67, 13,  88,  89],
    "A2" : [ 65, 14,  90,  91],
    "A3" : [ 64, 15,  92,  93],
    "A4" : [ 63, 16,  94,  95],
    "A5" : [ 61, 17,  98,  99],
    "A6" : [ 60, 18, 100, 101],
    "A7" : [ 58, 19, 102, 103],
    "A8" : [ 48, 24, 112, 113],
    "A9" : [ 47, 25, 114, 115],
    "A10": [ 44, 28, 120, 121],
    "A11": [ 46, 26, 116, 117],
    "A12": [ 57, 20, 104, 105],
    "A13": [ 52, 23, 110, 111],
    "A14": [ 56, 21, 106, 107],
    "CE/": [ 42, 29, 122, 123],
    "OE/": [ 45, 27, 118, 119],
    "WR/": [ 54, 22, 108, 109]
}

def dump(bitz):
    for k in fm1808:
        print(f"!{fm1808[k][0]:3d} {k:3s}:", end='')
        if bitz[fm1808[k][2]]:
            print("OUT", "1" if bitz[fm1808[k][3]] else "0")
        else:
            print("IN ", "1" if bitz[fm1808[k][1]] else "0")

dump(Bits('0x40a2a255940000000dd575565566b8bac000101ee8400112'))


# Cell lists for the FM1808 device, in LSb order
# _rd = input cells, _dir = control cells, _wr = output cells

# D0-7
data_rd  = [52, 54, 56, 58, 60, 3, 5, 7]
data_dir = [170, 176, 180, 184, 188, 66, 70, 74]
data_wr  = [171, 177, 181, 185, 189, 67, 71, 75]

# A0-14
addr_wr  = [87, 89, 91, 93, 95, 99, 101, 103, 113, 115, 121, 117, 105, 111, 107]

# control signals
ce_wr = [123]
oe_wr = [119]
we_wr = [109]

parser = argparse.ArgumentParser(
    description='generate openocd JTAG script to bit-bang Intel hex files into fat8 memory',
    epilog='')
parser.add_argument('ihex_file', action="extend", nargs="+", type=str, help='Intel Hex file')
parser.add_argument('--verify', action="store_true", help='verify only')
args = parser.parse_args()

# set all FM180 connections to output
bs = BitArray(bin='0')*192
for k in fm1808:
    bs.set(True, fm1808[k][2])

# set FM1808 selects to inactive
# @todo should there be a weak pullup on WE/ ?
bs.set(True, ce_wr + oe_wr + we_wr)

# create a read data mask and expected read data
expected = BitArray(bin='0')*192
rd_mask = BitArray(bin='0')*192
rd_mask.set(True, data_rd)

# prolog
print("""
TRST ABSENT;
ENDIR IDLE;
ENDDR IDLE;
RUNTEST 5E-2 SEC;
STATE RESET;
STATE IDLE;
SIR 10 TDI (059);
! check device type
SDR 32 TDI (ffffffff) TDO (0150403f) MASK (ffffffff);
STATE IDLE;
SIR 10 TDI (000);""")

def set_all(bitz, value, positions):
    bitz.set(value != 0, positions)

def set_value(bitz, value, positions):
    for b in positions:
        bitz.set(1 == (value & 1), b)
        value >>= 1

def upd_pins(extra=''):
    #dump(bs)
    print("SDR 192 TDI (", bs.hex, f"){extra};", sep='',)

for fn in args.ihex_file:
    fd = IntelHex(fn)
    if not args.verify:
        # write
        bs.set(True, data_dir)
        for addr in fd.addresses():
            print(f"! {addr:04x} write {fd[addr]:02x}")
            # set up addr and data
            set_value(bs, addr, addr_wr)
            set_value(bs, fd[addr], data_wr)
            upd_pins()
            # pulse enable+write
            set_all(bs, 0, ce_wr + we_wr)
            upd_pins()
            set_all(bs, 1, ce_wr + we_wr)
            upd_pins()
    # read/verify
    bs.set(False, data_dir)
    for addr in fd.addresses():
        print(f"! {addr:04x} expect {fd[addr]:02x}")
        set_value(bs, addr, addr_wr)
        upd_pins()
        # pulse enable+read
        set_all(bs, 0, ce_wr + oe_wr)
        upd_pins()
        # a delay might be needed here if jtag clock is high freq
        set_value(expected, fd[addr], data_rd)
        upd_pins(" TDO(" + expected.hex + ") MASK(" + rd_mask.hex + ")")
        set_all(bs, 1, ce_wr + oe_wr)
        upd_pins()


print("!end")
upd_pins()

