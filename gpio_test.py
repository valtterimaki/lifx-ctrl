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


# GPIO library, note that the except part is for enabling dummy development on mac/pc
try:
    # checks if you have access to RPi.GPIO, which is available inside RPi
    import RPi.GPIO as GPIO
except:
    # In case of exception, you are executing your script outside of RPi, so import Mock.GPIO
    import Mock.GPIO as GPIO
# from encoder import Encoder



#####################
##### VARIABLES #####
#####################

# define buttons (TODO remap)
BTN_POWER_ON = 1
BTN_POWER_OFF = 2
BTN_ZONE = 3
BTN_COLOR = 4
SWITCH_BRIGHTNESS = 5
SWITCH_COLOR = 6

# these are for the potentiometer
# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D5)
# create the mcp object
mcp = MCP.MCP3008(spi, cs)
# create an analog input channel on pin 0
chan = AnalogIn(mcp, MCP.P0)


########################################################################
##### GPIO callbacks that determine what happen on button triggers #####
########################################################################

def btn_power_on_cb(channel):
  print("Power switch on!")
  global state_power
  strip.set_power("on", True)
  state_power = 1
  print("power " + str(state_power))


def btn_power_off_cb(channel):
  print("Power switch off!")
  strip.set_power("off", True)
  state_power = 0
  print("power " + str(state_power))


def btn_zonemode_cb(channel):
  print("Zonemode button pressed!")
  global state_zonemode
  global zone_set_color

  # first of all, check if lifx power is on or not and do nothing if not
  if state_power == 1:
    selected_zone = 0
    if state_zonemode == 0:
      zone_set_color = list(strip.get_color_zones(selected_zone, selected_zone + 1)[0])
      temp_color = zone_set_color
    sleep(0.1)
    state_zonemode = 1 - state_zonemode
    print("zonemode " + str(state_zonemode))


def btn_colormode_cb(channel):
  print("Colormode button pressed!")
  global state_colormode

  # first of all, check if lifx power is on or not and do nothing if not
  if state_power == 1:
    state_colormode = 1 - state_colormode
    print("colormode " + str(state_colormode))


def enc_cb(value, direction):
  print("Encoder turned!")
  global selected_zone

  # first of all, check if lifx power is on or not and do nothing if not
  if state_power == 1:

    # if zone mode is OFF
    if state_zonemode == 0:
      pass

    # if zone mode is ON
    else:
      if direction == "R":
        if selected_zone < zone_count:
          strip.set_zone_color(selected_zone, selected_zone, zone_set_color, 0, 1, 1)
          selected_zone += 1
          print("selected zone " + str(selected_zone))
          print(zone_set_color)
      if direction == "L":
        if selected_zone > 0:
          strip.set_zone_color(selected_zone, selected_zone, zone_set_color, 0, 1, 1)
          selected_zone -= 1
          print("selected zone " + str(selected_zone))
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

  GPIO.setup(BTN_POWER_ON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(BTN_POWEROFF, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(BTN_ZONE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(BTN_COLOR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(SWITCH_BRIGHTNESS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(SWITCH_COLOR, GPIO.IN, pull_up_down=GPIO.PUD_UP)

  GPIO.add_event_detect(BTN_POWER_ON, GPIO.FALLING, callback=btn_power_on_cb, bouncetime=50)
  GPIO.add_event_detect(BTN_POWER_OFF, GPIO.FALLING, callback=btn_power_off_cb, bouncetime=50)
  GPIO.add_event_detect(BTN_ZONE, GPIO.FALLING, callback=btn_zonemode_cb, bouncetime=50)
  GPIO.add_event_detect(BTN_COLOR, GPIO.FALLING, callback=btn_colormode_cb, bouncetime=50)

  # enc = Encoder(6, 7, enc_cb) # remap gpio


  #######################################
  #### actual running program itself ####
  #######################################

  while True:



if __name__=="__main__":
  main()


