# *************************************************** 
#   International Space Station Tracker.
#   using Raspberry Pi B+, Waveshare ePaper Display and ProtoStax enclosure
#   --> https://www.waveshare.com/product/modules/oleds-lcds/e-paper/2.7inch-e-paper-hat-b.htm
#   --> https://www.protostax.com/products/protostax-for-raspberry-pi-b
#
#   It displays the current location of the ISS and also its tracked trajectory. The
#   current location is shown by the ISS icon, and the trajectory by small circles.
#   15 minute markers are shown as small rectangles.
#
#   ISS Current Location is obtained using Open Notify ISS Current Location API
#   http://open-notify.org/Open-Notify-API/ISS-Location-Now/
j# 
#   Written by Sridhar Rajagopal for ProtoStax.
#   BSD license. All text above must be included in any redistribution
# *


import sys
sys.path.append(r'lib')

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

from enum import Enum
import signal
import epd2in7b
import epdconfig

from PIL import Image,  ImageDraw,  ImageFont, ImageOps
from datetime import datetime
from time import sleep

import requests 

# Update Interval
INTERVAL = 30 #seconds

# Note:
# The dimensions of the 2.7 in ePaper display are
# 264 x 176

class Display(object):
    def __init__(self, imageWidth, imageHeight):
        self.imageWidth = imageWidth
        self.imageHeight = imageHeight

    # Draws the ISS current location and trajectory from array of positions
    def drawISS(self, positions):
        imageBlack = Image.new('1', (self.imageWidth, self.imageHeight), 255) # 1: clear the frame
        imageMap = Image.open('world_map_m.bmp').convert('L')
        imageBlack.paste(imageMap, (0,0))

        imageRed = Image.new('1', (self.imageWidth, self.imageHeight), 255) # 1: clear the frame
        issLogo = Image.open('iss.bmp').convert('L')
        drawred = ImageDraw.Draw(imageGray)
  
        for i,t in enumerate(positions):
            (lat,lon) = t

            # Map the lat, lon to our x/y coordinate system
            (x,y) = self.mapLatLongToXY(lat, lon)

            # last position in the positions array is the latest location
            # Every 15 minutes, we add a rectangular marker
            # and a small red circle to mark other locations
        
            if (i == len(positions) - 1):
                s = 10
                # drawred.rectangle((x-s,y-s,x+s,y+s), fill=0)
                imageGray.paste(issLogo, ((int)(x-s), (int)(y-s)))
            elif (((i+1) % 30) == 0): # every 15 minutes (one reading every 30 seconds, so 30 readings)
                s = 2
                drawred.rectangle((x-s,y-s,x+s,y+s), fill=0)
            else:
                s = 1
                drawred.ellipse((x-s,y-s,x+s,y+s), outline=0)
                # drawred.point((x,y), fill=0)

        # return the rendered Red and Black images
        return imageBlack, imageRed

    # Maps lat, long to x,y coordinates in 264x181 (the size of the world map)
    # (90 to -90 lat and -180 to 180 lon) map to 0-181 (y) and 0-264 (x) respectively
    # Simple algebra gives us the equations below
    # Recalculate as appropriate for map size and coordinates
    def mapLatLongToXY(self, lat, lon):
        x = (int)(0.733 * lon + 132)
        y = (int)(-1.006 * lat + 90.5)
        return x, y 

# The main function    
def main():
    # API to get ISS Current Location
    URL = 'http://api.open-notify.org/iss-now.json'

    # Initialize and clear the 2in7b (tri-color) display
    epd = epd2in7b.EPD()

    display = Display(epd2in7b.EPD_HEIGHT, epd2in7b.EPD_WIDTH)

    # Store positions in list
    positions = []

    while(True):
        epd.init()

        r = requests.get(url = URL)

        # extracting data in json format 
        data = r.json() 
        print(data)
        
        lat = float(data['iss_position']['latitude'])
        lon = float(data['iss_position']['longitude'])
        
        positions.append((lat, lon))
        print(positions)

        (imageBlack, imageRed) = display.drawISS(positions)

        # We're drawing the map in black and the ISS location and trajectory in red
        # Swap it around if you'd like the inverse color scheme
        epd.display(epd.getbuffer(imageBlack), epd.getbuffer(imageRed))
        sleep(2)
        epd.sleep()
       
        sleep(INTERVAL) # sleep for 30 seconds 


# gracefully exit without a big exception message if possible
def ctrl_c_handler(signal, frame):
    print('Goodbye!')
    # XXX : TODO
    #
    # To preserve the life of the ePaper display, it is best not to keep it powered up -
    # instead putting it to sleep when done displaying, or cutting off power to it altogether.
    #
    # epdconfig.module_exit() shuts off power to the module and calls GPIO.cleanup()
    # The latest epd library chooses to shut off power (call module_exit) even when calling epd.sleep()    
    # epd.sleep() calls epdconfig.module_exit(), which in turns calls cleanup().
    # We can therefore end up in a situation calling GPIO.cleanup twice
    # 
    # Need to cleanup Waveshare epd code to call GPIO.cleanup() only once
    # for now, calling epdconfig.module_init() to set up GPIO before calling module_exit to make sure
    # power to the ePaper display is cut off on exit
    # I have also modified epdconfig.py to initialize SPI handle in module_init() (vs. at the global scope)
    # because slepe/module_exit closes the SPI handle, which wasn't getting initialized in module_init
    epdconfig.module_init()
    epdconfig.module_exit()
    print("Remeber to clear the display using cleardisplay.py if you plan to power down your Pi and store it, to prevent burn-in!")
    exit(0)

signal.signal(signal.SIGINT, ctrl_c_handler)


if __name__ == '__main__':
    main()
