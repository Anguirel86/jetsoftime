import os
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename

import datastore as ds
import plandowriter

datastore = ds.DataStore()

def generate():
  print("Generating seed")
  plandowriter.plandomize(datastore)


#
# Function to display a file chooser for the input ROM.
# Set the chosen file to the datastore.
#
def browseForRom():
  print("Browsing for ROM")
  filename = askopenfilename()
  datastore.inputFilePath.set(filename)
  
  
#
# Main entry point for the plando GUI
#
def guiMain():
  mainWindow = tk.Tk()
  mainWindow.wm_title("Chrono Trigger: Jets of Time Plandomizer")
  
  tabs = ttk.Notebook(mainWindow)
  
  tabs.add(getGameFlagsFrame(tabs), text="Flags")
  tabs.add(getCharacterFrame(tabs), text="Characters")
  tabs.add(getKeyItemFrame(tabs), text="Key Items")
  tabs.add(getShopFrame(tabs), text="Shops")
  tabs.add(getChestFrame(tabs), text="Chests")
  tabs.pack(expand=1, fill="both")
  
  tk.Button(mainWindow, text="Generate", command=generate).pack()
  
  mainWindow.mainloop()

  
#
# Get a tab where the user can pick game flags.
#  
def getGameFlagsFrame(notebook):
  frame = ttk.Frame(notebook, borderwidth = 1)
  
  # Checkboxes for the randomizer flags
  # Disable glitches
  var = tk.IntVar()
  datastore.flags['g'] = var
  tk.Checkbutton(frame, text="Disable Glitches(g)", variable = var).grid(row=0, sticky=tk.W, columnspan=3)
  # Faster overworld movement
  var = tk.IntVar()
  datastore.flags['s'] = var
  tk.Checkbutton(frame, text="Fast overworld movement(s)", variable = var).grid(row=1, sticky=tk.W, columnspan=3)
  
  # faster dpad inputs in menus
  var = tk.IntVar()
  datastore.flags['d'] = var
  tk.Checkbutton(frame, text="Fast dpad in menus(d)", variable = var).grid(row=2, sticky=tk.W, columnspan=3)
  
  # Lost Worlds
  var = tk.IntVar()
  datastore.flags['l'] = var
  tk.Checkbutton(frame, text="Lost Worlds(l)", variable = var).grid(row=3, sticky=tk.W, columnspan=3)
  
  # Boss scaling
  var = tk.IntVar()
  datastore.flags['b'] = var
  tk.Checkbutton(frame, text="Boss scaling(b)", variable = var).grid(row=4, sticky=tk.W, columnspan=3)
  
  # Zeal 2 as last boss
  var = tk.IntVar()
  datastore.flags['z'] = var
  tk.Checkbutton(frame, text="Zeal 2 as last boss(z)", variable = var).grid(row=5, sticky=tk.W, columnspan=3)
  
  # Early pendant charge
  var = tk.IntVar()
  datastore.flags['p'] = var
  tk.Checkbutton(frame, text="Early Pendant Charge(p)", variable = var).grid(row=6, sticky=tk.W, columnspan=3)
  
  # Locked characters
  var = tk.IntVar()
  datastore.flags['c'] = var
  tk.Checkbutton(frame, text="Locked characters(c)", variable = var).grid(row=7, sticky=tk.W, columnspan=3)
  
  # Tech rando
  var = tk.IntVar()
  datastore.flags['te'] = var
  tk.Checkbutton(frame, text="Randomize techs(te)", variable = var).grid(row=8, sticky=tk.W, columnspan=3)
  
  tk.Label(frame, text="Seed(optional):").grid(row=9, column=0, sticky=tk.E)
  datastore.seed = tk.StringVar()
  tk.Entry(frame, textvariable=datastore.seed).grid(row=9, column=1)
  
  tk.Label(frame, text="Input ROM:").grid(row=10, column=0, sticky=tk.E)
  datastore.inputFilePath = tk.StringVar()
  tk.Entry(frame, textvariable=datastore.inputFilePath).grid(row=10, column=1)
  tk.Button(frame, text="Browse", command=browseForRom).grid(row=10, column=2)
  
  return frame
  
#
# Get a tab where the user can place the game's characters.
#
def getCharacterFrame(notebook):
  frame = ttk.Frame(notebook)
  frame.grid(column=0, row=0, sticky=(tk.N,tk.W,tk.E,tk.S))
  #frame.columnconfigure(0, weight=1)
  
  # Add a row for each character with a location dropdown
  charLocChoices = ['', 'Start1', 'Start2', 'Cathedral', 'Guardia Castle', 'Proto Dome', 'Frog Burrow', 'Dactyl Nest']
  rowval = 0
  for char in datastore.characters:
    label = tk.Label(frame, text=(char + ":"))
    var = tk.StringVar()
    var.set('')
    datastore.charLocVars[char] = var
    dropdown = tk.OptionMenu(frame, var, *charLocChoices)
    dropdown.config(width = 12)
    label.grid(row = rowval, column = 0, sticky=tk.W)
    dropdown.grid(row = rowval, column = 1, sticky=tk.W)
    rowval = rowval + 1
  
  return frame
  
#
# Get a tab where the user can set the location of the
# game's various key items.
#  
def getKeyItemFrame(notebook):
  frame = ttk.Frame(notebook)
  return frame
  
#
# Get a tab where the user can set the items for sale at
# the various shops in the game.
#  
def getShopFrame(notebook):
  frame = ttk.Frame(notebook)
  return frame
  
#
# Get a tab where the user can set chest contents for the
# chests in the game.
#
def getChestFrame(notebook):
  frame = ttk.Frame(notebook)
  return frame

################  
##### MAIN #####
################
# Start the gui  
os.chdir("../")
guiMain()