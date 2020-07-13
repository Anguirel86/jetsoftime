import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter import messagebox

import datastore as ds
import keyitems
import plandowriter


#
# Script variables
#
datastore = ds.DataStore()
progressBar = None
genThread = None

#
# This function is the target of the genThread thread.
# It handles calling the plando writer and writing the ROM.
#
def plandomize():
  plandowriter.plandomize(datastore)
  progressBar.stop()
  tk.messagebox.showinfo("Plandomization Complete", "Plandomization complete. Seed: " + datastore.seed.get())

#
# This function is the target of the "Generate" button on the GUI
#
def generate():
  global genThread
  if genThread == None or not genThread.is_alive():
    genThread = threading.Thread(target=plandomize)
    progressBar.start(50)
    genThread.start()


#
# Function to display a file chooser for the input ROM.
# Set the chosen file to the datastore.
#
def browseForRom():
  filename = askopenfilename()
  datastore.inputFilePath.set(filename)
  
  
#
# Function to display a file chooser for the chest data file.
# Set the chosen file to the datastore.
#
def browseForChestFile():
  filename = askopenfilename()
  datastore.chestFilePath.set(filename)
  

#
# Function to display a file chooser for the chest data file.
# Set the chosen file to the datastore.
#
def browseForSealedChestFile():
  filename = askopenfilename()
  datastore.sealedChestFilePath.set(filename)  
  
def saveDatastore():
  datastore.saveDatastpre()
  
def loadDatastore():
  datastore.loadDatastore()
  
