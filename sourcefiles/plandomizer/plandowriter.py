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
import specialwriter as hardcoded_items
import techwriter as tech_order
import treasurewriter as treasures


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
  handlEnemyLoot(datastore)
  handleShops(datastore)
  handleTechs(datastore)
  applyMiscFixes(datastore)


def read_names():
  p = open("../names.txt","r")
  names = p.readline()
  names = names.split(",")
  p.close
  return names  
  
  
#
# Function to handle enemy loot
#  
def handlEnemyLoot(datastore):
  outfile = datastore.outputFile
  enemystuff.randomize_enemy_stuff(outfile)
  

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
  # TODO: full rando for now, need to implement plando
  outfile = datastore.outputFile
  treasures.randomize_treasures(outfile)
  hardcoded_items.randomize_hardcoded_items(outfile)
  
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
  if datastore.flags['p'].get == 1 and datastore.flags['l'].get() != 1:
    # Fast pendant charge
    patches.patch_file("patches/fast_charge_pendant.txt",outfile)


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
def handleKeyItemsAndBossScaling(datastore):
  # TODO: implement key item plando
  outfile = datastore.outputFile
  locked_chars = ""
  if datastore.flags['c'].get() == 1:
    locked_chars = "Y"
    
  if datastore.flags['l'].get() == 1:
    keyitems = logicwriter.randomize_lost_worlds_keys(datastore.charToLocMap,outfile)
  else:
    keyitems = logicwriter.randomize_keys(datastore.charToLocMap,outfile,locked_chars)
  
  if datastore.flags['b'].get() == 1:
    boss_scale.scale_bosses(datastore.charToLocMap,keyitems,locked_chars,outfile)
  
  
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



  
  







