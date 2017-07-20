'''
Created on 24 Jan 2017
@author: muth    
'''
import os
import RPi.GPIO as GPIO
from time import sleep
from PIL import Image
from PIL import ImageOps
from PIL import ImageEnhance
from smemlcd import SMemLCD
from picamera import PiCamera
from io import BytesIO
from Adafruit_Thermal import *

S_WIDTH = 400
S_HEIGHT = 240
S_SIZE = (S_WIDTH, S_HEIGHT)
F_WIDTH = 2400
F_HEIGHT = 1440
F_SIZE = (S_WIDTH, S_HEIGHT)
P_WIDTH = 640
P_HEIGHT = 384
P_SIZE = (S_WIDTH, S_HEIGHT)

lcd = SMemLCD('/dev/spidev0.0')

SHOT_PIN = 16
PRINT_PIN = 15
NEXT_PIN = 13
PREV_PIN = 11

isShot = False
currentFileNumber = -1

# GPIO setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(SHOT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PRINT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(NEXT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PREV_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# add edge detection on a channel
GPIO.add_event_detect(SHOT_PIN, GPIO.FALLING, bouncetime=250)  
GPIO.add_event_detect(PRINT_PIN, GPIO.FALLING, bouncetime=250)  
GPIO.add_event_detect(NEXT_PIN, GPIO.FALLING, bouncetime=250)  
GPIO.add_event_detect(PREV_PIN, GPIO.FALLING, bouncetime=250)  

# Create camer and in-memory stream
stream = BytesIO()
camera = PiCamera()
camera.resolution = (P_WIDTH, P_HEIGHT)
camera.framerate = 6
camera.contrast = 50
camera.start_preview()
sleep(1)

def displayImageFileOnLCD(filename):
    print 'displays ', filename
    # resize/dither to screen resolution and send to LCD
    image = Image.open(filename)
    im_width, im_height = image.size
    if im_width < im_height:
        image = image.rotate(90)
    image.thumbnail(S_SIZE, Image.ANTIALIAS)
    image_sized = Image.new('RGB', S_SIZE, (0, 0, 0))
    image_sized.paste(image,((S_SIZE[0] - image.size[0]) / 2, (S_SIZE[1] - image.size[1]) / 2))
    image_sized = ImageOps.invert(image_sized)
    image_sized = image_sized.convert('1') # convert image to black and white
    
    lcd.write(image_sized.tobytes())
    
def printImageFile(filename):
    print 'prints ', filename
    # resize/dither to printer resolution and send to printer
    
def saveImageToFile(image, filename):
    print 'saves image ', filename
    image.save(filename)
#     fh = open(filename, 'w')
#     fh.close()
    # save full res image
    
#Main loop
while True:
    stream.seek(0)

    # View Loop
    for foo in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
        stream.seek(0) # "Rewind" the stream to the beginning so we can read its content
        image_source = Image.open(stream)
        imageResized = image_source.resize((S_WIDTH, S_HEIGHT), Image.NEAREST)
        imageEnancer = ImageEnhance.Contrast(imageResized)
        imageContrasted = imageEnancer.enhance(2)
        imageInverted = ImageOps.invert(imageContrasted)
        imagedithered = imageInverted.convert('1') # convert image to black or white
        
        lcd.write(imagedithered.tobytes())
        
        stream.seek(0)
        
        if GPIO.event_detected(SHOT_PIN):
            isShot = True
            break
        if GPIO.event_detected(PRINT_PIN):
            break
    
    # Do we shot ?
    if isShot:
        # Increment file number
        i = 1
        while os.path.exists("pz%05d.jpg" % i):
            i += 1
        currentFileNumber = i
        
        # save last to a jpeg file
        saveImageToFile(image_source, "pz%05d.jpg" % currentFileNumber)
        isShot = False
        
    # Is current file number set yet ?
    elif currentFileNumber == -1 :
        i = 0
        while True:
            if os.path.exists("pz%05d.jpg" % (i+1)):
                i += 1
            else :
                break
        currentFileNumber = i
    
    # Display current image
    displayImageFileOnLCD("pz%05d.jpg" % currentFileNumber)
    
    # Review Loop
    while True:
        sleep(0.25)
        if GPIO.event_detected(NEXT_PIN):
            # Increment current file name and display it
            if os.path.exists("pz%05d.jpg" % (currentFileNumber+1)):
                currentFileNumber += 1
            displayImageFileOnLCD("pz%05d.jpg" % currentFileNumber)
        if GPIO.event_detected(PREV_PIN):
            # Decrement current file name and display it
            if os.path.exists("pz%05d.jpg" % (currentFileNumber-1)):
                currentFileNumber -= 1
            displayImageFileOnLCD("pz%05d.jpg" % currentFileNumber)
        if GPIO.event_detected(PRINT_PIN):
            # Print current file
            printImageFile("pz%05d.jpg" % currentFileNumber)
        if GPIO.event_detected(SHOT_PIN):
            # Exit review
            break
            
print("Main loop has exited")


