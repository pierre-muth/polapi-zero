'''
Created on 24 Jan 2017
@author: muth    
'''
from time import sleep
import os
import RPi.GPIO as GPIO
from PIL import Image
from PIL import ImageOps
from smemlcd import SMemLCD

S_WIDTH = 400
S_HEIGHT = 240
S_RATIO_H = S_WIDTH/S_HEIGHT
S_RATIO_V = S_HEIGHT/S_WIDTH
S_SIZE = (S_WIDTH, S_HEIGHT)

lcd = SMemLCD('/dev/spidev0.0')

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
    fh = open(filename, 'w')
    fh.close()
    # save full res image
    
def displayImageOnLCD(image):
    print image
    
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
GPIO.add_event_detect(SHOT_PIN, GPIO.FALLING, bouncetime=100)  
GPIO.add_event_detect(PRINT_PIN, GPIO.FALLING, bouncetime=100)  
GPIO.add_event_detect(NEXT_PIN, GPIO.FALLING, bouncetime=100)  
GPIO.add_event_detect(PREV_PIN, GPIO.FALLING, bouncetime=100)  

#Main loop
while True:
        # View Loop
        while True:
            sleep(0.5)
            # Take images at screen resolution, dither and send to display
            displayImageOnLCD('Viewing')

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
            # Take an image from camera
            image = 'Take an image'
            # save it to a jpeg file
            saveImageToFile(image, "pz%05d.jpg" % currentFileNumber)
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
            sleep(0.5)
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


