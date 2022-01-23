#!/usr/bin/env python
import sys
from lifxlan import *
from copy import deepcopy
import time
from random import *
import math
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from encoder import Encoder

# GPIO library, note that the except part is for enabling dummy development on mac/pc
try:
    # checks if you have access to RPi.GPIO, which is available inside RPi
    import RPi.GPIO as GPIO
except:
    # In case of exception, you are executing your script outside of RPi, so import Mock.GPIO
    import Mock.GPIO as GPIO

#####################
##### VARIABLES #####
#####################

# define buttons (TODO remap)
SWITCH_POWER = 18
BTN_ZONE = 17
BTN_COLOR = 27
BTN_PRESET = 23
LED_ZONE = 16
LED_COLOR = 20
LED_PRESET = 24
SWITCH_BRIGHTNESS = 5
SWITCH_COLOR = 6

# these are for the potentiometer
# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D22)
# create the mcp object
mcp = MCP.MCP3008(spi, cs)
# create an analog input channel on pin 0
chan0 = AnalogIn(mcp, MCP.P0)


########################################################################
##### GPIO callbacks that determine what happen on button triggers #####
########################################################################

def btn_power_on_cb(channel):
  sleep(0.009)
  if GPIO.input(SWITCH_POWER) == 1:
    print("Power switch on!")
  else:
    print("Power switch off!")


def btn_zonemode_cb(channel):
  if GPIO.input(BTN_ZONE) == 1:
    print("Zonemode button pressed!")
    GPIO.output(LED_ZONE,GPIO.HIGH)
  else:
    GPIO.output(LED_ZONE,GPIO.LOW)


def btn_colormode_cb(channel):
  if GPIO.input(BTN_COLOR) == 1:
    print("Colormode button pressed!")
    GPIO.output(LED_COLOR, GPIO.HIGH)
  else:
    GPIO.output(LED_COLOR, GPIO.LOW)

def btn_preset_cb(channel):
  if GPIO.input(BTN_PRESET) == 1:
    print("Preset button pressed!")
    GPIO.output(LED_PRESET, GPIO.HIGH)
  else:
    GPIO.output(LED_PRESET, GPIO.LOW)


def enc_cb(value, direction):
  print("Encoder turned!")
  print("* New value: {}, Direction: {}".format(value, direction))



# TODO add preset change here at some point



##################################
##### other custom functions #####
##################################

def map(val, src, dst):
    # Map the given value from the scale of src to the scale of dst.
    return ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]

def count_halfsecond():
  global prev_time
  if prev_time + 2 < math.floor(time.time()*10):
    prev_time = math.floor(time.time()*10)
    return True


# main function --------------------------------------------


def main():

  ########################
  #### Initialization ####
  ########################

  #### GPIO setups ####

  GPIO.setmode(GPIO.BCM)

  GPIO.setup(SWITCH_POWER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.setup(BTN_ZONE, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.setup(BTN_COLOR, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.setup(BTN_PRESET, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.setup(SWITCH_BRIGHTNESS, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.setup(SWITCH_COLOR, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.setup(LED_ZONE,GPIO.OUT)
  GPIO.setup(LED_COLOR,GPIO.OUT)
  GPIO.setup(LED_PRESET,GPIO.OUT)

  GPIO.add_event_detect(SWITCH_POWER, GPIO.BOTH, callback=btn_power_on_cb, bouncetime=10)
  GPIO.add_event_detect(BTN_ZONE, GPIO.RISING, callback=btn_zonemode_cb, bouncetime=10)
  GPIO.add_event_detect(BTN_COLOR, GPIO.RISING, callback=btn_colormode_cb, bouncetime=10)
  GPIO.add_event_detect(BTN_PRESET, GPIO.RISING, callback=btn_preset_cb, bouncetime=10)

  enc = Encoder(21, 12, enc_cb) # remap gpio

  last_read = 0   # this keeps track of the last potentiometer value
  tolerance = 550 # to keep from being jittery we'll only change
                # volume when the pot has moved a significant amount
                # on a 16-bit ADC


  #######################################
  #### actual running program itself ####
  #######################################

  while True:

    # we'll assume that the pot didn't move
    trim_pot_changed = False

    # read the analog pin
    trim_pot = chan0.value

    # how much has it changed since the last read?
    pot_adjust = abs(trim_pot - last_read)

    if pot_adjust > tolerance:
        trim_pot_changed = True
    if trim_pot_changed:
        print(trim_pot)
        if GPIO.input(SWITCH_BRIGHTNESS):
          print("Brightness switch on")
        elif GPIO.input(SWITCH_COLOR):
          print("Color switch on")
        elif not GPIO.input(SWITCH_BRIGHTNESS) and not GPIO.input(SWITCH_COLOR):
          print("Saturation switch on")

        # save the potentiometer reading for the next loop
        last_read = trim_pot
    sleep(0.01)



if __name__=="__main__":
  main()

