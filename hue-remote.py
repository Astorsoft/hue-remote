#!/usr/bin/python
# -*- coding: UTF-8 -/-
import logging, logging.handlers
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
    return " ".join([self.name, ":", str(self.buff), "\t| last update :", str(self.last_update)]) 

def switch_lights(hue):
  is_on = hue.get_group(LIGHT_GROUP, "on")
  hue.set_group(LIGHT_GROUP, "on", not(is_on))

def change_param(hue, param, val):
  param += val
  if (datetime.now() - param.last_update).microseconds > 100000:
    curr_val = hue.get_group(LIGHT_GROUP, param.name)
    if curr_val != param.buff:
      logger.debug(param)
      for i in range(1,4):
	hue.set_light(i, param.name, param.buff)
      param.last_update = datetime.now()
      param.changed = False


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

  params = dict()
  params["brightness"] = hueparam("bri", 255, 4)
  params["hue"] = hueparam("hue", 65535, 20, modulo=True)
  params["saturation"] = hueparam("sat", 255, 1)
  #params["temperature"] = hueparam("ct", 500, 2, mini=153) 
  #params["cie_x"] = hueparam("xy", 1.0, 0.001, isfloat=True)
  #params["cie_y"] = hueparam("xy", 1.0, 0.001, isfloat=True)

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
        change_param(hue, params["brightness"], event.value)
      elif event.code == ecodes.REL_Y:
        change_param(hue, params["saturation"], event.value)
      elif event.code == ecodes.REL_X:
        change_param(hue, params["hue"], event.value) 
