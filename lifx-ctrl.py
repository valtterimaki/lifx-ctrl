#!/usr/bin/env python
import sys
from lifxlan import *
from copy import deepcopy
from time import sleep
from random import *

global strip

ph_input_power = 1
ph_input_zonemode = 0
ph_input_colormode = 0
ph_input_pot = 1
ph_input_switch_temperature = 1
ph_input_switch_color = 0
ph_input_encoder = 0
ph_input_preset = 0

def main():

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
    all_zones = strip.get_color_zones()
    original_zones = deepcopy(all_zones)

    # the amount of zones in the light
    zone_count = len(all_zones)

  # if there's no light available...
  else:
    print("No multizone lights available")


  #######################################
  #### actual running program itself ####
  #######################################

  while True:

    ## first of all, checking if lifx power is on or not

    # if power is off, only power on switch function and indicator lights are active
    if strip.get_power() == 0:

      # if power switch is turned ON
      if ph_input_power == 1:
        strip.set_power("on")
        print("power on")
        sleep(0.1)

    # if power is on, all functions are active
    if strip.get_power() == 65535:

      # if power switch is turned OFF
      if ph_input_power == 0:
        strip.set_power("off")
        print("power off")
        sleep(0.1)

      ## checking if strip is in zone mode or default mode and determine the behaviour of the controls in both

      # if zone mode is OFF
      if ph_input_zonemode == 0:

        # if the color mode is off only brightness is adjusted
        if ph_input_colormode == 0:
          pass

        # if the color mode is on, the 3-way switch selects which parameter is changed
        else:
          # if temperature mode
          if ph_input_switch_temperature == 1:
            pass
          # if color mode
          elif ph_input_switch_color == 1:
            pass
          # if saturation mode
          else:
            pass

        # TODO encoder behaviour here (randomizer)

      # if zone mode is ON
      else:
        # TODO knob behaviour here
        # TODO encoder behaviour here
        pass


      # TODO preset button behaviour



if __name__=="__main__":
  main()
