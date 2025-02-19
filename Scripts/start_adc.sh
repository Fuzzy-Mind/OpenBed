echo mcp3421 0x69 > /sys/bus/i2c/devices/i2c-1/new_device
sleep 1

echo 15 > /sys/bus/iio/devices/iio\:device0/in_voltage_sampling_frequency
