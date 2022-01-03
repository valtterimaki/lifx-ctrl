#!/usr/bin/env python
import sys
from lifxlan import *
from copy import deepcopy
from time import sleep
from random import *
import keyboard

global strip

#def directionchange(val, dir):
#    x = 1
#    if val >= 65535 and dir == 1:
#        x = 0
#    if val <= 0 and dir == 0:
#        x = 1
#    return x

class Star:

    def __init__(self, zonenumber):
        self.zonenumber = zonenumber
        self.brightness = randint(0, 65535)

    def glitter(self):
        if self.brightness <=  30000:
            self.brightness = randint(30001, 65535)
        else:
            self.brightness = randint(0, 30000)

        color = [0, 0, self.brightness, randint(2500, 9000)]
        strip.set_zone_color(self.zonenumber, self.zonenumber, color, 2000, True, 1)

        checker = self.brightness


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

    print("Turning lights on...")
    lifx.set_power_all_lights("on")

    print ("Magic happens now:")

    # get devices
    multizone_lights = lifx.get_multizone_lights()

    delay = 0.05

    if len(multizone_lights) > 0:
        global strip
        strip = multizone_lights[0]
        print("Selected {}".format(strip.get_label()))

        # naa on alkuperasta varia varten
        original_zones = strip.get_color_zones()

        # tassa loudetaan zonejen maara
        zone_count = len(original_zones)

        # stars = [Star(i) for i in range(zone_count)]
        # 

    else:
        print("No multizone lights available")

    while True:

        #randomlist = list(range(zone_count))
        #print(randomlist)
        #shuffle(randomlist)
        #for i in range(zone_count):
        #    stars[randomlist[i]].glitter()
        #    sleep(delay)

        if keyboard.read_key() == "a":
            print("Copying all zones to memory A")
            memory_a = strip.get_color_zones()
        if keyboard.read_key() == "b":
            print("Copying all zones to memory B")
            memory_b = strip.get_color_zones()

        if keyboard.read_key() == "s":
            print("Applying zones from memory A")
            strip.set_zone_colors(memory_a)
        if keyboard.read_key() == "n":
            print("Applying zones from memory B")
            strip.set_zone_colors(memory_b) 

        if keyboard.read_key() == "x":
            print("Resetting to original colors")
            strip.set_zone_colors(original_zones) 


if __name__=="__main__":
    main()
