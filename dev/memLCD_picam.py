'''
Created on Jan 13, 2017

@author: pfreyerm
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

GPIO.setmode(GPIO.BOARD)
GPIO.setup(22, GPIO.OUT, initial=GPIO.LOW)

WIDTH, HEIGHT = 400, 240

# Create the in-memory stream
stream = BytesIO()
camera = PiCamera()
camera.resolution = (864, 576)
camera.start_preview()
camera.contrast = 25
time.sleep(2)

lcd = SMemLCD('/dev/spidev0.0')

for i in range(100, -1, -1):
    t1 = time.time()
    
    camera.capture(stream, format='jpeg', use_video_port=True, resize=(WIDTH, HEIGHT))
    stream.seek(0) # "Rewind" the stream to the beginning so we can read its content
    image = Image.open(stream)
    image = image.convert('L') # convert image to black and white
    image = PIL.ImageOps.invert(image)
    image = image.convert('1') # convert image to black and white
    GPIO.output(22, 1)
    lcd.write(image.tobytes())
    GPIO.output(22, 0)
    stream.seek(0) # "Rewind" the stream to the beginning so we can read its content
    
    print('lcd writing time: %f' % (round(time.time() - t1, 4)) )

GPIO.cleanup()


if __name__ == '__main__':
    pass