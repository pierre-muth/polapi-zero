'''
Created on Jan 13, 2017
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
camera.resolution = (640, 384)
#camera.start_preview()
camera.framerate = 5
time.sleep(2)

lcd = SMemLCD('/dev/spidev0.0')

try:
    t1 = time.time()
    t2 = time.time()
    for foo in camera.capture_continuous(stream, format='jpeg', use_video_port=True, resize=(WIDTH, HEIGHT)):
        t2 = time.time()
        stream.seek(0) # "Rewind" the stream to the beginning so we can read its content
        image_source = Image.open(stream)
        imageEnancer = ImageEnhance.Contrast(image_source)
        imageContrasted = imageEnancer.enhance(2)
        imageInverted = PIL.ImageOps.invert(imageContrasted)
        imagedithered = imageInverted.convert('1') # convert image to black or white
        
#        GPIO.output(22, 1)
        lcd.write(imagedithered.tobytes())
#        GPIO.output(22, 0)
        
        stream.seek(0)
        
        print('loop time: %f, process time %f' % (time.time() - t1, time.time() - t2))
        t1 = time.time()
finally:
    GPIO.cleanup()
    camera.close()

if __name__ == '__main__':
    pass
