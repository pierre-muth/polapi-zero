'''
Created on 24 Jan 2017

@author: muth    
'''
from time import sleep
import threading
import os
from platform import _release_filename
from sysconfig import _get_makefile_filename

class TimerClass(threading.Thread):
    eventShot = False
    eventPrint = False
    eventPrevious = False
    eventNext = False
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.event = threading.Event()

    def run(self):
        while True:
            foo = raw_input(">")
            self.eventShot = foo == "s"
            self.eventPrint = foo == "p"
            self.eventPrevious = foo == "a"
            self.eventNext = foo == "d"
            
    def hasEventShot(self):
        if self.eventShot:
            self.eventShot = False
            return True
        else:
            return False
        
    def hasEventPrint(self):
        if self.eventPrint:
            self.eventPrint = False
            return True 
        else:
            return False

    def hasEventPrevious(self):
        if self.eventPrevious:
            self.eventPrevious = False
            return True 
        else:
            return False
        
    def hasEventNext(self):
        if self.eventNext:
            self.eventNext = False
            return True
        else:
            return False


thread = TimerClass()
thread.start()

def displayImage(filename):
    print 'displays ', filename
    
def printImage(filename):
    print 'prints ', filename
    
def saveImage(image, filename):
    print 'saves image ', filename
    fh = open(filename, 'w')
    fh.close()

isShot = False
currentFileNumber = -1

#Main loop
while True:
        # View Loop
        while True:
            sleep(0.5)
            # Take image for view & display it'
            print 'Viewing'
            if thread.hasEventShot():
                isShot = True
                break
            if thread.hasEventPrint():
                break
        
        # Do we shot ?
        if isShot:
            # Increment file number
            i = 1
            while os.path.exists("pz%05d.jpg" % i):
                i += 1
            currentFileNumber = i
            # Take an image
            image = 'Take an image'
            # save it to file
            saveImage(image, "pz%05d.jpg" % currentFileNumber)
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
        displayImage("pz%05d.jpg" % currentFileNumber)
        
        # Review Loop
        while True:
            sleep(0.5)
            if thread.hasEventNext():
                # Increment current file name and display it
                if os.path.exists("pz%05d.jpg" % (currentFileNumber+1)):
                    currentFileNumber += 1
                displayImage("pz%05d.jpg" % currentFileNumber)
            if thread.hasEventPrevious():
                # Decrement current file name and display it
                if os.path.exists("pz%05d.jpg" % (currentFileNumber-1)):
                    currentFileNumber -= 1
                displayImage("pz%05d.jpg" % currentFileNumber)
            if thread.hasEventPrint():
                # Print current file
                printImage("pz%05d.jpg" % currentFileNumber)
            if thread.hasEventShot():
                # Exit review
                break
            
print("Main loop has exited")


