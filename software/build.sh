# translate source files to JTAG boundary scan loader

# assemble monitor and SCELBAL
asl -g map -listradix 8 -splitbyte : -L monitor
asl -g map -listradix 8 -splitbyte : -L scelbal
# generate ihex file
p2hex -F Intel monitor.p scelbal.p image.hex
# convert ihex to svf for this hardware
echo 'FRAM programming file => monitor.svf'
../tools/fram-programmer.py image.hex > image.svf
echo 'FRAM verification file => verify.svf'
../tools/fram-programmer.py --verify image.hex > verify.svf
