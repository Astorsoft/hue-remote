#!/usr/bin/python
# -*- coding: UTF-8 -/-
import evdev, phue, logging
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
  def __init__(self, name, maxi, multiplier, modulo=False):
    self.name = str(name)
    self.maxi = float(maxi)
    self.multiplier = float(multiplier)
    self.modulo = bool(modulo)
    self.changed = False
    self.last = None
    self.buff = 0.0

  def __iadd__(self, val):
    """ add the device data taking into account max and modulo
    it also mark the hueparam as changed and register the datetime
    it has been changed
    """
    self.buff += float(val) * self.multiplier
    if modulo:
      self.buff = self.buff % self.modulo
    else:
      if self.buff > self.maxi:
        self.buff = self.maxi
      elif self.buff < 0.0:
    	self.buff = 0.0
    self.last = datetime.now()


  def __reprr__(self):
    """Return attributes as strigified dict without methods"""
    return str(dict((key, getattr(self, key)) for key in dir(self) if key not in dir(self.__class__)))






remote = InputDevice(TRACKPAD_DEVICE)
remote.grab()
hue = Bridge(BRIDGE_IP, API_USERNAME)
logger = logging.getLogger("remote-hue")
logger.setLevel(LOG_LEVEL)
logfile = logging.FileHandler("/var/log/remote-hue.log")
logformat = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
logfile.setFormatter(logformat)
logger.addHandler(logfile)

wheel_offset = 0
x_offset = 0.0
y_offset = 0.0
hue_offset = 0
sat_offset = 0

def switch_lights(hue):
  is_on = hue.get_group(LIGHT_GROUP, "on")
  hue.set_group(LIGHT_GROUP, "on", not(is_on))

def change_brightness(hue, val):
  global wheel_offset
  wheel_offset += val * 4
  
  if (wheel_offset >= 20 or wheel_offset <= -20):
    curr_bri = hue.get_group(LIGHT_GROUP, "bri")
    new_bri = curr_bri + wheel_offset
    if new_bri > 255:
      new_bri = 255
    if new_bri < 0:
      new_bri = 0
    
    if curr_bri != new_bri:
      logger.debug("Increase bri (" + str(curr_bri) + ") by " + str(wheel_offset))
      #hue.set_group(LIGHT_GROUP, "bri", curr_bri + wheel_offset)
      for i in [1,2,3]:
        hue.set_light(i, "bri", new_bri)
  
  if not(-20 <= wheel_offset <= 20):
    wheel_offset = 0  
 

def change_cie(hue, val, code):
  global x_offset, y_offset
  if code == ecodes.REL_X:
    x_offset += val / 1000.0
  else:
    y_offset += val / 1000.0
  
  if (x_offset >= 0.02) or (x_offset <= -0.02) or (y_offset >= 0.02) or (y_offset <= -0.02):
    curr_x, curr_y = hue.get_group(LIGHT_GROUP, "xy")
    new_x = curr_x + x_offset

    if new_x > 1.0:
      new_x = 1.0
    if new_x < 0.0:
      new_x = 0.0      
    
    new_y = curr_y + y_offset
    if new_y > 1.0:
      new_y = 1.0
    if new_y < 0.0:
      new_y = 0.0

    #hue.set_group(LIGHT_GROUP, "xy", [new_x, new_y])
    logger.debug("Change  x,y (" + str(curr_x) + "," + str(curr_y) + ") to (" + str(new_x) + ";" + str(new_y) + ")")
    for i in [1,2,3]:
      hue.set_light(i, "xy", [new_x, new_y])
    x_offset = 0.0
    y_offset = 0.0

def change_hue(hue, val):
  global hue_offset
  hue_offset += val * 20 

  if (hue_offset >= 200) or (hue_offset <= -200):
    curr_hue = hue.get_group(LIGHT_GROUP, "hue")
    new_hue = (curr_hue + hue_offset) % 65535
    if new_hue < 0:
      new_hue += 65535
    logger.debug("Change hue from " + str(curr_hue) + " to " + str(new_hue))
    for i in [1,2,3]:
      hue.set_light(i, "hue", new_hue)

  if not(-500 <= hue_offset <= 500):
    hue_offset = 0

  
def change_sat(hue, val):
  global sat_offset
  sat_offset += val

  if (sat_offset >= 20 or sat_offset <= -20):
    curr_sat = hue.get_group(LIGHT_GROUP, "sat")
    new_sat = curr_sat + sat_offset
    if new_sat > 255:
      new_sat = 255
    if new_sat < 0:
      new_sat = 0
      
    if new_sat != curr_sat:
      logger.debug("Change sat from " + str(curr_sat) + " to " + str(new_sat))
      #hue.set_group(LIGHT_GROUP, "bri", curr_bri + wheel_offset)
      for i in [1,2,3]:
        hue.set_light(i, "sat", new_sat)

  if not(-20 <= sat_offset <= 20):
    sat_offset = 0

for event in remote.read_loop():
  if event.type in [ecodes.EV_KEY, ecodes.EV_REL]:
    if event.code == ecodes.BTN_RIGHT:
      if event.value == 1:
        logger.debug("BTN_RIGHT")
        switch_lights(hue)
    elif event.code == ecodes.BTN_LEFT:
	    print("todo")
    elif event.code == ecodes.BTN_SIDE: 
      # 3 doigts de droite à gauche
	    print("todo")
    elif event.code == ecodes.BTN_EXTRA: 
      # 3 doigts de gauche ) droite
	    print("todo")
    elif event.code == ecodes.KEY_PAGEUP: 
      # 3 doigts de bas en haut
	    print("todo")
    elif  event.code == ecodes.KEY_PAGEDOWN: 
      # 3 doigts de haut en bas
	    print("todo")
    elif event.code == ecodes.REL_WHEEL: 
      # 2 doigt à la verticale
      logger.debug("2 Doigt, Vertical, " + str(event.value) + " wheel_offset=" + str(wheel_offset))
      change_brightness(hue, event.value)
    #elif event.code in [ecodes.REL_Y, ecodes.REL_X] : # coordonnés X Y un doigt
      #change_cie(hue, event.value, event.code)
    elif event.code == ecodes.REL_Y:
      change_sat(hue, event.value)
    elif event.code == ecodes.REL_X:
      change_hue(hue, event.value)  
