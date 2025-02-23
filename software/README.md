# Software

This project is built under Linux, except for the vintage CPLD tools which were published on Windows.  It is probably possible to run the Windows tools under WINE, or the assembler and Python tools on Windows, but those paths are not documented here.

## Tools required

* [Macroassembler AS](http://john.ccac.rwth-aachen.de:8000/as/), which can be more conveniently built on Linux using [this repository](https://github.com/Macroassembler-AS/asl-releases)
* Python 3 with intelhex, bitstring, and hid modules installed
* Software in [tools/](../tools/) directory of this project

## monitor.asm

Simple terminal-oriented monitor.  No real debugging ability, just
display and modification of bytes in memory, start execution
somewhere, and do byte I/O.

| Commands: | |
| :---- | :---- |
| P aa:aaa | print 8 bytes, Enter/Esc |
| E aa:aaa | enter bytes until Esc |
| J aa:aaa | jump to address |
| I p | input from port p |
| O p ddd | output to port 1p |
| S | start SCELBAL (jump to 06:000) |
| :<data> | Intel hex loader (Work In Progress) |

Note that memory addresses in the monitor are in "split
octal" form.  It's a bit different from hexadecimal
(literally) because the high-order address byte has 2
digits and the low-order byte has 2 2/3 digits. '2/3'
of a digit means it only ranges from 0 to 3.

FRAM Memory is non-volatile, thus there is no RAM or ROM
distinction.  However there are some memory controls:

### Write Protection
I/O port 1 is a byte register where each bit protects a 2KB area; the least
significant bit protects the first 2KB and so on.

### Memory Banks
The FRAM is 32KB but the 8008 can address only 16KB.  The USB interface
stores two configuration bits in its nonvolatile settings that switch
each 8KB half between two alternates.  The usb-config.py program has
command-line options to set these.

Because the monitor + SCELBAL image is closer to 10KB, these are best used
in tandem to switch between two complete memory images.

### Memory Map

| Write protected at power-up: |
| :----- |
| 00:000-05:377 : Monitor |
| 06:000-37:377 : SCELBAL code |

| Writable at power-up: |
| :---- |
| 40:000-77:377 : SCELBAL data and user program |

A machine-code program may be loaded in high memory and would only
interfere with SCELBAL if a very large SCELBAL program is loaded.

If a larger program area is needed, SCELBAL can be overwritten by
disabling the memory protection for all but the first 2KB containing
the monitor ('O 1 001') and then from 08:000 to 77:377 is available.

### Monitor-supplied facilities
These use the 1-byte call instruction RST *n*:

| RST instruction | Action | Uses |
| :---- | :---- | :---- |
| RST 0 | Enter monitor | *n/a* |
| RST 1 | Print zero-terminated string | ABHL |
| RST 3 | Print char in A | B |
| RST 4 | Read character to A | AB |
| RST 5 | Delay 14B+12 cycles (incl RST) | B |
| RST 6 | Reserved for future definition | |
