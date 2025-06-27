import TDFunctions
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from threading import Thread
import queue
import time
import os.path
import numpy as np
import sys


pythonCommand = sys.argv[1]

iconpath = os.path.join(os.getcwd(),"Resource","trans.png")

# Get transparent png to remove tkinter icon from windows
class myWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.iconphoto(False,tk.PhotoImage(file=iconpath))
        self.title("OEN data explorer")

# Ensure presence of docx and csv information files for ftp server
TDFunctions.FileFromUrl("ftp://anonymous:anonymous@ftp.ncdc.noaa.gov//pub/data/noaa/isd-history.csv","TD3505History.csv")
TDFunctions.FileFromUrl("ftp://anonymous:anonymous@ftp.ncdc.noaa.gov//pub/data/noaa/isd-format-document.docx","TD3505Format.docx")

def awaitWithWindow(label,target,args=None):
    popup = tk.Toplevel()
    popup.iconphoto(False,tk.PhotoImage(file=iconpath))
    tk.Label(popup,text=label).grid(row=0,column=1)
    pb = ttk.Progressbar(popup,mode="indeterminate")
    pb.start()
    pb.grid(row=1,column=1)
    output = queue.Queue()
    if args != None:
        t = Thread(target=target,args=args)
    else:
        t = Thread(target=lambda:output.put(target()))
    t.start()
    while t.is_alive():
        popup.update()
        popup.update_idletasks()
        time.sleep(.1)
    t.join(timeout=1800)
    try:
        popup.destroy()
    except:
        pass
    return output.get()

def ShowStationDetails(root, StationDict):
    def retry(exclusion):
        root.exclusions.append(exclusion)
        ShowStationDetails(root, TDFunctions.LocateStation(float(TargetLatitude.get()),
                                                           float(TargetLongitude.get()),
                                                           float(LatitudeError.get()),
                                                           float(LongitudeError.get()),root.exclusions))

    try:
        root.SiteInfoFrame.destroy()
    except:
        pass
    if type(StationDict)!=type(dict()):
        StationInfo = "No more unique stations could be identified in this zone, please try again"
        messagebox.showerror("Error",StationInfo)
        root.destroy()
        return
    else:
        StationInfo = f"Found: {StationDict['STATION NAME']}\n"
        StationInfo += f"Location: {StationDict['CTRY']}, {StationDict['STATE']}\n"
        StationInfo += f"Latitude: {StationDict['LAT']}\t Longitude: {StationDict['LON']}\n"
        StationInfo += f"USAF: {StationDict['USAF']}; WBAN: {StationDict['WBAN']}; ICAO: {StationDict['ICAO']}"
    root.SiteInfoFrame = tk.Frame(root)

    tk.Label(root.SiteInfoFrame, text=StationInfo).grid(row=0,column=0)
    root.RetryButton = tk.Button(root.SiteInfoFrame, text="Search again", command=lambda:retry(StationDict["STATION NAME"])).grid(row=0,column=1)

    Desired_Start = tk.StringVar()
    Desired_End = tk.StringVar()
    Desired_Start.set("1975")
    Desired_End.set("2025")

    tk.Label(root.SiteInfoFrame, text="Earliest desired year of data: ").grid(row=1,column=0)
    tk.Label(root.SiteInfoFrame, text="Latest desired year of data: ").grid(row=2,column=0)

    tk.Entry(root.SiteInfoFrame, textvariable=Desired_Start).grid(row=1,column=1)
    tk.Entry(root.SiteInfoFrame, textvariable=Desired_End).grid(row=2,column=1)

    tk.Button(root.SiteInfoFrame,
              text="Get data files",
              command=lambda:ShowDowloadFrame(root,StationDict=StationDict,Years=(int(Desired_Start.get()),int(Desired_End.get())))).grid(row=3,column=1)

    root.SiteInfoFrame.grid(row=2,column=0)

