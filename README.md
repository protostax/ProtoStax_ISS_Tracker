# ProtoStax_ISS_Tracker
Demo for ProtoStax ISS Tracker with ePaper Display and Raspberry Pi

![ProtoStax Word Clock](ProtoStax_ISS_Tracker.jpg)

![ProtoStax Word Clock](ProtoStax_ISS_Tracker.gif)


using [ProtoStax for Raspberry Pi B+](https://www.protostax.com/products/protostax-for-raspberry-pi-b)

## Prerequisites

* Enable SPI on the Raspberry P
* Python 3 or higher. The code and the ePaper library assumes you are
  using Python 3 or higher! (with Raspbian Buster, the latest is
  Python3.7)

**Install spidev, RPi.gpio, Pillow and requests**
**NOTE - Use sudo pip3!**

```
sudo apt-get install python3-spidev
sudo apt-get install rpi.gpio
sudo apt-get install python3-pil
sudo pip3 install requests
```


## Installing

This demo uses Waveshare's ePaper libary - see
[https://github.com/waveshare/e-Paper](https://github.com/waveshare/e-Paper)

but includes the necessary files from that library directly, so you
**don't need to install anything extra**!

```
git clone https://github.com/protostax/ProtoStax_Word_Clock.git
```

## Usage

```
cd ProtoStax_ISS_Tracker
```

**NOTE - Using Python 3 or higher!**

```
python3 iss.py
```

The program will run every 30 seconds, updating the 
display with the current location of the ISS as well as the trajectory recorded
since the start.

## License

Written by Sridhar Rajagopal for ProtoStax. BSD license, all text above must be included in any redistribution

A lot of time and effort has gone into providing this and other code. Please support ProtoStax by purchasing products from us!
Also uses the Waveshare ePaper library. Please support Waveshare by purchasing products from them!


