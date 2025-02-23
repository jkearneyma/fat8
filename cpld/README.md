# CPLD logic

Note: this project is built under Linux, except for the vintage CPLD tools which were published on Windows.  I'm running the Windows programs in a Gnome Boxes VM with Windows 7 installed, but bare-metal Windows or any other VM manager will work.  It is probably possible to run the Windows tools under WINE but that isn't tested or documented by me.  

The CPLD implements all the random logic for fat8.  This is primarily fundamental 8008 stuff like clock generation, state decoding, address demultiplexing, and I/O decoding.  In addition, it exposes the USB Rx/Tx to the CPU data bus as an I/O port, and implements an FRAM write protect register with 2KB resolution as another I/O register.

If you're not changing anything, you don't need to do anything below; the output files are provided.

## fat8.pld

The complete implementation.  The CPLD is the AFT1504AS, which is one of the few 5V CPLDs still available.  Atmel built it, and was acquired later by MicroChip: https://www.microchip.com/en-us/product/ATF1504AS

## fat8.jed

The output of the logic compiler in JEDEC format.

The logic compiler used is WinCUPL.  It may be downloaded from https://www.microchip.com/en-us/products/fpgas-and-plds/spld-cplds/pld-design-resources

After compilation of fat8.pld, various output files are produced, the most important one being fat8.jed and secondly fat8.fit which documents the resulting hardware.

## fat8.svf

If one happens to have a ATDH1150USB programming cable, the fat8.jed file can be directly downloaded using ATMISP from the above web page.  You will need an adapter from one of its connectors (see page 6 of [its user manual](https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-8909-CPLD-ATDH1150USB-ATF15-JTAG-ISP-Download-Cable-UserGuide.pdf)) to the more common [Arm Coresight JTAG](https://developer.arm.com/documentation/101761/1-0/Target-interface-connectors/CoreSight-10-connector) connector, which is 10 pins on 0.05" spacing.

If not, it can be converted into a .svf file that openocd or other JTAG tools support, using ATMISP.

Create a new project in ATMISP with one device, then select a device of ATF1504AS, JTAG instruction of Program/Verify, and the fat8.jed file. After clicking OK, check the Write SVF File box and enter fat8.svf into the destination, then click the Run button.

## Using openocd and one of its supported JTAG probes

Make sure that you have the appropriate JTAG connector or adapter for your device to a [Arm Coresight JTAG](https://developer.arm.com/documentation/101761/1-0/Target-interface-connectors/CoreSight-10-connector) connector.  Your programmer must be capable of 5V operation.

Scripts are provided under [tools](../tools/) to play the SVF file.  Typical usage would be:
````
openocd -f interface/ftdi/olimex-arm-usb-ocd-h.cfg -f ../tools/atf1504_program.tcl
````
If you have an Olimex ARM-USB-TINY-H with ARM-JTAG-20-10 adapter.

Any JTAG adapter + software capable of 5V operation and playing an SVF file should work, for example there are numerous inexpensive designs using FTDI chips.

## Extreme measures

It's apparently possible that the CPLD is in a state where it won't accept programming without extra work.

First, according to the some manufacturer notes, it may be necessary to stop input clocks during programming.  I've not seen this, but there is provision on the board to cut the clock trace at JP2 (and later jumper it).

Second, for some devices, [it may be necessary to apply 12V to the OE1 pin to enable programming](https://www.hackup.net/2020/01/erasing-and-programming-the-atf1504-cpld/).  There is a cuttable jumper at JP1 for this purpose.