import sys
from TDFunctions import Extract
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import os
from threading import Thread
from queue import Queue

idString = sys.argv[1]
startYear = int(sys.argv[2])
stopYear = int(sys.argv[3])
stationName = sys.argv[4]
pythonCommand = sys.argv[5]

iconpath = os.path.join(os.getcwd(),"Resource","trans.png")
outputFile = os.path.join(os.getcwd(),"data",stationName,f"{stationName}.Clean.csv")
outputFileExists = os.path.exists(outputFile)
# Get transparent png to remove tkinter icon from windows
class myWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.iconphoto(False,tk.PhotoImage(file=iconpath))
        self.title("OEN data extractor")

def updateRootAndWait(target,root):
    output = Queue()
    t = Thread(target=lambda:output.put(target()))
    t.start()
    while t.is_alive():
        root.update()
        root.update_idletasks()
    t.join()
    return output.get()

if outputFileExists:
    fileInfo = f"Found saved data for {stationName}.\n"
    fileInfo += "Press \"OK\" to overwrite and continue or \"cancel\" to return"
    okContinue = messagebox.askokcancel(message=fileInfo)
else:
    okContinue = True

if not okContinue:
    exit()

root = myWindow()
root.lift()
loadingFrame = tk.Frame(root)
pb = ttk.Progressbar(loadingFrame,mode="indeterminate")
pb.start()
loadingFrame.grid(row=0,column=1)

missingData = Extract.CheckGZ(idString,startYear,stopYear)
if missingData != None:
    missingYears = [int(data.split("-")[-1][0:4]) for data in missingData]
    errorText=f"Data not found for the following selected years:\n"
    for year in missingYears:
        errorText += f"{year}\n"
    messagebox.showerror("ERROR",errorText)
    exit()

tk.Label(loadingFrame,text="Found data files, please wait...").grid(row=1,column=1)
pb.grid(row=0,column=1)

def extractGZ():
    return Extract.ExtractGZ(idString,startYear,stopYear,stationName)

dataFrame = updateRootAndWait(target=extractGZ,root=root)    

dataWarnings = []
noWarnings = "Station ID and coordinates are consistent"
for col in Extract.constantCols:
    uniqueVals = set(dataFrame[col])
    if len(uniqueVals) != 1:
        dataWarnings.append(f"{col} not consistent, {uniqueVals}")

def cleanGZ():
    return Extract.CleanData(dataFrame)

dataFrame = updateRootAndWait(target=cleanGZ,root=root)
pb.destroy()
loadingFrame.destroy()

loadingFrame = tk.Frame(root)
tk.Label(loadingFrame,text=f"Found {dataFrame.shape[0]:,} valid records").grid(row=0,column=1)
currentRow = 1
if len(dataWarnings) > 0:
    for warning in dataWarnings:
        tk.Label(loadingFrame, text=warning).grid(row=currentRow,column=1)
        currentRow += 1
else:
    tk.Label(loadingFrame,text=noWarnings).grid(row=currentRow,column=1)
    currentRow += 1

Extract.Save(dataFrame,stationName)

tx = "\nData stored with ID \"" + stationName +"\""
tx+= "\nYou may now close this window and proceed to data modeling for this site"
tk.Label(loadingFrame,text=tx).grid(row=currentRow,column=1)
currentRow+=1

loadingFrame.grid(row=0,column=1,padx=10,pady=10)
root.mainloop()