#!/usr/bin/env python
import os
import sys
from lifxlan import *
from copy import deepcopy
import time
import random
import math
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from encoder import Encoder
import urllib.request

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

global strip

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

# set state variables
state_power = 1
state_zonemode = 0
state_colormode = 0

prev_time = math.floor(time.time()*10)

general_color = [0, 0, 65535, 3500]
temp_color = [0, 0, 65535, 3500]
zone_set_color = [0, 0, 65535, 3500]
selected_zone = 0

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
  global state_power
  sleep(0.009)
  if GPIO.input(SWITCH_POWER) == 1:
    print("Power switch on!")
    strip.set_power("on", True)
    state_power = 1
    print("power " + str(state_power))
  else:
    print("Power switch off!")
    strip.set_power("off", True)
    state_power = 0
    print("power " + str(state_power))


def btn_zonemode_cb(channel):
    print("Zonemode button pressed!")
    global selected_zone
    global state_zonemode
    global zone_set_color

    # first of all, check if lifx power is on or not and do nothing if not
    if state_power == 1 and GPIO.input(BTN_ZONE) == 1:
      state_zonemode = 1 - state_zonemode
      print("zonemode " + str(state_zonemode))
      selected_zone = 0

    if state_zonemode == 1:
      GPIO.output(LED_ZONE,GPIO.HIGH)
      #zone_set_color = list(strip.get_color_zones(selected_zone, selected_zone + 1)[0])
      #temp_color = zone_set_color
    else: GPIO.output(LED_ZONE,GPIO.LOW)

    sleep(0.1)


def btn_colormode_cb(channel):
    print("Colormode button pressed!")
    global state_colormode

    # first of all, check if lifx power is on or not and do nothing if not
    if state_power == 1 and GPIO.input(BTN_COLOR) == 1:
        state_colormode = 1 - state_colormode
        print("colormode " + str(state_colormode))

    if state_colormode == 1:
      GPIO.output(LED_COLOR,GPIO.HIGH)
      if state_zonemode == 0:
        general_color[3] = 3500
        general_color[1] = 65535
        strip.set_color(general_color, 100, True)
      else:
        zone_set_color[3] = 3500
        zone_set_color[1] = 65535
    else:
      GPIO.output(LED_COLOR,GPIO.LOW)
      if state_zonemode == 0:
        general_color[1] = 0
        strip.set_color(general_color, 100, True)
      else:
        zone_set_color[1] = 0

    sleep(0.1)


def btn_preset_cb(channel):
  if GPIO.input(BTN_PRESET) == 1:
    print("Preset button pressed!")
    GPIO.output(LED_PRESET, GPIO.HIGH)
    # this can be used for reset, make some rule for this
    #os.execl(sys.executable, sys.executable, *sys.argv)
  else:
    GPIO.output(LED_PRESET, GPIO.LOW)


def enc_cb(value, direction):
  print("Encoder turned!")
  global selected_zone

  # first of all, check if lifx power is on or not and do nothing if not
  if state_power == 1:

    # if zone mode is OFF
    if state_zonemode == 0:
      rand_zone = random.randint(0, zone_count)
      rand_color = [random.randint(0, 65535), random.randint(0, 65535), 65535, 3500]
      strip.set_zone_color(rand_zone, rand_zone, rand_color, 0, 1, 1)

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

def internet_on():
    try:
        urllib.request.urlopen('http://www.google.com', timeout=1)
        return True
    except urllib.request.URLError:
        return False


# main function --------------------------------------------


