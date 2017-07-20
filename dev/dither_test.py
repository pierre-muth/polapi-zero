'''
Created on Jan 13, 2017

@author: pfreyerm
'''

from io import BytesIO
from time import sleep
from picamera import PiCamera
from PIL import Image

# Create the in-memory stream
stream = BytesIO()
camera = PiCamera()
camera.resolution = (400, 240)
camera.start_preview()
sleep(2)
camera.capture(stream, format='jpeg')
# "Rewind" the stream to the beginning so we can read its content
stream.seek(0)
image = Image.open(stream)
image = image.convert('1') # convert image to black and white
image.save('result.png')


if __name__ == '__main__':
    pass