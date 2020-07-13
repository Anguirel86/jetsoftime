

#
# This class represents a key item
#
class KeyItem:
  def __init__(self, name, itemCode):
    self.name = name
    self.itemCode = itemCode
	 
	 
#
# This class represents a key item location, including the item 
# name and its memory addresses.
#
class Location:
  def __init__(self, name, memloc1, memloc2):
    self.name = name
    self.memloc1 = memloc1
    self.memloc2 = memloc2
    self.item = None
	 
class KeyItemManager:
  def __init__(self):
    self.resetKeyItems()
	 
  def resetKeyItems(self):
    self.keyItems = {
      "Toma's Pop": KeyItem("Toma's Pop", 0xE3),
      "Bent Hilt": KeyItem("Bent Hilt", 0x51),
      "Bent Blade": KeyItem("Bent Blade", 0x50),
      "Dreamstone": KeyItem("Dreamstone", 0xDC),
      "Ruby Knife": KeyItem("Ruby Knife", 0xE0),
      "Gate Key": KeyItem("Gate Key", 0xD7),
      "Jerky":KeyItem("Jerky", 0xDB),
      "Pendant": KeyItem("Pendant", 0xD6),
      "Moon Stone": KeyItem("Moon Stone", 0xDE),
      "Prism Shard": KeyItem("Prism Shard", 0xD8),
      "Tools": KeyItem("Tools", 0xDA),
      "Clone": KeyItem("Clone", 0xE2),
      "C. Trigger": KeyItem("C. Trigger", 0xD9),
      "Hero Medal": KeyItem("Hero Medal", 0xB3),
      "Robo's Ribbon": KeyItem("Robo's Ribbon", 0xB8)
    }
    
  def getKeyItemList(self):
    keyItemList = []
    for key,value in self.keyItems.items():
      keyItemList.append(key)
    return keyItemList

  def getKeyItem(self, name):
    return self.keyItems[name]

#
# TODO: Add prolog
#  
class LocationManager:
  def __init__(self):
    self.resetLocations()

  def getLocationList(self):
    locList = ["Zenan Bridge", "Lucca's House", "Denadoro Mountain", 
               "Snail Stop", "Frog's Burrow", "Lazy Carpenter", "King's Trial", 
               "Melchior's Refinements", "Giant's Claw", "Fiona's Shrine","Arris Done", 
               "Geno Dome", "Sun Palace", "Reptite Lair", "Mount Woe" ]
    return locList
  
  def resetLocations(self):
    self.locations = [
      Location("Zenan Bridge", 0x393C82, 0x393C84),
      Location("Lucca's House", 0x35F8AE, 0x35F8B0),
      Location("Denadoro Mountain", 0x37742F, 0x377432),
      Location("Snail Stop", 0x380C42, 0x380C5B),
      Location("Frog's Burrow", 0x3891D1, 0x3891D4),
      Location("Lazy Carpenter", 0x3966B, 0x3966D),
      Location("King's Trial", 0x38045D, 0x38045F),
      Location("Melchior's Refinements", 0x3805DE, 0x3805E0),
      Location("Giant's Claw", 0x1B8AEC, 0x1B8AEF),
      Location("Fiona's Shrine", 0x6EF5E, 0x6EF61),
      Location("Arris Done", 0x392F4C, 0x392F4E),
      Location("Geno Dome", 0x1B1844, 0x1B1846),
      Location("Sun Palace", 0x1B8D95, 0x1B8D97),
      Location("Reptite Lair", 0x18FC2C, 0x18FC2F),
      Location("Mount Woe", 0x381010, 0x381013)
    ]
    
  #
  # Get a location object based on a name.
  #
  # This should be a dictionary.  I'll fix it when I'm less lazy.
  #
  def getLocation(self, name):
    for location in self.locations:
      if location.name == name:
        return location
    
  
