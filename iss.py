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
#
#   Written by Sridhar Rajagopal for ProtoStax.
#
#   Contributions by:
#   jplegat
#   MatKier
#   MiketheChap/melcasipit-Mike Davis paid coder melcasipit on Fiverr to write ring/circular buffer+exception handling
#
#   BSD license. All text above must be included in any redistribution


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
from time import time, sleep

import requests

# Update Interval for fetching positions
DATA_INTERVAL = 30 #seconds
# Update interval for the display
DISPLAY_REFRESH_INTERVAL = 2 # Number of DATA_INTERVAL between successive display updates (e.g. 2 => update display every second deta fetch)

# Limit the number of data entries
# Entries older than this will be aged out - ie. circular buffer
# Since we update the position every 30 seconds (DATA_INTERVAL),
# that would be 24*60*2 = 2880 data points. The ISS does about
# 16 orbits per day. Setting the DATA_LIMIT to 1440 would give us about
# 8 orbits worth of data
# You can adjust this down to the period of interest for you with the
# above math
DATA_LIMIT = 1440 # positions limit

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
        drawred = ImageDraw.Draw(imageRed)

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
                imageRed.paste(issLogo, ((int)(x-s), (int)(y-s)))
            elif (((i+1) % (15 * 60 / DATA_INTERVAL)) == 0): # every 15 minutes (so 15 * 60s / DATA_INTERVAL = number of readings within 15 minutes)
                s = 2
                drawred.rectangle((x-s,y-s,x+s,y+s), fill=0)
            else:
                s = 1
                drawred.ellipse((x-s,y-s,x+s,y+s), outline=0)
                # drawred.point((x,y), fill=0)

        # Rotate image 180 degrees - Remove the # comments of the lines below to rotate the image and allow for alternate positioning/mounting of the Raspberry Pi 
        # imageRed = imageRed.transpose(Image.ROTATE_180)
        # imageBlack = imageBlack.transpose(Image.ROTATE_180)

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
        t0 = time()
        try:
            r = requests.get(url = URL)

            # extracting data in json format
            data = r.json()
            print(data)
        except:
            print("error getting data.... might be a temporary hiccup so continuing")
            continue

        lat = float(data['iss_position']['latitude'])
        lon = float(data['iss_position']['longitude'])
        if len(positions) > (DATA_LIMIT - 1):
            del positions[0]
        positions.append((lat, lon))
        print(positions)

        # Refresh the display on the first fetch and then on every DISPLAY_REFRESH_INTERVAL fetch
        if ((len(positions) >= 1) and ((len(positions)-1) % DISPLAY_REFRESH_INTERVAL)):
            epd.init()
            (imageBlack, imageRed) = display.drawISS(positions)
            # We're drawing the map in black and the ISS location and trajectory in red
            # Swap it around if you'd like the inverse color scheme
            epd.display(epd.getbuffer(imageBlack), epd.getbuffer(imageRed))
            sleep(2)
            epd.sleep()
       
        t1 = time()
        sleepTime = max(DATA_INTERVAL - (t1 - t0), 0)
        sleep(sleepTime) # sleep for 30 seconds minus duration of get request and display refresh



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
