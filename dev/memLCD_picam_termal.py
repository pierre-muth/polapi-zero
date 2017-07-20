'''
Created on Jan 13, 2017

@author: muth
'''
import time
import spidev
import RPi.GPIO as GPIO
import PIL.ImageOps    
from PIL import Image
from PIL import ImageEnhance
from picamera import PiCamera
from io import BytesIO
from smemlcd import SMemLCD
from Adafruit_Thermal import *

GPIO.setmode(GPIO.BOARD)
GPIO.setup(22, GPIO.OUT, initial=GPIO.LOW)

WIDTH, HEIGHT = 400, 240

# Create the in-memory stream
stream = BytesIO()
camera = PiCamera()
camera.resolution = (640, 384)
camera.framerate = 8
camera.start_preview()
time.sleep(2)

lcd = SMemLCD('/dev/spidev0.0')

try:
    t1 = time.time()
    camera.capture(stream, format='jpeg', use_video_port=True)
    t2 = time.time()
    stream.seek(0) # "Rewind" the stream to the beginning so we can read its content
    image_source = Image.open(stream)
    imageResized = image_source.resize((WIDTH, HEIGHT), Image.ANTIALIAS)
    imageEnancer = ImageEnhance.Contrast(imageResized)
    imageContrasted = imageEnancer.enhance(2)
    imageInverted = PIL.ImageOps.invert(imageContrasted)
    imagedithered = imageInverted.convert('1') # convert image to black or white
    
#    GPIO.output(22, 1)
    lcd.write(imagedithered.tobytes())
#    GPIO.output(22, 0)
    
    stream.seek(0) # "Rewind" the stream to the beginning so we can read its content
    
    print('capture time: %f, process time %f' % (t1 - t2, time.time() - t2))
    t1 = time.time()
    
    imageRotated = image_source.rotate(90)
    printer = Adafruit_Thermal("/dev/ttyAMA0", 115200, timeout=0, rtscts=True)
    printer.printImage(imageRotated, False)
    printer.feed(3)

finally:
    GPIO.cleanup()
    camera.close()

if __name__ == '__main__':
    pass
