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
from encoder import Encoder
import urllib.request
import numpy as np

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
BTN_ENC = 26

# set state variables
state_power = 1
state_zonemode = 0
state_colormode = 0

prev_time = math.floor(time.time()*10)

general_color = [0, 0, 65535, 3500]
temp_color = [0, 0, 65535, 3500]
zone_set_color = [0, 0, 65535, 3500]
selected_zone = 0

selected_preset = 0;


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
    print("power set to " + str(state_power))
  else:
    print("Power switch off!")
    strip.set_power("off", True)
    state_power = 0
    print("power set to " + str(state_power))


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

    ## use this for reboot later
    #os.execl(sys.executable, sys.executable, *sys.argv)


def btn_preset_cb(channel):
  if state_power == 1 and GPIO.input(BTN_PRESET) == 0:
    global selected_preset

    print("Preset button pressed!")
    GPIO.output(LED_PRESET, GPIO.LOW)

    prst = np.loadtxt("preset_" + str(selected_preset) + ".txt", dtype=int)
    strip.set_zone_colors(prst, 0, True)
    if selected_preset < 3:
      selected_preset += 1
    else:
      selected_preset = 0

  if state_power == 1 and GPIO.input(BTN_PRESET) == 1:
    GPIO.output(LED_PRESET, GPIO.HIGH)


def btn_enc_cb(channel):
  if state_power == 1 and GPIO.input(BTN_ENC) == 0:
    print("Encoder button pressed!")


def enc_cb(value, direction):
  print("Encoder turned!")
  global selected_zone

  # first of all, check if lifx power is on or not and do nothing if not
  if state_power == 1:

    # if zone mode is OFF
    if state_zonemode == 0:

      rand_hue = 0
      prob = random.random()
      if prob < 0.3:
          rand_hue = random.randint(0, 65535)
      elif prob <= 0.6:
          rand_hue = random.randint(52428, 58981)
      else:
          rand_hue = random.randint(0, 16383)

      rand_color = [rand_hue, random.randint(0, 65535), 65535, 3500]

      rand_zone = random.randint(0, zone_count)
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

  print("* New value encoder 2: {}, Direction: {}".format(value, direction))


def enc_vb(value, direction):
  print("Encoder turned!")
  global selected_zone

  # first of all, check if lifx power is on or not and do nothing if not
  if state_power == 1:

    # check encoder direction and assign + or -
    if direction == "R":
      dir = 1
    else: # better than elif direction == "L":
      dir = -1

    # if zone mode is OFF
    if state_zonemode == 0:

      # if the color mode is off only temperature is adjusted
      if state_colormode == 0:
        general_color[3] = clamp(general_color[3] + (100 * dir), 2500, 9000)

      # if the color mode is on, the 3-way switch selects which parameter is changed
      else:
        # if brightness mode
        if GPIO.input(SWITCH_BRIGHTNESS):
          general_color[2] = clamp(general_color[2] + (100 * dir), 0, 65535)
        # if color mode
        elif GPIO.input(SWITCH_COLOR):
          general_color[0] = clamp(general_color[0] + (100 * dir), 0, 65535)
        # if saturation mode
        elif not GPIO.input(SWITCH_BRIGHTNESS) and not GPIO.input(SWITCH_COLOR):
          general_color[1] = clamp(general_color[1] + (100 * dir), 0, 65535)

      strip.set_color(general_color, 200, True)

    # if zone mode is ON
    else:

      # if the color mode is off only temperature is adjusted
      if state_colormode == 0:
        zone_set_color = clamp(zone_set_color[3] + (100 * dir), 2500, 9000)

      # if the color mode is on, the 3-way switch selects which parameter is changed
      else:
        # if brightness mode
        if GPIO.input(SWITCH_BRIGHTNESS):
          zone_set_color = clamp(zone_set_color[2] + (100 * dir), 0, 65535)
        # if color mode
        elif GPIO.input(SWITCH_COLOR):
          zone_set_color = clamp(zone_set_color[0] + (100 * dir), 0, 65535)
        # if saturation mode
        elif not GPIO.input(SWITCH_BRIGHTNESS) and not GPIO.input(SWITCH_COLOR):
          zone_set_color = clamp(zone_set_color[1] + (100 * dir), 0, 65535)

      strip.set_zone_color(selected_zone, selected_zone, zone_set_color, 0, 1, 1)


  print("* New value encoder 1: {}, Direction: {}".format(value, direction))
  print(dir)


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

def clamp(n, minn, maxn):
    if n < minn:
        return minn
    elif n > maxn:
        return maxn
    else:
        return n



# main function --------------------------------------------


