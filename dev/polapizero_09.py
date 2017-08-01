'''
Created on 24 Jan 2017
@author: muth    
'''
import os
import RPi.GPIO as GPIO
import threading
import time
import pygame
from Adafruit_Thermal import *
from time import sleep
from PIL import Image
from PIL import ImageOps
from PIL import ImageEnhance
from PIL import ImageDraw
from PIL import ImageFont
from picamera import PiCamera
from io import BytesIO
from subprocess import check_output
from symbol import except_clause


# Constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 240
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
PRINTER_WIDTH = 640
PRINTER_HEIGHT = 384
PRINTER_SIZE = (PRINTER_WIDTH, PRINTER_HEIGHT)
FILE_WIDTH = PRINTER_WIDTH*2
FILE_HEIGHT = PRINTER_HEIGHT*2
FILE_SIZE = (FILE_WIDTH, FILE_HEIGHT)
LCD_ratio = 1.0*SCREEN_WIDTH/SCREEN_HEIGHT

SHOT_PIN = 16
PRINT_PIN = 15
NEXT_PIN = 13
PREV_PIN = 11
HALT_PIN = 31
NO_SCAN = 1
SCAN_MODE = 2
SCAN_MODE_FIX = 3

class SlitScan(object):
    def __init__(self):
        self.image_scan = Image.new('L', PRINTER_SIZE, 0)
        self.x = 0
        self.mode = NO_SCAN
        self.scanDone = False
        self.lastTime = time.time()
        
    def write(self, s):
            
        if self.mode == SCAN_MODE:
            image = Image.frombuffer('L', PRINTER_SIZE, s, "raw", 'L', 0, 1)
            image = image.crop((self.x, 0, self.x+1, PRINTER_HEIGHT))
            self.image_scan.paste(image,(self.x, 0))
            
            if self.x < PRINTER_WIDTH-1:
                self.x += 1
            else:
                self.scanDone = True
                
            image = ImageOps.invert(self.image_scan)
            image.thumbnail(SCREEN_SIZE, Image.NEAREST)
            image = image.convert('1')
            
        if self.mode == SCAN_MODE_FIX:
            image = Image.frombuffer('L', PRINTER_SIZE, s, "raw", 'L', 0, 1)
            image = image.crop((PRINTER_WIDTH/2, 0, (PRINTER_WIDTH/2)+1, PRINTER_HEIGHT))
            image_total = Image.new('L', (self.x+1, PRINTER_HEIGHT), 0)
            image_total.paste(self.image_scan, (0, 0))
            image_total.paste(image,(self.x, 0))
            self.image_scan = image_total.copy()
              
            if self.x < 5000:
                self.x += 1
            else:
                self.scanDone = True
                  
            image = ImageOps.invert(self.image_scan)
            if image.size[0] > PRINTER_SIZE[0]:
                image = image.crop((image.size[0]-1 - PRINTER_SIZE[0], 0, image.size[0]-1, PRINTER_HEIGHT))
            
            image.thumbnail(SCREEN_SIZE, Image.NEAREST)
            image_sized = Image.new('L', SCREEN_SIZE, 0)
            image_sized.paste(image,(0, 0))
            image = image_sized.convert('1')

    def flush(self):
        print('Stop SlitScan') 

# Variables
currentFileNumber = -1
print check_output(['hostname', '-I'])

# pygame & splash screen
screen_size = width, height = 640, 480
backgroundColor = 255, 255, 255
screen = pygame.display.set_mode(screen_size)
pygame.mouse.set_visible(False)
screen.fill(backgroundColor)
logo = pygame.image.load("logo01.png")
previousimage = logo
screen.blit(logo, (40,95))
pygame.display.flip()
clock = pygame.time.Clock()

# GPIO setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(SHOT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PRINT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(NEXT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PREV_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(HALT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# add edge detection on a channel
GPIO.add_event_detect(SHOT_PIN, GPIO.FALLING, bouncetime=1000)  
GPIO.add_event_detect(PRINT_PIN, GPIO.FALLING, bouncetime=1000)  
GPIO.add_event_detect(NEXT_PIN, GPIO.FALLING, bouncetime=400)  
GPIO.add_event_detect(PREV_PIN, GPIO.FALLING, bouncetime=400)  
GPIO.add_event_detect(HALT_PIN, GPIO.FALLING, bouncetime=1000)  

