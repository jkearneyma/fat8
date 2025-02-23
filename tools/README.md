# Tools for programming and testing fat8

## usb-config.py

Programs the MCP2221A for its role on fat8:
- provides 3 MHz clock
- provides 2 sticky configuration bits to control the mapping of the FRAM (32KB) to the CPU address space (16KB)

```
# you will need to unload and possibly blacklist this kernel module
# in newer Linux versions because it sets up the USB interface for I2C:
sudo rmmod hid_mcp2221
# Then configure the device, unplug and plug:
sudo ./usb-config.py [-cfg0] [-cfg1]
```

## emulator.py

Software emulation of the board - reads a .hex file and executes it.  Character I/O is intercepted, and write-protects (port 1/11) are emulated.

## atf1504_program.tcl

openocd script to program the CPLD using JTAG by uploading cpld/fat8.svf.  Sample command line:
openocd -f <jtag adapter>.cfg -f atf1504_program.tcl

## fram-programmer.py

Translate an Intel hex file to JTAG a boundary scan command file which writes the contents into the FRAM by wiggling the CPLD's pins.  Used in software/ to prepare code for upload

## fm1808_program.tcl and fm1808_verify.tcl

openocd scripts to execute software/image.svf and software/verify.svf
