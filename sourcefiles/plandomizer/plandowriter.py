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
# Function to generate the plandomized output ROM  
#
def plandomize(datastore):
  
  if not datastore.validate():
    # TODO: handle validation failure
    print("Validation failed")

  inputfile = datastore.inputFilePath.get()
  path = os.path.dirname(inputfile)
  
  # Generate a seed if one wasn't specified
  if datastore.seed.get() is None or datastore.seed.get() == "":
    names = read_names()
    datastore.seed.set("".join(rand.choice(names) for i in range(2)))
  
  rand.seed(datastore.seed.get()) 
  
  datastore.outputFile = path + os.path.sep + "plando_" + datastore.seed.get() + ".sfc"
  
  # make a copy of the ROM and strip ROM header if one is present
  size = stat(inputfile).st_size
  if size % 0x400 == 0:
    copyfile(inputfile, datastore.outputFile)
  elif size % 0x200 == 0:
    f = open(inputfile, 'r+b')
    data = f.read()
    f.close()
    data = data[0x200:]
    open(datastore.outputFile, 'w+').close()
    f = open(datastore.outputFile, 'r+b')
    f.write(data)
    f.close()
  
   
  # start applying settings
  applyFlagPatches(datastore)
  handleCharacters(datastore)
  handleKeyItemsAndBossScaling(datastore)
  handleTreasures(datastore)
  handleEnemyLoot(datastore)
  handleShops(datastore)
  handleTechs(datastore)
  applyMiscFixes(datastore)

#
# Read in the list of enemy names used to generate a random seed.
#
def read_names():
  p = open("../names.txt","r")
  names = p.readline()
  names = names.split(",")
  p.close
  return names  
  
  
#
# Function to handle enemy loot
#  
def handleEnemyLoot(datastore):
  outfile = datastore.outputFile
  enemystuff.randomize_enemy_stuff(outfile, datastore.difficulty.get())
  

#
# Handle placing shop items
#
def handleShops(datastore):
  outfile = datastore.outputFile
  shops.randomize_shops(outfile)


# handle tech randomization  
def handleTechs(datastore):
  outfile = datastore.outputFile
  
  if datastore.flags['te'].get() == 1:
    tech_order.take_pointer(outfile)
 
#
# Function to handle treasures
#
def handleTreasures(datastore):
  outfile = datastore.outputFile
  romFile = open(outfile, "r+b")
  
  # read in the treasure file
  treasureMap = {}
  # TODO add error handling for a blank or unreadable file
  with open(datastore.chestFilePath.get()) as file:
    for line in file.readlines():
      line = line.strip()
      if line == "" or line.startswith("#"):
        continue
      temp = line.split(":")
      treasureLocation = temp[0]
      treasureName = temp[1]
      if treasureName != "":
        if  treasureName in treasures.ItemNameToCodeMap.keys():
          treasureMap[treasureLocation] = treasureName
        else:
          print("Skipping Invalid Treasure: " + treasureName + " at location: " + treasureLocation)
  
  # Read in the sealed treasures file
  sealedChestMap = {}
  with open(datastore.sealedChestFilePath.get()) as file:
    for line in file.readlines():
      line = line.strip()
      if line == "" or line.startswith("#"):
        continue
      temp = line.split(":")
      chestLoc = temp[0]
      treasureName = temp[1]
      if treasureName in treasures.ItemNameToCodeMap.keys():
        sealedChestMap[chestLoc] = treasureName
      else:
        print("Skipping Invalid Treasure: " + treasureName + " at location: " + chestLoc) 
  
  # Loop through the full list of treasure pointers in the baseline randomizer
  # For each pointer, check if it's part of the treasure list we read in.
  # If it is, look up the user defined treasure and set it.  If the user didn't
  # define a treasure for that spot, use the baseline rando functionality to 
  # choose a treasure for us.
  for pointer in treasurewriter.allpointers:
    locationName = treasures.getNameFromPointer(pointer)
    treasureCode = 0
    if locationName == "" or not locationName in treasureMap.keys():
      # This chest isn't in the plando treasure list or
      # the user didn't specify a treasure for this chest
      treasureCode = treasurewriter.choose_item(pointer, datastore.difficulty.get())
    else:
      # The user specified a treasure for this chest
      treasureName = treasureMap[locationName]
      treasureCode = treasures.ItemNameToCodeMap[treasureName]
    
    # write the treasure
    romFile.seek(pointer-3)
    romFile.write(st.pack("B",0x00))
    romFile.seek(pointer)
    romFile.write(st.pack("B",treasureCode))
  

  # Sealed chests each have 2 pointers.  In the base rando code all pointers
  # are stored sequentially, with each pair making up a sealed chest.
  # Convert the list into a list of tuples.
  it = iter(specialwriter.sealed_pointers)
  pointer_pairs = zip(it, it)
  
  # Loop over the list of tuples, each one represents a chest
  for pointers in pointer_pairs:
    locationName = treasures.getSealedChestNameFromPointer(pointers[0])
    treasureCode = 0
    if locationName == "" or not locationName in sealedChestMap.keys():
      # This chest isn't in the sealed treasure list or
      # the user didn't specify a treasure for this chest
      treasureCode = rand.choice(specialwriter.sealed_treasures)
      treasureName = str(treasureCode)
    else:
      treasureName = sealedChestMap[locationName]
      treasureCode = treasures.ItemNameToCodeMap[treasureName]
  
    # write the treasure to the chest's memory locations
    romFile.seek(pointers[0])
    romFile.write(st.pack("B", treasureCode))
    romFile.seek(pointers[1])
    romFile.write(st.pack("B", treasureCode))
 
  # TODO:
  #  1) Taban's trade items
  #  2) Pre-history trading hut items
  #  3) Rocks
  #  4) Jerky trade item
  romFile.close()    
  
 
  
