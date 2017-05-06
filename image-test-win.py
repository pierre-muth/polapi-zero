'''
Created on Jan 29, 2017
@author: muth
'''
from PIL import Image
from PIL import ImageOps

S_WIDTH = 400
S_HEIGHT = 240
S_RATIO_H = S_WIDTH/S_HEIGHT
S_RATIO_V = S_HEIGHT/S_WIDTH
S_SIZE = (S_WIDTH, S_HEIGHT)

image = Image.open('pz00176.jpg')
im_width, im_height = image.size

if im_width < im_height:
    image = image.rotate(90, expand=1)

image.show()

image.thumbnail(S_SIZE, Image.ANTIALIAS)

image.show()

image_sized = Image.new('RGB', S_SIZE, (128, 128, 128))
image_sized.paste(image,((S_SIZE[0] - image.size[0]) / 2, (S_SIZE[1] - image.size[1]) / 2))
image_sized = image_sized.convert('1') # convert image to black and white

image_sized.show()