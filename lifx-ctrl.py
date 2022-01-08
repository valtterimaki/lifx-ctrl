#!/usr/bin/env python
import sys
from lifxlan import *
from copy import deepcopy
from time import sleep
from random import *
from pynput import keyboard

global strip

# state variables
state_power = 0
state_zonemode = 0
state_colormode = 0
state_switch_temperature = 1
state_switch_color = 0
state_preset = 0

ph_input_pot = 0.0 # TODO For now, i'm assuming the pot range as 0-1. Correct this as the actual connections are made.

# Keyboard input placeholder to simulate GPIO inputs
# TODO replace with actual gpio stuff
def on_press(key):
    try:
      pass
        #print('alphanumeric key {0} pressed'.format(key.char))
    except AttributeError:
        #print('special key {0} pressed'.format(key))
        pass

def on_release(key):

    # placeholder variable to simulate pot reading
    global ph_input_pot

    #print('{0} released'.format(key))
    if key == keyboard.Key.esc:
        # Stop listener
        return False
    if 'char' in dir(key):
      if key.char == 'q':
        strip.set_power("on", True)
        state_power = 1
        print("power " + str(state_power))
      if key.char == 'a':
        strip.set_power("off", True)
        state_power = 0
        print("power " + str(state_power))
      if key.char == 'p':
        if ph_input_pot < 0.95:
          ph_input_pot += 0.1
          print("pot value " + str(ph_input_pot))
      if key.char == 'o':
        if ph_input_pot > 0.05:
          ph_input_pot -= 0.1
          print("pot value " + str(ph_input_pot))

def map(val, src, dst):
    # Map the given value from the scale of src to the scale of dst.
    return ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]


def main():

  ########################
  #### Initialization ####
  ########################

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

  # check the power and set the state variable accordingly
  if strip.get_power() == 65535:
    state_power = 1

  #######################################
  #### actual running program itself ####
  #######################################


  while True:

    # Collect keyboard events until released
    with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
      listener.join()

    ## first of all, checking if lifx power is on or not

    # if power is off, only power on switch function and indicator lights are active
    if state_power == 0:
      pass

    # if power is on, all functions are active
    if state_power == 1:

      ## checking if strip is in zone mode or default mode and determine the behaviour of the controls in both

      # if zone mode is OFF
      if state_zonemode == 0:

        # if the color mode is off only brightness is adjusted
        if state_colormode == 0:
          strip.set_brightness(65535 * ph_input_pot, 0, False)
          print("test")

        # if the color mode is on, the 3-way switch selects which parameter is changed
        else:
          # if temperature mode
          if state_switch_temperature == 1:
            strip.set_colortemp(map(ph_input_pot, (0.0, 1.0), (2500, 9000)), 0, False)
          # if color mode
          elif state_switch_color == 1:
            strip.set_hue(65535 * ph_input_pot, 0, False)
          # if saturation mode
          else:
            strip.set_saturation(65535 * ph_input_pot, 0, False)

        # TODO encoder behaviour here (randomizer)

      # if zone mode is ON
      else:
        # TODO knob behaviour here
        # TODO encoder behaviour here
        pass


      # TODO preset button behaviour


if __name__=="__main__":
  main()


