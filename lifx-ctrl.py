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

global strip

# define buttons (TODO remap)
BTN_POWER_ON = 1
BTN_POWER_OFF = 2
BTN_ZONE = 3
BTN_COLOR = 4
SWITCH_BRIGHTNESS = 5
SWITCH_COLOR = 6

# set state variables
state_power = 1
state_zonemode = 0
state_colormode = 0
state_switch_brightness = 0
state_switch_color = 0

prev_time = math.floor(time.time()*10)

temp_color = [0, 0, 65535, 5000]
zone_set_color = [0, 0, 0, 5000]

# these are for the potentiometer
# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D5)
# create the mcp object
mcp = MCP.MCP3008(spi, cs)
# create an analog input channel on pin 0
chan = AnalogIn(mcp, MCP.P0)



##############################################
##### OLD PLACEHOLDER KEYBOARD TEST CODE #####
##############################################

# Keyboard input placeholder to simulate GPIO inputs
# TODO replace with actual gpio stuff
"""
def key_release(key):

  # declare state variables (here because wtf...)
  global state_power
  global state_zonemode
  global state_colormode
  global state_switch_brightness
  global state_switch_color
  global state_preset

  global selected_zone

  # placeholder variable to simulate pot reading
  global ph_input_pot
  global ph_input_pot_prev

  global temp_color
  global zone_set_color

  #print('{0} released'.format(key))
  #if key == keyboard.Key.esc:
  #    # Stop listener
  #    return False
  if 'char' in dir(key):
    if key.char == 'q':
      strip.set_power("on", True)
      state_power = 1
      print("power " + str(state_power))
    if key.char == 'a':
      strip.set_power("off", True)
      state_power = 0
      print("power " + str(state_power))

    if key.char == 'h':
      state_colormode = 1 - state_colormode
      print("colormode " + str(state_colormode))
    if key.char == 'j':
      state_switch_color = 1
      state_switch_brightness = 0
      print("color switch on")
    if key.char == 'k':
      state_switch_color = 0
      state_switch_brightness = 0
      print("saturation switch on")
    if key.char == 'l':
      state_switch_color = 0
      state_switch_brightness = 1
      print("brightness switch on")

    if key.char == 'z':
      selected_zone = 0
      if state_zonemode == 0:
        zone_set_color = list(strip.get_color_zones(selected_zone, selected_zone + 1)[0])
        temp_color = zone_set_color
      sleep(0.1)
      state_zonemode = 1 - state_zonemode
      print("zonemode " + str(state_zonemode))

#-------------

    ## first of all, checking if lifx power is on or not

    # if power is off, only power on switch function and indicator lights are active
    if state_power == 0:
      pass

    # if power is on, all functions are active
    if state_power == 1:

      if key.char == 'p':
        if ph_input_pot < 0.95:
          ph_input_pot += 0.1
          print("pot value " + str(ph_input_pot))
      if key.char == 'o':
        if ph_input_pot > 0.05:
          ph_input_pot -= 0.1
          print("pot value " + str(ph_input_pot))

      ## checking if strip is in zone mode or default mode and determine the behaviour of the controls in both

      # if zone mode is OFF
      if state_zonemode == 0:

        # Knob behaviour

        # if the color mode is off only temperature is adjusted
        if state_colormode == 0 and ph_input_pot != ph_input_pot_prev:
          strip.set_colortemp(map(ph_input_pot, (0.0, 1.0), (2500, 9000)), 0, False)
          ph_input_pot_prev = ph_input_pot

        # if the color mode is on, the 3-way switch selects which parameter is changed
        else:
          # if brightness mode
          if state_switch_brightness == 1 and ph_input_pot != ph_input_pot_prev:
            strip.set_brightness(65535 * ph_input_pot, 0, False)
            ph_input_pot_prev = ph_input_pot
          # if color mode
          elif state_switch_color == 1 and ph_input_pot != ph_input_pot_prev:
            strip.set_hue(65535 * ph_input_pot, 0, False)
            ph_input_pot_prev = ph_input_pot
          # if saturation mode
          elif state_switch_brightness == 0 and state_switch_color == 0 and ph_input_pot != ph_input_pot_prev:
            strip.set_saturation(65535 * ph_input_pot, 0, False)
            ph_input_pot_prev = ph_input_pot

        # TODO encoder behaviour here (randomizer)

      # if zone mode is ON
      else:

        if key.char == 'c':
          if selected_zone < zone_count:
            strip.set_zone_color(selected_zone, selected_zone, zone_set_color, 0, 1, 1)
            selected_zone += 1
            print("selected zone " + str(selected_zone))
            print(zone_set_color)
        if key.char == 'x':
          if selected_zone > 0:
            strip.set_zone_color(selected_zone, selected_zone, zone_set_color, 0, 1, 1)
            selected_zone -= 1
            print("selected zone " + str(selected_zone))

        # Knob behaviour

        # if the color mode is off only temperature is adjusted
        if state_colormode == 0 and ph_input_pot != ph_input_pot_prev:
          zone_set_color[3] = map(ph_input_pot, (0.0, 1.0), (2500, 9000))
          ph_input_pot_prev = ph_input_pot

        # if the color mode is on, the 3-way switch selects which parameter is changed
        else:
          # if brightness mode
          if state_switch_brightness == 1 and ph_input_pot != ph_input_pot_prev:
            zone_set_color[2] = 65535 * ph_input_pot
            ph_input_pot_prev = ph_input_pot
          # if color mode
          elif state_switch_color == 1 and ph_input_pot != ph_input_pot_prev:
            zone_set_color[0] = 65535 * ph_input_pot
            ph_input_pot_prev = ph_input_pot
          # if saturation mode
          elif state_switch_brightness == 0 and state_switch_color == 0 and ph_input_pot != ph_input_pot_prev:
            zone_set_color[1] = 65535 * ph_input_pot
            ph_input_pot_prev = ph_input_pot



        # TODO knob behaviour here
        # TODO encoder behaviour here
"""



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

  global zone_count

  ph_input_pot = 0.5 # TODO For now, i'm assuming the pot range as 0-1. Correct this as the actual connections are made.
  ph_input_pot_prev = ph_input_pot


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
  multizone_lights = lifx.get_multizone_lights()

  # finding the correct light to operate on
  if len(multizone_lights) > 0:
    global strip
    strip = multizone_lights[0]
    print("Selected {}".format(strip.get_label()))

    # saving the original zones
    original_zones = strip.get_color_zones()
    current_zones = deepcopy(original_zones)

    # the amount of zones in the light
    zone_count = len(original_zones)

  # if there's no light available...
  else:
    print("No multizone lights available")



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

    if count_halfsecond() == True:
      simplecounter += 1
      print(simplecounter)

    ## checking if strip is in zone mode or default mode and determine the behaviour of the controls in both

    # if zone mode is OFF
    if state_zonemode == 0:

      # Knob behaviour

      # if the color mode is off only temperature is adjusted
      if state_colormode == 0 and ph_input_pot != ph_input_pot_prev:
        strip.set_colortemp(map(ph_input_pot, (0.0, 1.0), (2500, 9000)), 0, False)
        ph_input_pot_prev = ph_input_pot

      # if the color mode is on, the 3-way switch selects which parameter is changed
      else:
        # if brightness mode
        if not GPIO.input(SWITCH_BRIGHTNESS) and ph_input_pot != ph_input_pot_prev:
          strip.set_brightness(65535 * ph_input_pot, 0, False)
          ph_input_pot_prev = ph_input_pot
        # if color mode
        elif not GPIO.input(SWITCH_COLOR) and ph_input_pot != ph_input_pot_prev:
          strip.set_hue(65535 * ph_input_pot, 0, False)
          ph_input_pot_prev = ph_input_pot
        # if saturation mode
        elif GPIO.input(SWITCH_BRIGHTNESS) and GPIO.input(SWITCH_COLOR) and ph_input_pot != ph_input_pot_prev:
          strip.set_saturation(65535 * ph_input_pot, 0, False)
          ph_input_pot_prev = ph_input_pot

    else:

      # Knob behaviour

      # if the color mode is off only temperature is adjusted
      if state_colormode == 0 and ph_input_pot != ph_input_pot_prev:
        zone_set_color[3] = map(ph_input_pot, (0.0, 1.0), (2500, 9000))
        ph_input_pot_prev = ph_input_pot

      # if the color mode is on, the 3-way switch selects which parameter is changed
      else:
        # if brightness mode
        if state_switch_brightness == 1 and ph_input_pot != ph_input_pot_prev:
          zone_set_color[2] = 65535 * ph_input_pot
          ph_input_pot_prev = ph_input_pot
        # if color mode
        elif state_switch_color == 1 and ph_input_pot != ph_input_pot_prev:
          zone_set_color[0] = 65535 * ph_input_pot
          ph_input_pot_prev = ph_input_pot
        # if saturation mode
        elif state_switch_brightness == 0 and state_switch_color == 0 and ph_input_pot != ph_input_pot_prev:
          zone_set_color[1] = 65535 * ph_input_pot
          ph_input_pot_prev = ph_input_pot

      # blinking behaviour

      if simplecounter >= 2:
        simplecounter = 0
        temp_color = zone_set_color
        temp_color[2] = 0
        strip.set_zone_color(selected_zone, selected_zone, temp_color, 0, 1, 1)
        print(temp_color)
      if simplecounter == 1 and temp_color[2] == 0:
        temp_color = zone_set_color
        temp_color[2] = 65535
        strip.set_zone_color(selected_zone, selected_zone, temp_color, 0, 1, 1)
        #print(temp_color)

  # TODO preset button behaviour


if __name__=="__main__":
  main()


