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

#Screen resolution
WIDTH, HEIGHT = 400, 240

# Camera setup and in-memory stream
stream = BytesIO()
camera = PiCamera()
camera.resolution = (640, 384)
camera.framerate = 6

#setup memory LCS
lcd = SMemLCD('/dev/spidev0.0')

# GPIO setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(7, GPIO.RISING)  # add rising edge detection on a channel

try:

    for foo in camera.capture_continuous(stream, format='jpeg', use_video_port=True, resize=(WIDTH, HEIGHT)):
        stream.seek(0) # "Rewind" the stream to the beginning so we can read its content

        image_source = Image.open(stream)
        imageEnancer = ImageEnhance.Contrast(image_source)
        imageContrasted = imageEnancer.enhance(2)
        imageInverted = PIL.ImageOps.invert(imageContrasted)
        imagedithered = imageInverted.convert('1') # convert image to black or white
        
        lcd.write(imagedithered.tobytes())
        
        stream.seek(0)
        
        if GPIO.event_detected(7):
            print('Button pressed')
            break
    
    camera.capture(stream, format='jpeg', use_video_port=True)
    stream.seek(0) # "Rewind" the stream to the beginning so we can read its content
    image_source = Image.open(stream)
    imageResized = image_source.resize((WIDTH, HEIGHT), Image.ANTIALIAS)
    imageEnancer = ImageEnhance.Contrast(imageResized)
    imageContrasted = imageEnancer.enhance(2)
    imageInverted = PIL.ImageOps.invert(imageContrasted)
    imagedithered = imageInverted.convert('1') # convert image to black or white
    
    lcd.write(imagedithered.tobytes())
    
    stream.seek(0) # "Rewind" the stream to the beginning so we can read its content
    
    imageRotated = image_source.rotate(90)
    printer = Adafruit_Thermal("/dev/ttyAMA0", 115200, timeout=0, rtscts=True)
    printer.printImage(imageRotated, False)
    printer.feed(3)

finally:
    GPIO.cleanup()
    camera.close()

if __name__ == '__main__':
    pass
