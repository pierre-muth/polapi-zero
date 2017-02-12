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
P_WIDTH = S_WIDTH*2
P_HEIGHT = S_HEIGHT*2
P_SIZE = (P_WIDTH, P_HEIGHT)

class MyOutput(object):
    def __init__(self):
        self.image_scan = Image.new('L', P_SIZE, 0)
        self.x = 0
    def write(self, s):
        global lcd
        image = Image.frombuffer('L', P_SIZE, s, "raw", 'L', 0, 1)
        image = image.crop((self.x, 0, self.x+1, P_HEIGHT))
        self.image_scan.paste(image,(self.x, 0))
        if self.x < P_WIDTH-1:
            self.x += 1
        image = ImageOps.invert(self.image_scan)
        image.thumbnail(S_SIZE, Image.NEAREST)
        image = image.convert('1')
        lcd.write(image.tobytes())

lcd = SMemLCD('/dev/spidev0.0')

with picamera.PiCamera() as camera:
    camera.rotation = 180
    camera.resolution = P_SIZE
    camera.framerate = 20
    camera.start_preview()
    myoutput = MyOutput()
    camera.start_recording(myoutput, format='yuv')
    xprev = 0
    while myoutput.x < P_WIDTH -1:
        print(myoutput.x - xprev)
        xprev = myoutput.x
        sleep(1)
    camera.stop_recording()
    t1 = time.time()
    myoutput.image_scan.save('test_video.jpg')
    print('time: %f' % (time.time()-t1) )
