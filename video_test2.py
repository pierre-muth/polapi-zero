'''
Created on Jan 13, 2017
@author: muth
'''
from __future__ import print_function
from io import BytesIO
from time import sleep
import picamera
from PIL import Image
from PIL import ImageOps
from io import BytesIO
from smemlcd import SMemLCD
from time import sleep
import time

S_WIDTH = 400
S_HEIGHT = 240
S_SIZE = (S_WIDTH, S_HEIGHT)
P_WIDTH = 640
P_HEIGHT = 384
P_SIZE = (P_WIDTH, P_HEIGHT)

class MyOutput(object):
    image_scan = Image.new('L', S_SIZE, 0)
    def __init__(self):
        self.size = 0
        self.x = 0
    def write(self, s):
        global lcd
        self.size += len(s)
        image = Image.frombuffer('L', (416, 240), s, "raw", 'L', 0, 1)
        image = image.crop((self.x, 0, self.x+1, S_HEIGHT))
        self.image_scan.paste(image,(self.x,0))
        self.x += 1
        if self.x >= S_WIDTH:
            self.x = 0
        image = ImageOps.invert(self.image_scan)
        image = image.convert('1')
        lcd.write(image.tobytes())

    def flush(self):
        print('%d bytes total' % self.size) 
        
lcd = SMemLCD('/dev/spidev0.0')

with picamera.PiCamera() as camera:
    camera.rotation = 180
    camera.resolution = P_SIZE
    camera.framerate = 24
    camera.start_preview()
    camera.start_recording(MyOutput(), format='yuv', resize=(416, 240))
    sleep(18)
    t1 = time.time()
    MyOutput.image_scan.save('test_video.jpg')
    print('time: %f' % (time.time()-t1) )
    camera.stop_recording()