# get IP adress
hostIP = check_output(['hostname', '-I'])

# Create Printer
printer = Adafruit_Thermal("/dev/ttyAMA0", 115200, timeout=0, rtscts=True)

# Create camera and in-memory stream
stream = BytesIO()
camera = PiCamera()
camera.rotation = 180
camera.resolution = FILE_SIZE
camera.framerate_range = (0.16666, 60)
camera.contrast = 50
camera.exposure_mode = 'night'
sleep(1)

def haltSystem():
    print 'Halt...'
    os.system("sudo halt")
    
# GPIO.add_event_detect(HALT_PIN, GPIO.FALLING, callback = haltSystem, bouncetime = 2000)

def slideImage(filename, direction):
    global previousimage
    image = pygame.image.load(filename)
    i_width = image.get_width()
    i_height = image.get_height()
    i_ratio = 1.0*i_width/i_height 
    l_height = SCREEN_HEIGHT
    l_width = SCREEN_WIDTH
    
    print 'displays ', filename
    
    if i_ratio < LCD_ratio:
        image = pygame.transform.scale( image, (int(i_width*(1.0*l_height/i_height)),  l_height) )

    else:
        image = pygame.transform.scale( image, (l_width,  int(i_height*(1.0*l_width/i_width))) )
        
    ynew = (l_height-image.get_height())/2
    yold = (l_height-previousimage.get_height())/2
    
    if direction == 1:    
        for i in range(0, l_width, 50):
            xnew = ((l_width-image.get_width())/2)+i-l_width 
            xold = ((l_width-previousimage.get_width())/2)+i
            screen.fill(backgroundColor)
            screen.blit(image, ( xnew , ynew ) )
            screen.blit(previousimage, ( xold, yold) )
            pygame.display.flip()
            clock.tick(20)
    else:
        for i in range(l_width, 0, -50):
            xnew = ((l_width-image.get_width())/2)+i
            xold = ((l_width-previousimage.get_width())/2)+i-l_width 
            screen.fill(backgroundColor)
            screen.blit(image, ( xnew , ynew ) )
            screen.blit(previousimage, ( xold, yold) )
            pygame.display.flip()
            clock.tick(20)
        
    screen.fill(backgroundColor)
    screen.blit(image, ((l_width - image.get_width())/2, (l_height-image.get_height())/2))
    pygame.display.flip()
    previousimage = image

def displayImageFileOnLCD(filename):
    print 'displays ', filename
    title = 'Review Mode'
    # resize/dither to screen resolution and send to LCD
    try:
        image = Image.open(filename)
    except IOError:
        print ("cannot identify image file", filename)
        image = Image.open('unidentified.jpg')
    im_width, im_height = image.size
    if im_width < im_height:
        image = image.rotate(90, expand=1)
    image.thumbnail(SCREEN_SIZE, Image.ANTIALIAS)
    image_sized = Image.new('RGB', SCREEN_SIZE, (0, 0, 0))
    image_sized.paste(image,((SCREEN_SIZE[0] - image.size[0]) / 2, (SCREEN_SIZE[1] - image.size[1]) / 2))
    # draw texts
    draw = ImageDraw.Draw(image_sized)
    font = ImageFont.truetype('arial.ttf', 18)
    draw.rectangle([(0, 0), (115, 22)], fill=(255,255,255), outline=(0,0,0))
    draw.text((2, 2), title, fill='black', font=font)
    draw.rectangle([(279, 217), (399, 239)], fill=(255,255,255), outline=(0,0,0))
    draw.text((290, 218), filename, fill='black', font=font)
    font = ImageFont.truetype('arial.ttf', 10)
    draw.rectangle([(300, 0), (399, 14)], fill=(255,255,255), outline=(0,0,0))
    draw.text((302, 2), hostIP, fill='black', font=font)
    # display on LCD
    image_sized = ImageOps.invert(image_sized)
    image_sized = image_sized.convert('1') # convert image to black and white
    
