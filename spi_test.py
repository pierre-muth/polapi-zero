'''
Created on Jan 13, 2017

@author: pfreyerm
'''

import time
import spidev
import RPi.GPIO as GPIO
from smemlcd import SMemLCD
import PIL.Image, PIL.ImageDraw, PIL.ImageFont


GPIO.setmode(GPIO.BOARD)
GPIO.setup(22, GPIO.OUT, initial=GPIO.LOW)

WIDTH, HEIGHT = 400, 240

def center(draw, y, txt, font):
    w, h = draw.textsize(txt, font=font)
    x = int((WIDTH - w) / 2)
    draw.text((x, y), txt, fill='white', font=font)

lcd = SMemLCD('/dev/spidev0.0')

img = PIL.Image.new('1', (WIDTH, HEIGHT))
draw = PIL.ImageDraw.Draw(img)
font = PIL.ImageFont.load_default()

for i in range(60, -1, -1):
    img.paste(0)

    center(draw, 60, 'smemlcd library demo', font)

    s = 'closing in {:02d}...'.format(i)
    center(draw, 100, s, font)

    draw.arc(((180, 180), (220, 220)), 0, 360, fill='white')
    draw.pieslice(((180, 180), (220, 220)), -90, (60 - i) * 6 - 90, outline='white')

    t1 = time.time()
    
    GPIO.output(22, 1)
    lcd.write(img.tobytes())
    GPIO.output(22, 0)
    
    print('lcd writing time', round(time.time() - t1, 4))

    time.sleep(1)

GPIO.cleanup()


if __name__ == '__main__':
    pass