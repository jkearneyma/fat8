adapter speed 5000
jtag newtap ATF1504AS tap -irlen 10 -expected-id 0x0150403f
init
svf ../cpld/fat8.svf
sleep 200
shutdown
