'''
Created on 27 Jul 2017
@author: muth
'''

import smbus

bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

DEVICE_ADDRESS = 0x04      #7 bit address (will be left shifted to add the read write bit)
received = 0x00

received = bus.read_byte(DEVICE_ADDRESS)
print(received)

received = bus.read_word_data(DEVICE_ADDRESS, 0)
print(received)

block = bus.read_i2c_block_data(04, 0, 16) # Returned value is a list of 16 bytes
print(block)
