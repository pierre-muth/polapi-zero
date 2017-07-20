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
from PIL import ImageDraw
from PIL import ImageFont
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
    def __init__(self):
        self.size = 0

    def write(self, s):
        global lcd
        
        b1 = bytearray()
        b1.extend(s[:(P_WIDTH*P_HEIGHT)])
        
        mi = min(b1)
        ma = max(b1)
        ra = ma-mi
        b2 = bytearray()
        
        for pix in range(P_WIDTH*P_HEIGHT):
            b2.append( (b1[pix]*(255/ra))-mi )
        
        print(max(b1), min(b1), max(b2), min(b2))
        
        image = Image.frombuffer('L', P_SIZE, b2, "raw", 'L', 0, 1)
        image.thumbnail(S_SIZE, Image.NEAREST)
        
#         draw = ImageDraw.Draw(image)
#         font = ImageFont.truetype('arial.ttf', 18)
#         
#         draw.rectangle([(0, 0), (115, 22)], fill=255, outline=0)
#         draw.text((2, 2), "TESt *", fill='black', font=font)
        
        image = ImageOps.invert(image)
        image = image.convert('1')
        lcd.write(image.tobytes())
        
lcd = SMemLCD('/dev/spidev0.0')

with picamera.PiCamera() as camera:
    camera.rotation = 180
    camera.resolution = P_SIZE
    camera.framerate = 2
    camera.start_preview()
    camera.start_recording(MyOutput(), format='yuv', resize=P_SIZE)
    sleep(10)
    camera.stop_recording()
    sleep(1)