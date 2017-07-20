'''
Created on Jan 29, 2017
@author: muth
'''
from PIL import Image
from PIL import ImageOps
from smemlcd import SMemLCD

S_WIDTH = 400
S_HEIGHT = 240
S_RATIO_H = S_WIDTH/S_HEIGHT
S_RATIO_V = S_HEIGHT/S_WIDTH
S_SIZE = (S_WIDTH, S_HEIGHT)

lcd = SMemLCD('/dev/spidev0.0')

image = Image.open('pz00002.jpg')
im_width, im_height = image.size
if im_width < im_height:
    image = image.rotate(90)
image.thumbnail(S_SIZE, Image.ANTIALIAS)
image_sized = Image.new('RGB', S_SIZE, (0, 0, 0))
image_sized.paste(image,((S_SIZE[0] - image.size[0]) / 2, (S_SIZE[1] - image.size[1]) / 2))
image_sized = ImageOps.invert(image_sized)
image_sized = image_sized.convert('1') # convert image to black and white

lcd.write(image_sized.tobytes())