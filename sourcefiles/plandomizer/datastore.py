import tkinter as tk

#
# The Datastore class holds all of the data displayed
# by the GUI and used by the plandowriter.  This acts as 
# the data model for the application.
#
class DataStore:
  def __init__(self):
    self.characters = ['Crono', 'Marle', 'Lucca', 'Frog', 'Robo', 'Ayla', 'Magus']
    self.charLocVars = {}
    self.flags = {}
    self.outputFile = None
    self.inputFile = None
    
    
  #
  # Validate user entries in the datastore.
  #
  # Returns True if valid, False if invalid
  #
  def validate(self):
    # TODO: Actually implement this
    return True  