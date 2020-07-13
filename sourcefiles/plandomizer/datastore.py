import tkinter as tk

#
# The Datastore class holds all of the data displayed
# by the GUI and used by the plandowriter.  This acts as 
# the data model for the application.
#
class DataStore:

  #
  # charLocVars is a mapping of character names to locations
  # itemLocVars is a mapping of location name to item name
  # The keys are strings, the values are tk StringVar variables.
  #
  def __init__(self):
    self.characters = ['Crono', 'Marle', 'Lucca', 'Frog', 'Robo', 'Ayla', 'Magus']
    self.charLocVars = {}
    self.itemLocVars = {}
    self.flags = {}
    self.outputFile = None
    self.inputFile = None
    self.chestFilePath = None
    self.sealedChestFilepath = None
    
    
  #
  # Validate user entries in the datastore.
  #
  # Returns True if valid, False if invalid
  #
  def validate(self):
    # TODO: Actually implement this
    return True  
    
  #
  # Save the datastore to a file
  #
  def saveDatastore(self, filename):
    return True
    
  #
  # Load the datastore from a file
  #
  def loadDatastore(self, filename):
    return True