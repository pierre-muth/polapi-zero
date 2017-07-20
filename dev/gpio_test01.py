'''
Created on Jan 23, 2017

@author: pfreyerm
'''

import time
import RPi.GPIO as GPIO

# GPIO setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(22, GPIO.RISING)  # add rising edge detection on a channel


for i in range(0, 30):
    time.sleep(1)
    print(i)
    if GPIO.event_detected(22):
        break
    
print('Button pressed')


if __name__ == '__main__':
    pass