#
# Main entry point for the plando GUI
#
def guiMain():
  mainWindow = tk.Tk()
  mainWindow.wm_title("Chrono Trigger: Jets of Time Plandomizer")
  
  menubar = tk.Menu(mainWindow)
  filemenu = tk.Menu(menubar, tearoff=0)
  filemenu.add_command(label="Save", command=saveDatastore)
  filemenu.add_command(label="Open", command=loadDatastore)
  filemenu.add_separator()
  filemenu.add_command(label="Quit", command=mainWindow.quit)
  menubar.add_cascade(label="File", menu=filemenu)
  
  mainWindow.config(menu=menubar)
  
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
  
  row = 0
  
  # Dropdown for the difficulty flags
  difficultyValues = ["easy", "normal", "hard"]
  label = tk.Label(frame, text="Difficulty:")
  var = tk.StringVar()
  var.set('normal')
  datastore.difficulty = var
  dropdown = tk.OptionMenu(frame, var, *difficultyValues)
  dropdown.config(width = 5)
  label.grid(row = row, column = 0, sticky=tk.W)
  dropdown.grid(row = row, column = 1, sticky=tk.W)
  row = row + 1
  
  # Checkboxes for the randomizer flags
  # Disable glitches
  var = tk.IntVar()
  datastore.flags['g'] = var
  tk.Checkbutton(frame, text="Disable Glitches(g)", variable = var).grid(row=row, sticky=tk.W, columnspan=3)
  row = row + 1
  
  # Faster overworld movement
  var = tk.IntVar()
  datastore.flags['s'] = var
  tk.Checkbutton(frame, text="Fast overworld movement(s)", variable = var).grid(row=row, sticky=tk.W, columnspan=3)
  row = row + 1
  
  # faster dpad inputs in menus
  var = tk.IntVar()
  datastore.flags['d'] = var
  tk.Checkbutton(frame, text="Fast dpad in menus(d)", variable = var).grid(row=row, sticky=tk.W, columnspan=3)
  row = row + 1
  
  # Lost Worlds
  var = tk.IntVar()
  datastore.flags['l'] = var
  tk.Checkbutton(frame, text="Lost Worlds(l)", variable = var).grid(row=row, sticky=tk.W, columnspan=3)
  row = row + 1
  
  # Boss scaling
  var = tk.IntVar()
  datastore.flags['b'] = var
  tk.Checkbutton(frame, text="Boss scaling(b)", variable = var).grid(row=row, sticky=tk.W, columnspan=3)
  row = row + 1
  
  # Zeal 2 as last boss
  var = tk.IntVar()
  datastore.flags['z'] = var
  tk.Checkbutton(frame, text="Zeal 2 as last boss(z)", variable = var).grid(row=row, sticky=tk.W, columnspan=3)
  row = row + 1
  
  # Early pendant charge
  var = tk.IntVar()
  datastore.flags['p'] = var
  tk.Checkbutton(frame, text="Early Pendant Charge(p)", variable = var).grid(row=row, sticky=tk.W, columnspan=3)
  row = row + 1
  
  # Locked characters
  var = tk.IntVar()
  datastore.flags['c'] = var
  tk.Checkbutton(frame, text="Locked characters(c)", variable = var).grid(row=row, sticky=tk.W, columnspan=3)
  row = row + 1
  
  # Tech rando
  var = tk.IntVar()
  datastore.flags['te'] = var
  tk.Checkbutton(frame, text="Randomize techs(te)", variable = var).grid(row=row, sticky=tk.W, columnspan=3)
  row = row + 1
  
  # Let the user choose a seed (optional parameter)
  tk.Label(frame, text="Seed(optional):").grid(row=row, column=0, sticky=tk.E)
  datastore.seed = tk.StringVar()
  tk.Entry(frame, textvariable=datastore.seed).grid(row=row, column=1)
  row = row + 1
  
  # Let the user select the base ROM to copy and patch
  tk.Label(frame, text="Input ROM:").grid(row=row, column=0, sticky=tk.E)
  datastore.inputFilePath = tk.StringVar()
  tk.Entry(frame, textvariable=datastore.inputFilePath).grid(row=row, column=1)
  tk.Button(frame, text="Browse", command=browseForRom).grid(row=row, column=2)
  row = row + 1

  # Add a progress bar to the GUI for ROM generation
  global progressBar
  progressBar = ttk.Progressbar(frame, orient='horizontal', mode='indeterminate')
  progressBar.grid(row = row, column = 0, columnspan = 3, sticky=tk.N+tk.S+tk.E+tk.W)
  row = row + 1
  
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
  
  # Add a row for each key item
  locationManager = keyitems.LocationManager()
  keyItemManager = keyitems.KeyItemManager()
  keyItems = keyItemManager.getKeyItemList()
  keyItems.insert(0, "")
  
  rowval = 0
  for location in locationManager.getLocationList():
    label = tk.Label(frame, text=location + ":")
    var = tk.StringVar()
    var.set('');
    datastore.itemLocVars[location] = var
    dropdown = tk.OptionMenu(frame, var, *keyItems)
    dropdown.config(width=12)
    label.grid(row = rowval, column = 0, sticky=tk.W)
    dropdown.grid(row = rowval, column = 1, sticky=tk.W)
    rowval = rowval + 1
    
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
  # TODO: Come up with a decent GUI for this.
  # For now just have the user load up a chest.txt file with
  # the chest item settings.
  
  tk.Label(frame, text="Input Chest File:").grid(row=0, column=0, sticky=tk.E)
  datastore.chestFilePath = tk.StringVar()
  tk.Entry(frame, textvariable=datastore.chestFilePath).grid(row=0, column=1)
  tk.Button(frame, text="Browse", command=browseForChestFile).grid(row=0, column=2)
  
  tk.Label(frame, text="Input Sealed Chest File:").grid(row=1, column=0, sticky=tk.E)
  datastore.sealedChestFilePath = tk.StringVar()
  tk.Entry(frame, textvariable=datastore.sealedChestFilePath).grid(row=1, column=1)
  tk.Button(frame, text="Browse", command=browseForSealedChestFile).grid(row=1, column=2)
  
  
  
  return frame

################  
##### MAIN #####
################
# Start the gui  
os.chdir("../")
guiMain()