#
# Function to apply patches for the more straightforward flags
#
def applyFlagPatches(datastore):
  outfile = datastore.outputFile
  bigpatches.write_patch("../patch.ips",outfile)
  patches.patch_file("patches/patch_codebase.txt",outfile)
  if datastore.flags['g'].get() == 1: # disable glitches
    patches.patch_file("patches/save_anywhere_patch.txt",outfile)
    patches.patch_file("patches/unequip_patch.txt",outfile)
    patches.patch_file("patches/fadeout_patch.txt",outfile)
    patches.patch_file("patches/hp_overflow_patch.txt",outfile)
  if datastore.flags['s'].get() == 1: # Fast overworld
    patches.patch_file("patches/fast_overworld_walk_patch.txt",outfile)
    patches.patch_file("patches/faster_epoch_patch.txt",outfile)
  if datastore.flags['d'].get() == 1: # fast dpad in menus
    patches.patch_file("patches/faster_menu_dpad.txt",outfile)
  if datastore.flags['z'].get() == 1: # Zeal 2 is last boss
    patches.patch_file("patches/zeal_end_boss.txt",outfile)
  if datastore.flags['l'].get() == 1: # lost worlds
    bigpatches.write_patch("patches/lost.ips",outfile)  
  elif datastore.flags['p'].get() == 1: # Fast pendant charge
    patches.patch_file("patches/fast_charge_pendant.txt",outfile)
    print("Fast charge patch")


#
# Miscellaneous fixes
#
def applyMiscFixes(datastore):
  outfile = datastore.outputFile
  # Tyrano Castle chest hack
  f = open(outfile,"r+b")
  f.seek(0x35F6D5)
  f.write(st.pack("B",1))
  f.close()
  #Mystic Mtn event fix in Lost Worlds
  if datastore.flags['l'].get() == 1:         
    f = open(outfile,"r+b")
    bigpatches.write_patch("patches/mysticmtnfix.ips",outfile)
    f.close()
  
  
#
# Handle placing key items.
#
# TODO - Randomly place key items that user didn't choose a spot for
#        Handle lost worlds vs regular placement
#        Handle boss scaling
def handleKeyItemsAndBossScaling(datastore):
  outfile = datastore.outputFile
  locked_chars = ""
  if datastore.flags['c'].get() == 1:
    locked_chars = "Y"

  keyItemManager = keyitems.KeyItemManager()
  locationManager = keyitems.LocationManager()
  for locname, itemname in datastore.itemLocVars.items():
    if itemname.get() != "":
      # User chose an item for this spot, place it
      keyItem = keyItemManager.getKeyItem(itemname.get())
      location = locationManager.getLocation(locname)
      f = open(outfile, "r+b")
      f.seek(location.memloc1)
      f.write(st.pack("B", keyItem.itemCode))
      f.seek(location.memloc2)
      f.write(st.pack("B", keyItem.itemCode))
      f.close()

  
  
#
# Handle placing characters based on the user's GUI selections
# stored in the datastore. If a character does not have a location
# specified then one will be assigned randomly
#
def handleCharacters(datastore):
  f = open(datastore.outputFile, "r+b")
  
  lost_worlds = ""
  if datastore.flags['l'].get() == 1:
    lost_worlds = "Y"
    
  locked_chars = ""
  if datastore.flags['c'].get() == 1:
    locked_chars = "Y"
  
  
  # Map to translate between display names and internal randomizer names
  charLocTranslationMap = {
      "Start1":"start", 
      "Start2":"start2", 
      "Cathedral":"cathedral", 
      "Guardia Castle":"castle", 
      "Proto Dome":"proto", 
      "Frog Burrow":"burrow", 
      "Dactyl Nest":"dactyl"}
  
  #Map of character display names to internal randomizer values
  characters = {
      "Crono":cw.chrono, 
      "Marle":cw.marle, 
      "Lucca":cw.lucca, 
      "Robo":cw.robo, 
      "Frog":cw.frog, 
      "Ayla":cw.ayla, 
      "Magus":cw.magus}
  charToLocMap = {"start": "", "start2": "", "cathedral": "", "castle": "", "proto": "", "burrow": "", "dactyl": ""}  
  # Determine which characters weren't given a starting location
  missingChars = []
  for char, loc in datastore.charLocVars.items():
    locName = loc.get()
    if locName == "":
      # No location specified for this character
      missingChars.append(characters[char])
    else:  
      charToLocMap[charLocTranslationMap[locName]] = characters[char]
      
  # assign random locations for characters without one specified
  for loc, char in charToLocMap.items():
    if char == "":
      chosenChar = rand.choice(missingChars)
      charToLocMap[loc] = chosenChar
      missingChars.remove(chosenChar)
  
  # Save the map to the datastore. Later steps need it.
  datastore.charToLocMap = charToLocMap
  # Now assign stats for each character based on location
  for loc, char in charToLocMap.items():
    cw.set_stats(f, char, loc, lost_worlds)
  
  # Finally, write the characters to the ROM  
  cw.write_chars(f, charToLocMap, locked_chars, lost_worlds, datastore.outputFile)

