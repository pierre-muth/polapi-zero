'''
Created on 24 Jan 2017
@author: muth    
'''
import os
import RPi.GPIO as GPIO
import threading
from Adafruit_Thermal import *
from time import sleep
from PIL import Image
from PIL import ImageOps
from PIL import ImageEnhance
from PIL import ImageDraw
from PIL import ImageFont
from smemlcd import SMemLCD
from picamera import PiCamera
from io import BytesIO

# Constants
S_WIDTH = 400
S_HEIGHT = 240
S_SIZE = (S_WIDTH, S_HEIGHT)
P_WIDTH = 640
P_HEIGHT = 384
P_SIZE = (P_WIDTH, P_HEIGHT)
F_WIDTH = 1280
F_HEIGHT = 768
F_SIZE = (F_WIDTH, F_HEIGHT)

SHOT_PIN = 16
PRINT_PIN = 15
NEXT_PIN = 13
PREV_PIN = 11

# Thread using the image full resolution
class CameraThread(threading.Thread):
    takeAshot = False
    stream2 = BytesIO()
        
    def __init__(self):
        threading.Thread.__init__(self)
        self.event = threading.Event()

    def run(self):
        global currentFileNumber
        for bug in camera.capture_continuous(self.stream2, format='jpeg', use_video_port=True, splitter_port=0):
            self.stream2.seek(0) # "Rewind" the stream to the beginning so we can read its content
            
            if self.takeAshot:
                image = Image.open(self.stream2)
                
                # Increment file number    
                i = 1
                while os.path.exists("pz%05d.jpg" % i):
                    i += 1
                currentFileNumber = i
#              
                # Save last to a jpeg file
                saveImageToFile(image, "pz%05d.jpg" % currentFileNumber)
                
                self.takeAshot = False
                break
            
# Variables
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

# Create Sharp mempry LCD
lcd = SMemLCD('/dev/spidev0.0')

# Create Printer
printer = Adafruit_Thermal("/dev/ttyAMA0", 115200, timeout=0, rtscts=True)

# Create camera and in-memory stream
stream = BytesIO()
camera = PiCamera()
camera.resolution = (F_WIDTH, F_HEIGHT)
camera.framerate = 8
camera.contrast = 50
camera.start_preview()
sleep(1)

def displayImageFileOnLCD(filename):
    print 'displays ', filename
    title = 'Review Mode'
    # resize/dither to screen resolution and send to LCD
    image = Image.open(filename)
    im_width, im_height = image.size
    if im_width < im_height:
        image = image.rotate(90)
    image.thumbnail(S_SIZE, Image.ANTIALIAS)
    image_sized = Image.new('RGB', S_SIZE, (0, 0, 0))
    image_sized.paste(image,((S_SIZE[0] - image.size[0]) / 2, (S_SIZE[1] - image.size[1]) / 2))
    # draw filename
    draw = ImageDraw.Draw(image_sized)
    font = ImageFont.truetype('arial.ttf', 18)
    draw.rectangle([(0, 0), (115, 22)], fill=(255,255,255), outline=(0,0,0))
    draw.text((2, 2), title, fill='black', font=font)
    draw.rectangle([(279, 217), (399, 239)], fill=(255,255,255), outline=(0,0,0))
    draw.text((290, 218), filename, fill='black', font=font)
    # display on LCD
    image_sized = ImageOps.invert(image_sized)
    image_sized = image_sized.convert('1') # convert image to black and white
    lcd.write(image_sized.tobytes())
    
def printImageFile(filename):
    print 'prints ', filename
    # resize to printer resolution and send to printer
    image = Image.open(filename)
    im_width, im_height = image.size
    if im_width > im_height:
        image = image.rotate(90)
    image.thumbnail((P_HEIGHT, P_WIDTH), Image.ANTIALIAS)
    printer.printImage(image, False)
    printer.feed(3)
    
def saveImageToFile(image, filename):
    print 'saves image ', filename
    # save full image
    image.save(filename)
    
#Main loop
while True:
    # Start a Printer resolution camera Thread to minimize shot delay
    cameraThreadForPrint = CameraThread()
    cameraThreadForPrint.start()

    # View Loop
    stream.seek(0)
    for foo in camera.capture_continuous(stream, format='jpeg', use_video_port=True, resize=(S_WIDTH, S_HEIGHT), splitter_port=1):
        t1 = time.time()
        stream.seek(0) # "Rewind" the stream to the beginning so we can read its content
        image_source = Image.open(stream)
        imageInverted = ImageOps.invert(image_source)
        
        # convert image to black or white and send to LCD
        lcd.write(imageInverted.convert('1').tobytes())
        stream.seek(0)
        print('capture and display time: %f' % (time.time() - t1))
        
        if GPIO.event_detected(SHOT_PIN):
            cameraThreadForPrint.takeAshot = True
            break
        if GPIO.event_detected(PRINT_PIN):
            break
    
    # Wait the picture is taken
    cameraThreadForPrint.join(5)
        
    # Set current file number if not set yet
    if currentFileNumber == -1 :
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


