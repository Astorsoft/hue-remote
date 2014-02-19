#!/usr/bin/python
# -*- coding: UTF-8 -/-
import logging, logging.handlers, signal
from evdev import ecodes, InputDevice 
from phue import Bridge
from datetime import datetime
# Trackpad device, type "evtest" to list devices and  see which one to choose
TRACKPAD_DEVICE = "/dev/input/event4"
BRIDGE_IP = "192.168.0.11"
API_USERNAME = "HueBTSwitch"
LIGHT_GROUP = "Salon"
LOG_LEVEL = logging.DEBUG

class hueparam:
    def __init__(self, name, maxi, multiplier, modulo=False, mini = 0):
        self.name = str(name)
        self.maxi = int(maxi)
        self.multiplier = multiplier
        self.last_update = datetime.now()
        self.buff = 0
        self.mini = int(mini)
        self.modulo = bool(modulo)

    def __iadd__(self, val):
        """ add the device data taking into account max and modulo
        it also mark the hueparam as changed and register the datetime
        it has been changed
        """
        self.buff += int(val * self.multiplier)
        if self.modulo:
            self.buff = self.buff % self.maxi
        else:
        if self.buff > self.maxi:
            self.buff = self.maxi
        elif self.buff < self.mini:
    	    self.buff = self.mini
        return self

    def __repr__(self):
        """Return attributes as dict without methods"""
        return dict((key, getattr(self, key)) for key in dir(self) if key not in dir(self.__class__))

    def __str__(self):
        """return name and """
        return " ".join(["[hueparam]", self.name, ":", str(self.buff), "\t| last update :", str(self.last_update)]) 



def switch_lights(hue):
    """Switch all lights on if they are off, and vice versa"""
    is_on = hue.get_group(LIGHT_GROUP, "on")
    hue.set_group(LIGHT_GROUP, "on", not(is_on))

def change_param(hue, param, val):
    """Change a specific parameter of the lamps
    I'm delaying the update frequency as the device sends input much more
    rapidly than the Philips Hue api is able to handle

    I'm using set_light instead of set_group for the same reason, e.g :
    "We can’t send commands to the lights too fast. If you stick to around
     10 commands per second to the /lights resource as maximum you should be fine.
     For /groups commands you should keep to a maximum of 1 per second."
    http://developers.meethue.com/coreconcepts.html
    """
    param += val
    if (datetime.now() - param.last_update).microseconds > 100000:
        curr_val = hue.get_light(2, param.name)
        if curr_val != param.buff:
            logger.debug(param)
            for i in range(1,4):
	            hue.set_light(i, param.name, param.buff)
            param.last_update = datetime.now()


def change_theme(hue, themes, index):
    theme_name = themes.keys()[theme_index]
    th = themes[theme_name]
    size = len(th)
    logger.debug("***Changing theme to " + theme_name + "***")

    for i in [1,2,3]:
        lamp_th = th[i % size]
        if lamp_th.has_key("xy"):
            hue.set_light(i, "xy", [lamp_th["xy"][0], lamp_th["xy"][1]])
        elif lamp_th.has_key("ct"):
            hue.set_light(i, "ct", lamp_th["ct"])
        elif lamp_th.has_key("hue"):
            hue.set_light(i, "hue", lamp_th["hue"])
        if lamp_th.has_key("sat"):
            hue.set_light(i, "sat", lamp_th["sat"])



if __name__ == "__main__":

    remote = InputDevice(TRACKPAD_DEVICE)
    remote.grab()
    hue = Bridge(BRIDGE_IP, API_USERNAME)
    logger = logging.getLogger("hue-remote")
    logger.setLevel(LOG_LEVEL)
    logfile = logging.handlers.RotatingFileHandler("/var/log/hue-remote/hue-remote.log", maxBytes=50000, backupCount=2)
    logformat = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    logfile.setFormatter(logformat)
    logger.addHandler(logfile)

    themes = dict()
    themes["relax"] = [{"ct": 2431}]
    themes["energize"] = [{"ct": 6474}]
    themes["deep_sea"] = [{"xy": (0.1859, 0.0771)}, {"xy": (0.6367, 0.3349)}, {"xy": (0.1859, 0.0771)}]
    themes["blue_rain"] = [{"xy": (0.1859, 0.0771)}]
    themes["laila"] = [{"xy": (0.4071, 0.514)}, {"ct": 3861}, {"xy": (0.4071, 0.514)}]
    themes["sunset"] = [{"ct": 2535}, {"xy": (0.6349, 0.3413)}, {"ct": 2535}]
    themes["love_shack"] = [{"hue": 53498, "sat": 254}, {"hue": 48401, "sat": 254}, {"hue": 53498, "sat": 254}] 
    themes["ultraviolet"] = [{"hue": 45831, "sat": 254}, {"hue": 48401, "sat": 254}, {"hue": 50671, "sat": 254}] 
    themes["candles"] = [{"hue": 4326, "sat": 254}, {"hue": 2141, "sat": 254}, {"hue": 4326, "sat": 254}]
    theme_index = 0

    params = dict()
    params["brightness"] = hueparam("bri", 255, 4)
    params["hue"] = hueparam("hue", 65535, 20, modulo=True)
    params["saturation"] = hueparam("sat", 255, 1)
    #params["temperature"] = hueparam("ct", 500, 2, mini=153) 
    #params["cie_x"] = hueparam("xy", 1.0, 0.001, isfloat=True)
    #params["cie_y"] = hueparam("xy", 1.0, 0.001, isfloat=True)

    for event in remote.read_loop():
        if event.type in [ecodes.EV_KEY, ecodes.EV_REL]:
            if event.code == ecodes.BTN_RIGHT and event.value == 1:
                logger.debug("Switching lights")
                switch_lights(hue)
            elif event.code == ecodes.BTN_LEFT:
                print("todo")
            elif event.code == ecodes.BTN_SIDE and event.value == 1: 
            # 3 doigts de droite à gauche
                theme_index = (theme_index - 1) % len(themes)
                change_theme(hue, themes, theme_index)
            elif event.code == ecodes.BTN_EXTRA and event.value == 1: 
            # 3 doigts de gauche ) droite
                theme_index = (theme_index + 1) % len(themes)
                change_theme(hue, themes, theme_index)
            elif event.code == ecodes.KEY_PAGEUP: 
            # 3 doigts de bas en haut
                print("todo")
            elif  event.code == ecodes.KEY_PAGEDOWN: 
            # 3 doigts de haut en bas
                print("todo")
            elif event.code == ecodes.REL_WHEEL: 
            # 2 doigt à la verticale
                change_param(hue, params["brightness"], event.value)
            elif event.code == ecodes.REL_Y:
                change_param(hue, params["saturation"], event.value)
            elif event.code == ecodes.REL_X:
                change_param(hue, params["hue"], event.value) 