def main():

  ########################
  #### Initialization ####
  ########################

  global zone_count

  ph_input_pot = 0.5 # TODO For now, i'm assuming the pot range as 0-1. Correct this as the actual connections are made.
  ph_input_pot_prev = ph_input_pot

  # check for internet connection
  for x in range(100):
    if internet_on() is True:
      print("Internet connection OK")
      break
    print("Testing internet connection", x)
    sleep(1)

  #### lifx init ####

  num_lights = None
  if len(sys.argv) != 2:
    print("\nDiscovery will go much faster if you provide the number of lights on your LAN:")
    print("  python {} <number of lights on LAN>\n".format(sys.argv[0]))
  else:
    num_lights = int(sys.argv[1])

  # instantiate LifxLAN client, num_lights may be None (unknown).
  # In fact, you don't need to provide LifxLAN with the number of bulbs at all.
  # lifx = LifxLAN() works just as well. Knowing the number of bulbs in advance
  # simply makes initial bulb discovery faster.
  lifx = LifxLAN(num_lights)

  # test power control
  print("Discovering lights...")
  original_powers = lifx.get_power_all_lights()

  print ("Starting program.")

  # get devices
  for x in range(100):
    multizone_lights = lifx.get_multizone_lights()
    if len(multizone_lights) > 0:
      print("Multizone light discovered")
      break
    print("Discovering multizone lights..", x)
    sleep(1)

  # finding the correct light to operate on
  if len(multizone_lights) > 0:
    global strip
    strip = multizone_lights[0]
    print("Selected {}".format(strip.get_label()))


    # saving the original zones
    original_zones = strip.get_color_zones()
    # the amount of zones in the light
    zone_count = len(original_zones)
    # make a mutable array for current zones
    current_zones = []
    for i in range(zone_count):
      current_zones.append(list(original_zones[i]))

  # if there's no light available...
  else:
    print("No multizone lights available")



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

  enc = Encoder(21, 12, enc_cb)

  last_read = 0   # this keeps track of the last potentiometer value
  tolerance = 550 # to keep from being jittery we'll only change
                # volume when the pot has moved a significant amount
                # on a 16-bit ADC


  #### others ####

  # check the power and set the state variable accordingly
  if strip.get_power() == 65535:
    state_power = 1
    print("powertest")
    print(state_power)

  simplecounter = 0



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


    # counter
    if count_halfsecond() == True:
      simplecounter += 1
      #print(simplecounter)

    # detect pot move
    if pot_adjust > tolerance:
        trim_pot_changed = True

    ## checking if strip is in zone mode or default mode and determine the behaviour of the controls in both

    # if zone mode is OFF
    if state_zonemode == 0:

        # if pot was turned
        if trim_pot_changed:

          print(trim_pot)

          # Knob behaviour

          # if the color mode is off only temperature is adjusted
          if state_colormode == 0:
            general_color[3] = map(trim_pot, (0, 65535), (2500, 9000))

          # if the color mode is on, the 3-way switch selects which parameter is changed
          else:
            # if brightness mode
            if GPIO.input(SWITCH_BRIGHTNESS):
              general_color[2] = trim_pot
            # if color mode
            elif GPIO.input(SWITCH_COLOR):
              general_color[0] = trim_pot
            # if saturation mode
            elif not GPIO.input(SWITCH_BRIGHTNESS) and not GPIO.input(SWITCH_COLOR):
              general_color[1] = trim_pot

          strip.set_color(general_color, 200, True)

          # save the potentiometer reading for the next loop
          last_read = trim_pot


    # if zone mode is ON
    else:

        # if pot was turned
        if trim_pot_changed:

          print(trim_pot)

          # Knob behaviour

          # if the color mode is off only temperature is adjusted
          if state_colormode == 0:
            zone_set_color[3] = map(trim_pot, (0, 65535), (2500, 9000))

          # if the color mode is on, the 3-way switch selects which parameter is changed
          else:
            # if brightness mode
            if GPIO.input(SWITCH_BRIGHTNESS):
              zone_set_color[2] = trim_pot
            # if color mode
            elif GPIO.input(SWITCH_COLOR):
              zone_set_color[0] = trim_pot
            # if saturation mode
            elif not GPIO.input(SWITCH_BRIGHTNESS) and not GPIO.input(SWITCH_COLOR):
              zone_set_color[1] = trim_pot

          strip.set_zone_color(selected_zone, selected_zone, zone_set_color, 0, 1, 1)

          # save the potentiometer reading for the next loop
          last_read = trim_pot

        # blinking behaviour
        """
        if simplecounter >= 2:
          simplecounter = 0
          temp_color = zone_set_color
          temp_color[2] = 0
          strip.set_zone_color(selected_zone, selected_zone, temp_color, 0, True, 1)
          #print(temp_color)
        if simplecounter == 1 and temp_color[2] == 0:
          temp_color = zone_set_color
          temp_color[2] = 65535
          strip.set_zone_color(selected_zone, selected_zone, temp_color, 0, True, 1)
          #print(temp_color)
        """
        # TODO preset button behaviour



    sleep(0.01)

if __name__=="__main__":
  main()


