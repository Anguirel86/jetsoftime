from shutil import copyfile
import os
from os import stat
import random as rand
import struct as st
import sys

# add the source files directory to the path so we can
# use the base randomizer code.
sys.path.append('../')
import bossscaler as boss_scale
import characterwriter as cw
import enemywriter as enemystuff
import ipswriter as bigpatches
import logicwriter
import patcher as patches
import shopwriter as shops
import specialwriter
import techwriter as tech_order
import treasurewriter

import keyitems
import treasures

#
# A quick, hacky script to dump a spoiler log of treasures.
#
def createSpoilerLog(romfile):
  
  reader = open(romfile, 'rb')
  try:
    # loop through the treasure list, read values and print them\
    print("Treasures")
    for pointer in treasurewriter.allpointers:
      locationName = treasures.getNameFromPointer(pointer)
      if not locationName == "":
        reader.seek(pointer)
        treasureCode = int.from_bytes(reader.read(1), byteorder='big', signed=False)
        treasureName = treasures.getTreasureNameFromValue(treasureCode)
        if treasureName == "":
          print("Unknown treasure value:" + hex(treasureCode,) + " at: " + locationName)
        else:
          print(locationName + ": " + treasureName)
      else:
        print("Unknown Location pointer: " + hex(pointer))
        
    # loop through the sealed chests
    print("Sealed Chests")
    it = iter(specialwriter.sealed_pointers)
    pointer_pairs = zip(it, it)
    for pointers in pointer_pairs:
      locationName = treasures.getSealedChestNameFromPointer(pointers[0])
      if not locationName == "":
        reader.seek(pointers[0])
        treasureCode = int.from_bytes(reader.read(1), byteorder='big', signed=False)
        treasureName = treasures.getTreasureNameFromValue(treasureCode)
        if treasureName == "":
          print("Unknown treasure value:" + hex(treasureCode,) + " at: " + locationName)
        else:
          print(locationName + ": " + treasureName)
      else:
        print("Unknown Location pointer: " + hex(pointers[0]))
    
  finally:
    reader.close()

##############    
#### Main ####
##############

inputRom = input("Enter ROM")
inputRom = inputRom.strip("\"")
createSpoilerLog(inputRom)