def main():

  ########################
  #### Initialization ####
  ########################

  global zone_count
  global selected_preset

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
  try:
    original_powers = lifx.get_power_all_lights()
  except:
    print("Couldn't get powers from lights, something might be wrong.")

  print ("Starting program.")

  # get devices
  for x in range(100):
    if len(lifx.get_multizone_lights()) > 0:
      multizone_lights = lifx.get_multizone_lights()
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
  GPIO.setup(BTN_ENC, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(LED_ZONE,GPIO.OUT)
  GPIO.setup(LED_COLOR,GPIO.OUT)
  GPIO.setup(LED_PRESET,GPIO.OUT)

  GPIO.add_event_detect(SWITCH_POWER, GPIO.BOTH, callback=btn_power_on_cb, bouncetime=10)
  GPIO.add_event_detect(BTN_ZONE, GPIO.RISING, callback=btn_zonemode_cb, bouncetime=10)
  GPIO.add_event_detect(BTN_COLOR, GPIO.RISING, callback=btn_colormode_cb, bouncetime=10)
  GPIO.add_event_detect(BTN_PRESET, GPIO.BOTH, callback=btn_preset_cb, bouncetime=10)
  GPIO.add_event_detect(BTN_ENC, GPIO.BOTH, callback=btn_enc_cb, bouncetime=10)

  enc1 = Encoder(25, 4, enc_vb)
  enc2 = Encoder(21, 12, enc_cb)


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

    ## checking if strip is in zone mode or default mode and determine the behaviour of the controls in both

    # if zone mode is OFF
#    if state_zonemode == 0:
#
#        # if pot was turned
#        if trim_pot_changed:
#
#          print(trim_pot)
#
#          # Knob behaviour
#
#          # if the color mode is off only temperature is adjusted
#          if state_colormode == 0:
#            if trim_pot <= 30767:
#              general_color[3] = map(trim_pot, (0, 30767), (2500, 3500))
#            elif trim_pot > 34767:
#              general_color[3] = map(trim_pot, (34767, 65535), (3500, 9000))
#
#          # if the color mode is on, the 3-way switch selects which parameter is changed
#          else:
#            # if brightness mode
#            if GPIO.input(SWITCH_BRIGHTNESS):
#              general_color[2] = trim_pot
#            # if color mode
#            elif GPIO.input(SWITCH_COLOR):
#              general_color[0] = trim_pot
#            # if saturation mode
#            elif not GPIO.input(SWITCH_BRIGHTNESS) and not GPIO.input(SWITCH_COLOR):
#              general_color[1] = trim_pot
#
#          strip.set_color(general_color, 200, True)
#
#          # save the potentiometer reading for the next loop
#          last_read = trim_pot


    # if zone mode is ON
#    elif state_zonemode == 1:
#
#        # if pot was turned
#        if trim_pot_changed:
#
#          print(trim_pot)
#
#          # Knob behaviour
#
#          # if the color mode is off only temperature is adjusted
#          if state_colormode == 0:
#            if trim_pot <= 30767:
#              zone_set_color[3] = map(trim_pot, (0, 30767), (2500, 3500))
#            elif trim_pot > 34767:
#              zone_set_color[3] = map(trim_pot, (34767, 65535), (3500, 9000))
#
#          # if the color mode is on, the 3-way switch selects which parameter is changed
#          else:
#            # if brightness mode
#            if GPIO.input(SWITCH_BRIGHTNESS):
#              zone_set_color[2] = trim_pot
#            # if color mode
#            elif GPIO.input(SWITCH_COLOR):
#              zone_set_color[0] = trim_pot
#            # if saturation mode
#            elif not GPIO.input(SWITCH_BRIGHTNESS) and not GPIO.input(SWITCH_COLOR):
#              zone_set_color[1] = trim_pot
#
#          strip.set_zone_color(selected_zone, selected_zone, zone_set_color, 0, 1, 1)
#
#
#          # save the potentiometer reading for the next loop
#          last_read = trim_pot


    ## preset save

    if GPIO.input(BTN_PRESET) == 1:
      # counter
      if count_halfsecond() == True:
        simplecounter += 1
        #print(simplecounter)
      if simplecounter > 3:
        try:
          prst = strip.get_color_zones(0, zone_count)
        except:
          print("couldn't get zones for preset")
        else:
          np.savetxt("preset_" + str(selected_preset) + ".txt", prst, fmt='%d')
          print("Preset saved to")
          print(selected_preset)
    elif GPIO.input(BTN_PRESET) == 0:
      if simplecounter > 0:
        simplecounter = 0



    sleep(0.01)

if __name__=="__main__":
  main()


