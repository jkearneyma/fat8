# fat8 Hardware

The hardware is physically quite minimal but is still "discrete" in the sense that the 8008 CPU is supported by gate-level logic and an actual memory IC, not a microcontroller or FPGA pretending to be logic or memory.  The highest integration chip is actually the USB interface, which is actually an embedded PIC processor.  The only thing that device does is provide a clock signal and a TTL serial connection, however.

The memory IC is a ferro-magnetic RAM (FRAM), which is nonvolatile yet fast so it serves as both RAM and ROM in the design.

The "gate-level logic" is built in a programmable logic device.  It's relatively small (64 logic blocks), but that's big enough to implement the ~25 latches and 40+ gates needed to do all the state decoding, bus demultiplexing and other functions necessary.  The device is the (ex)Atmel ATF1504 CPLD.  It is old enough to have 5V I/O but new enough to be in-circuit (re)programmable using JTAG. Futhermore, it supports JTAG boundary scan, which allows us to download data into the FRAM by wiggling the I/O lines connected to it, which solves the bootstrap problem.

The [cpld/](../cpld/) folder contains the logic description for the CPLD, and the [tools/](../tools/) folder has the utilities needed to program the various devices.

The 8008 is a PMOS design, and requires a -9V supply (actually it requires a 14V supply and its logic signals are 9V-14V).  A small isolated DC-DC converter takes care of this.

This folder contains the schematic and board (Work In Progress) created in Kicad 9.