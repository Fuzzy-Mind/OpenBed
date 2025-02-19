modprobe rtc-ds1307
echo mcp7941x 0x6f > /sys/bus/i2c/devices/i2c-1/new_device
hwclock --localtime --hctosys