def printImageFile(filename):
    print 'prints ', filename
    # resize to printer resolution and send to printer
    try:
        image = Image.open(filename)
        im_width, im_height = image.size
        if im_width > im_height:
            image = image.rotate(90, expand=1)
            im_width, im_height = image.size
        ratio = (PRINTER_HEIGHT/float(im_width))
        height = int((float(im_height)*float(ratio)))
        image = image.resize((PRINTER_HEIGHT, height), Image.ANTIALIAS)
        
        printer.printImage(image, False)
        printer.justify('C')
        printer.setSize('S')
        printer.println("PolaPi-Zero")
        printer.feed(3)
    except IOError:
        print ("cannot identify image file", filename)
    
def saveImageToFile(image, filename):
    print 'saves image ', filename
    # save full image
    image.save(filename)

#Main loop
while True:
    slitScanProcess = SlitScan()
    camera.start_preview()
    camera.preview.fullscreen = False
    camera.preview.window = (0,0,400,240)
    # Buttons loop
    while True:
        sleep(0.1)
        # take a picture   
        if GPIO.event_detected(SHOT_PIN):
            # Increment file number    
            i = 1
            while os.path.exists("pz%05d.jpg" % i):
                i += 1
            currentFileNumber = i
            print("capture pz%05d.jpg" % currentFileNumber)
            
            if slitScanProcess.mode == NO_SCAN:
                camera.capture("pz%05d.jpg" % currentFileNumber, use_video_port=True)
            
            if slitScanProcess.mode == SCAN_MODE_FIX:
                slitScanProcess.image_scan.save("pz%05d.jpg" % currentFileNumber)
                camera.stop_recording()
                
            if slitScanProcess.mode == SCAN_MODE:
                slitScanProcess.image_scan.save("pz%05d.jpg" % currentFileNumber)
                camera.stop_recording()
            
            camera.stop_preview()
            break
        # start slit-scan mode
        if GPIO.event_detected(PREV_PIN):
            slitScanProcess.mode = SCAN_MODE
            camera.start_recording(slitScanProcess, format='yuv', resize=PRINTER_SIZE)
            camera.stop_preview()
        # start slit-scan mode
        if GPIO.event_detected(NEXT_PIN):
            slitScanProcess.mode = SCAN_MODE_FIX
            camera.start_recording(slitScanProcess, format='yuv', resize=PRINTER_SIZE)
            camera.stop_preview()
        # halt system
        if GPIO.event_detected(HALT_PIN):
            haltSystem()
        # slit-scan mode done
        if slitScanProcess.scanDone:
            # Increment file number    
            i = 1
            while os.path.exists("pz%05d.jpg" % i):
                i += 1
            currentFileNumber = i
            print("capture pz%05d.jpg" % currentFileNumber)
            slitScanProcess.image_scan.save("pz%05d.jpg" % currentFileNumber)
            camera.stop_recording()
            camera.stop_preview()
            break
        # review mode
        if GPIO.event_detected(PRINT_PIN):
            hostIP = check_output(['hostname', '-I']) #refresh IP adress
            
            if slitScanProcess.mode == SCAN_MODE_FIX:
                camera.stop_recording()
                
            if slitScanProcess.mode == SCAN_MODE:
                camera.stop_recording()
            
            camera.stop_preview()
            break
    
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
    slideImage("pz%05d.jpg" % currentFileNumber, 1)
    
    # Review Loop
    while True:
        sleep(0.25)
        if GPIO.event_detected(NEXT_PIN):
            # Increment current file name and display it
            if os.path.exists("pz%05d.jpg" % (currentFileNumber+1)):
                currentFileNumber += 1
            slideImage("pz%05d.jpg" % currentFileNumber, 1)
        if GPIO.event_detected(PREV_PIN):
            # Decrement current file name and display it
            if os.path.exists("pz%05d.jpg" % (currentFileNumber-1)):
                currentFileNumber -= 1
            slideImage("pz%05d.jpg" % currentFileNumber, 3)
        if GPIO.event_detected(PRINT_PIN):
            # Print current file
            printImageFile("pz%05d.jpg" % currentFileNumber)
        if GPIO.event_detected(HALT_PIN):
            # halt system
            haltSystem()
        if GPIO.event_detected(SHOT_PIN):
            # Exit review
            break
            
print("Main loop has exited")