def ShowDowloadFrame(root, StationDict, Years):
    validated = queue.Queue()
    def downloadAndValidate():
        return TDFunctions.getTD3505GZ(StationDict=StationDict,FirstYear=Years[0],LastYear=Years[1])

    validated = awaitWithWindow("Please wait...",downloadAndValidate)

    requestedYears = range(Years[0],Years[1]+1)
    gotYears = [int(s.split("-")[-1][0:4]) for s in validated]
    gotYears = [x for x in gotYears if x in requestedYears]

    sequential = list(range(len(gotYears)))
    for i in range(len(gotYears)):
        ii = len(gotYears)-(1+i)
        ij = ii-1
        sequential[ii] = gotYears[ij] == gotYears[ii]-1
    sequential[0] = gotYears[1] == gotYears[0] + 1
    
    seq_start_index = 0
    seq_stop_index = len(gotYears)-1
    longest_seq = 0
    current_seq = 0
    current_seq_start = 0
    for i, is_seq in enumerate(sequential[:-1]):
        next_is_seq = sequential[i+1]
        is_start = ((is_seq==False) or i == 0) and (next_is_seq==True)
        is_end = i==len(sequential)-2
        is_stop = (is_seq==True) and (next_is_seq==False or is_end)
        if is_start:
            current_seq = 1
            current_seq_start = i
        elif is_stop:
            if current_seq > longest_seq:
                longest_seq = current_seq
                seq_start_index = current_seq_start
                seq_stop_index = i
                if is_end and sequential[-1]:
                    seq_stop_index = i + 1
                    longest_seq = current_seq + 1
        else:
            if is_seq:
                current_seq+=1
    
    consecutiveYearsInfo = f"Longest consecutive data found: {longest_seq} years from {gotYears[seq_start_index]} to {gotYears[seq_stop_index]}\n"
    consecutiveYearsInfo += "Continue with these years and set unique station name"

    root.DownloadFrame = tk.Frame(root)

    sep = "\n" + ("="*60) + "\n"
    tk.Label(root.DownloadFrame, text=sep).grid(row=0,column=1)

    totalWidth = max(3*len(requestedYears),300)
    gotYearsCanvas = tk.Canvas(root.DownloadFrame, width=totalWidth, height=100)
    gotYearsCanvas.create_line(((0,75),(totalWidth,75)),fill="black")
    spacing = np.linspace(20,totalWidth-20,len(requestedYears))
    for i,y in enumerate(requestedYears):
        if i == 0:
            gotYearsCanvas.create_text(20,85, text=y)
        if i==len(requestedYears)-1:
            gotYearsCanvas.create_text(totalWidth-20,85, text=y)
        if y in gotYears:
            if gotYears[seq_start_index] <= y <= gotYears[seq_stop_index]:
                gotYearsCanvas.create_line(((spacing[i],0),(spacing[i],75)),fill="green",width=3)
            else:
                gotYearsCanvas.create_line(((spacing[i],0),(spacing[i],75)),fill="blue",width=3)
        else:
            gotYearsCanvas.create_line(((spacing[i],0),(spacing[i],75)),fill="red",width=3)

    gotYearsCanvas.grid(row=1,column=1)
    tk.Label(root.DownloadFrame,text=consecutiveYearsInfo).grid(row=2,column=1)

    extractFrame = tk.Frame(root.DownloadFrame)
    extractStart = tk.StringVar()
    extractStop = tk.StringVar()
    stationName = tk.StringVar()
    extractStart.set(gotYears[seq_start_index])
    extractStop.set(gotYears[seq_stop_index])
    stationName.set(StationDict["STATION NAME"].replace(" ","_"))
    tk.Label(extractFrame, text="Station name (permanent)").grid(row=0,column=0)
    tk.Label(extractFrame, text="Start year to continue with:").grid(row=2,column=0)
    tk.Label(extractFrame, text="End year to continue with:").grid(row=3,column=0)
    tk.Entry(extractFrame, textvariable=stationName).grid(row=0,column=1)
    startEntry = tk.Entry(extractFrame, textvariable=extractStart)
    stopEntry = tk.Entry(extractFrame, textvariable=extractStop)
    startEntry.config(state="disabled")
    stopEntry.config(state="disabled")
    
    def toggleEdit():
        if editEnabled.get():
            startEntry.config(state="normal")
            stopEntry.config(state="normal")
        else:
            startEntry.config(state="disabled")
            stopEntry.config(state="disabled")


    editEnabled = tk.BooleanVar()
    tk.Label(extractFrame, text="Edit years (not recommended)").grid(row=1,column=0)
    tk.Checkbutton(extractFrame, variable=editEnabled, onvalue=True,offvalue=False,command=toggleEdit).grid(row=1,column=1)

    def continueToExtract():
        firstYear = int(extractStart.get())
        lastYear = int(extractStop.get())
        stationNameSafe = stationName.get().replace(" ","_")
        #print(f"Assigning data from years {firstYear}-{lastYear} to site \"{stationNameSafe}\"")
        extractScript = os.path.join(os.getcwd(),"TD3505","TDExtract.py")
        idString = f"{StationDict['USAF']}-{StationDict['WBAN']}"
        runExtractCommand = f"{pythonCommand} {extractScript} {idString} {firstYear} {lastYear} {stationNameSafe} {pythonCommand}"
        #print(runExtractCommand)
        os.system(runExtractCommand)
        exit()
    startEntry.grid(row=2,column=1)
    stopEntry.grid(row=3,column=1)
    tk.Button(extractFrame, text="Continue",command=continueToExtract).grid(row=4,column=1)

    extractFrame.grid(row=3,column=1)

    root.DownloadFrame.grid(row=3,column=0)

root = myWindow()

root.exclusions = []
root.StartFrame = tk.Frame()
TargetLatitude = tk.StringVar()
TargetLongitude = tk.StringVar()
LongitudeError = tk.StringVar()
LatitudeError = tk.StringVar()

TargetLatitude.set("30.4382")
TargetLongitude.set("-84.2806")
LatitudeError.set(".1")
LongitudeError.set(".1")


tk.Label(root.StartFrame, text="Desired Latitude:").grid(row=0, column=0)
tk.Label(root.StartFrame, text="Desired Londitude:").grid(row=1, column=0)

tk.Entry(root.StartFrame, textvariable=TargetLatitude).grid(row=0, column=1)
tk.Entry(root.StartFrame, textvariable=TargetLongitude).grid(row=1, column=1)

tk.Label(root.StartFrame, text="+/-").grid(row=0,column=2)
tk.Label(root.StartFrame, text="+/-").grid(row=1,column=2)

tk.Entry(root.StartFrame, textvariable=LatitudeError).grid(row=0,column=3)
tk.Entry(root.StartFrame, textvariable=LongitudeError).grid(row=1,column=3)

button = tk.Button(root.StartFrame,text="Get TD3505 Station",command=lambda:ShowStationDetails(root, TDFunctions.LocateStation(float(TargetLatitude.get()),
                                                                                                                               float(TargetLongitude.get()),
                                                                                                                               float(LatitudeError.get()),
                                                                                                                               float(LongitudeError.get()))))
button.grid(row=3,column=1)
root.StartFrame.grid(row=1,column=0)

root.mainloop()
