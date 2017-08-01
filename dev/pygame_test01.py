'''
Created on 20 Jul 2017
@author: muth
'''

import sys, pygame, math
import os
pygame.init()
s_width = 640
s_height = 480
screen_size = s_width, s_height
l_width = 400
l_height = 240
lcd_size = l_width, l_height
lcd_ratio = 1.0*l_width/l_height 
backgroundColor = 255, 255, 255
black = 0, 0, 0
currentFileNumber = -1

screen = pygame.display.set_mode(screen_size)
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

logo = pygame.image.load("logo01.png")
previousimage = logo
# logo = pygame.transform.scale(logo, (400, 240))

screen.fill(backgroundColor)

pygame.draw.line(screen, black, (0, l_height), (l_width, l_height), 1)
pygame.draw.line(screen, black, (l_width, 0), (l_width, l_height), 1)

screen.blit(logo, (40,95))
pygame.display.flip()

x = y = 0

    
# Set current file number if not set yet
if currentFileNumber == -1 :
    i = 0
    while True:
        if os.path.exists("pz%05d.jpg" % (i+1)):
            i += 1
        else :
            break
    currentFileNumber = i

def slideImage(imageFile, direction):
    global previousimage
    image = pygame.image.load(imageFile)
    i_width = image.get_width()
    i_height = image.get_height()
    i_ratio = 1.0*i_width/i_height 
    
    if i_ratio < lcd_ratio:
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
    pygame.draw.line(screen, black, (0, l_height), (l_width, l_height), 1)
    pygame.draw.line(screen, black, (l_width, 0), (l_width, l_height), 1)
    pygame.display.flip()
    previousimage = image
    
while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                # Increment current file name and display it
                if os.path.exists("pz%05d.jpg" % (currentFileNumber+1)):
                    currentFileNumber += 1
                    slideImage("pz%05d.jpg" % currentFileNumber, 3);
                
            if event.button == 1:
                # Increment current file name and display it
                if os.path.exists("pz%05d.jpg" % (currentFileNumber-1)):
                    currentFileNumber -= 1
                    slideImage("pz%05d.jpg" % currentFileNumber, 1);

