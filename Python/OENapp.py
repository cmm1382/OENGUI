#### Calvin McGinnis 10/3/24 ##############################################
#==========================================================================
# This script contains the main functions and driver code for a TKinter
# App meant for visualizing and analyzing fitted OEN models.
# Before using this app, the analysis must be completed for the site,
# Analysis is completed for a set of sample sites

import numpy as np
import tkinter as tk
from tkinter import ttk
import os

from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import platform
import StationHelper

###########################################################################
################ CLASS DEFINITIONS ########################################
###########################################################################
# --------- TKapp ---------------------------------------------------------
# Superclass for the App, inherits from tk.Tk
# Handles control and display of the different pages
class TKapp(tk.Tk):
    def __init__(self):
        self.root = super().__init__()
        iconpath = os.path.join(os.getcwd(),"Resource","trans.png")
        self.iconphoto(False,tk.PhotoImage(file=iconpath))
        self.title("OEN Wind Library")
        self.container = tk.Frame(self) # make master frame for all contents
        self.container["bg"]="white"
        # Make sure the master frame takes up the entire window
        self.container.pack(side = "top", fill = "both", expand = True) 
        self.container.grid_rowconfigure(0, weight = 1)
        self.container.grid_columnconfigure(0, weight = 1)
        # Initialize the pages of the app as a dictionary
        # The app has 3 pages that are all mutable from the global scope
        self.frames = {}
        for PageName in (StartPage,PreviewPage,SamplePage):
            frame = PageName(self.container, self)
            self.frames[PageName] = frame
            frame.grid(row=0,column=0)
        self.show_page(StartPage)
        self.frames[RecordBrowser]=None
    # Method to show the requested page and hide the others
    # Call before/after writing changes to page
    def show_page(self,handle):
        display = self.frames[handle]
        display.tkraise()
        hide = list(self.frames.keys())
        hide.remove(handle)
        for name in hide:
            current_frame = self.frames[name]
            current_frame.lower()
    # Re-Initialize a page in case it needs to be destroyed
    # after the app is initialized
    def init_page(self, handle):
        frame = handle(self.container, self)
        self.frames[handle] = frame
        frame.grid(row=0,column=0)
    # Grid two pages in the master frame to display both at once
    # Expects a list of Page classes and a list of equal length of
    # length 2 tuples giving the row and column to grid the respective
    # page at in the master frame
    def grid_pages(self, handles, locations):
        for i, name in enumerate(handles):
            frame = self.frames[name]
            frame.tkraise()
            frame.grid(row=locations[i][0],
                       column=locations[i][1])
# From (need to credit if used in final thing?):
# https://gist.github.com/mp035/9f2027c3ef9172264532fcd6262f3b01
class ScrollFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent) # create a frame (self)

        self.canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")#place canvas on self
        self.viewPort = tk.Frame(self.canvas, background="#ffffff")#place a frame on the canvas, this frame will hold the child widgets 
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview) #place a scrollbar on self 
        self.canvas.configure(yscrollcommand=self.vsb.set)#attach scrollbar action to scroll of canvas

        self.vsb.pack(side="right", fill="y")#pack scrollbar to right of self
        self.canvas.pack(side="left", fill="both", expand=True)#pack canvas to left of self and expand to fil
        self.canvas_window = self.canvas.create_window((4,4), window=self.viewPort, anchor="nw",            #add view port frame to canvas
                                  tags="self.viewPort")

        self.viewPort.bind("<Configure>", self.onFrameConfigure)#bind an event whenever the size of the viewPort frame changes.
        self.canvas.bind("<Configure>", self.onCanvasConfigure)#bind an event whenever the size of the canvas frame changes.
            
        self.viewPort.bind('<Enter>', self.onEnter)# bind wheel events when the cursor enters the control
        self.viewPort.bind('<Leave>', self.onLeave)# unbind wheel events when the cursorl leaves the control

        self.onFrameConfigure(None)#perform an initial stretch on render, otherwise the scroll region has a tiny border until the first resize

    def onFrameConfigure(self, event):                                              
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))#whenever the size of the frame changes, alter the scroll region respectively.

    def onCanvasConfigure(self, event):
        '''Reset the canvas window to encompass inner frame when required'''
        canvas_width = event.width
        #whenever the size of the canvas changes alter the window region respectively.
        self.canvas.itemconfig(self.canvas_window, width = canvas_width)
    # cross platform scroll wheel event
    def onMouseWheel(self, event):
        if platform.system() == 'Windows':
            self.canvas.yview_scroll(int(-1* (event.delta/120)), "units")
        elif platform.system() == 'Darwin':
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.canvas.yview_scroll( -1, "units" )
            elif event.num == 5:
                self.canvas.yview_scroll( 1, "units" )
    # bind wheel events when the cursor enters the control
    def onEnter(self, event):
        if platform.system() == 'Linux':
            self.canvas.bind_all("<Button-4>", self.onMouseWheel)
            self.canvas.bind_all("<Button-5>", self.onMouseWheel)
        else:
            self.canvas.bind_all("<MouseWheel>", self.onMouseWheel)
    # unbind wheel events when the cursorl leaves the control
    def onLeave(self, event): 
        if platform.system() == 'Linux':
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        else:
            self.canvas.unbind_all("<MouseWheel>")
class RecordBrowser(tk.Toplevel):
    def __init__(self, controller):
        super().__init__()
        self.controller=controller # Connect to app
        self.scrollFrame = ScrollFrame(self) # Init scrollable frame
        self.titleFrame = tk.Frame(self) # Init header that won't scroll
        Preview = self.controller.frames[PreviewPage] # Local alias for active PreviewPage
        self.title(f"{Preview.site}: {Preview.month} {Preview.hour}") # Make title more descriptive
        Hoffset = StationHelper.Hoffsets[Preview.station.ID] # Station's local UTC offset from config file
        TZ = StationHelper.Time_Zones[Preview.station.ID]
        width=[20,10,10,10,10,10,10,10,10] # Manually set widths of columns
        # Make title for each column of weather data present (Except MH)
        for col, name in enumerate(Preview.station.data_names):
            w=width[col]
            # For every column of data except UTC and MH, just use the name from CSV
            if name not in ("MH","UTC"):
                tk.Label(self.titleFrame, text=name, borderwidth="1",width=w,
                         relief="solid").grid(row=0,column=col)
            # Change label for UTC's to indicate that they are adjusted
            if name == "UTC":
                tx = TZ + f" (UTC {Hoffset}:00)"
                tk.Label(self.titleFrame, text = tx, borderwidth="1",width=w,
                         relief="solid").grid(row=0,column=col)
        self.titleFrame.pack(side="top",fill="x",expand=False) # Place at top, don't fill
        #print(Preview.station.data_names,Preview.station.nRecords)
        # Load and place every weather record immediately, scroll to show more
        for row in range(Preview.station.nRecords):
            for col, name in enumerate(Preview.station.data_names):
                w=width[col]
                value = Preview.station.Data[name][row]
                if "\n" in value:
                    value.strip("\n")
                # Prepare to make labels for the individual values
                text = value
                if name != "UTC":
                    if value != "NA":
                        floatval = float(value)
                        text = f"{floatval:.1f}" # If the data is not a date time, display it as a float
                else: # If the data is a date time, convert to local
                    # Expecting Format: "%y-%m-%d %H:%M:%S"
                    datestring, timestring = value.split(" ") # "%y-%m-%d %H:%M:%S" -> "%y-%m-%d", "%H:%M:%S"
                    Year_str, Month_str, Day_str = datestring.split("-") # "%y-%m-%d" -> "%y", "%m", "%d"
                    Hour_str, Minute_str, Second_str = timestring.split(":") # "%H:%M:%S" -> "%H", "%M", "%S"
                    LocalH = int(Hour_str)+Hoffset # Convert from UTC to local time
                    # Fix artifacts of times needing to wrap around midnight
                    # if (LocalH < 0) is 1 (True) add 24, if (LocalH > 24) is 1 (True) subtract 24, else add 0
                    LocalH += 24*(LocalH<0) - 24*(LocalH>24)
                    LocalH = str(LocalH).zfill(2)
                    text = (Month_str + "/" + Day_str + "/" + Year_str + ", " +
                            LocalH + ":" + Minute_str + ":" + Second_str)
                # Make label for every column except MH
                if name != "MH":
                    tk.Label(self.scrollFrame.viewPort, text = text, relief="solid",
                             width=w,borderwidth="1").grid(row=row+1,column=col)
        self.scrollFrame.pack(side="bottom",fill="both",expand=True)
###########################################################################
# -------- StartPage ------------------------------------------------------
# Dropdown menu to select the site, month, and hour
# Passes the location, month, hour, and MH to PreviewPage
class StartPage(tk.Frame):
    # Overwrite Default initialization
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller=controller # Controller is TKapp object
        self["bg"]="white"
        # Initialize string variables accessible to the TK interface
        self.Location, self.ChosenMonth, self.ChosenHour = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.Location.set(StationHelper.Locations[0])
        self.ChosenMonth.set(StationHelper.Months[0])
        self.ChosenHour.set(StationHelper.Hours[0])
        # Labeled Dropdowns for site, month and hour selection
        tk.Button(self, text="Open Data Explorer",command=self.EnterDataExplorer).grid(column=0,row=1)
        ttk.Label(self, text="Select Site", background="white").grid(column=1, row=1, sticky="E")
        ttk.Combobox(self,values=StationHelper.Locations,state="readonly",textvariable=self.Location).grid(column=2, row=1)
        ttk.Label(self, text="Select Month", background="white").grid(column=1, row=2, sticky="E")
        ttk.Combobox(self,values=StationHelper.Months,state="readonly",textvariable=self.ChosenMonth).grid(column=2, row=2)
        ttk.Label(self, text="Select Hour", background="white").grid(column=1, row=3, sticky="E")
        ttk.Combobox(self,values=StationHelper.Hours,state="readonly",textvariable=self.ChosenHour).grid(column=2, row=3)
        ttk.Button(self, text="Choose",command=self.pass_options).grid(column=2, row=4)
    def EnterDataExplorer(self):
        if os.name == "nt":
            pythonCommand = "python"
        else:
            pythonCommand ="python3"
        DataExplorerPath = os.path.join(os.getcwd(),"TD3505","TDDownload.py")
        os.system(f"{pythonCommand} {DataExplorerPath} {pythonCommand}")
    def OpenBrowser(self):
        if self.controller.frames[RecordBrowser]:
            self.controller.frames[RecordBrowser].destroy()
        self.controller.frames[RecordBrowser]=RecordBrowser(self.controller)
    # Command to make the preview page visible once the model is selected
    def pass_options(self):
        Preview = self.controller.frames[PreviewPage]
        Preview.site = self.Location.get()
        Preview.month = self.ChosenMonth.get()
        Preview.hour = self.ChosenHour.get()
        Preview.MH = (StationHelper.Months.index(Preview.month)*24)+StationHelper.Hours.index(Preview.hour)
        Preview.SiteSelected()
        # Show preview page while keeping start page visible
        self.controller.grid_pages([PreviewPage,StartPage],
                                   [(1,0),(0,0)])
        leftarrow, rightarrow = u"\u2190", u"\u2192"
        M,H = StationHelper.Months.index(Preview.month),StationHelper.Hours.index(Preview.hour)
        # Month down
        ttk.Button(self,text=leftarrow,command=lambda mo=M-1,hr=H:self.change_time(mo,hr)).grid(column=3,row=2)
        # Month up
        ttk.Button(self,text=rightarrow,command=lambda mo=M+1,hr=H:self.change_time(mo,hr)).grid(column=4,row=2)
        # Hour down
        ttk.Button(self,text=leftarrow,command=lambda mo=M,hr=H-1:self.change_time(mo,hr)).grid(column=3,row=3)
        # Hour up
        ttk.Button(self,text=rightarrow,command=lambda mo=M,hr=H+1:self.change_time(mo,hr)).grid(column=4,row=3)
        # Browse Wind Records
        ttk.Button(self, text="Wind Records", command = self.OpenBrowser).grid(column=3,row=1,columnspan=2)
    def change_time(self, month, hour):
        dM = 0
        if hour > 23:
            hour = 0
            dM = 1
        elif hour < 0:
            hour = 23
            dM = -1
        month = max(min(month,11),0) + dM
        hour = max(min(hour,23),0)
        self.ChosenMonth.set(StationHelper.Months[month])
        self.ChosenHour.set(StationHelper.Hours[hour])
        self.pass_options()

###########################################################################
# ------------ PreviewPage ------------------------------------------------
# Preview the OEN model for the selected site, month, hour
class PreviewPage(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self["bg"] = "white"
        self.site = None   # Empty variable to be set from StartPage
        self.month = None  # Empty variable to be set from StartPage
        self.hour = None   # Empty variable to be set from StartPage
        self.MH = None     # Empty variable to be set from StartPage
        self.selected = -1 # Variable for which ellipses are selected
        # Placing the frames in a dictionary allows them to not be removed
        # by the garbage cleaner while still having names
        self.frames = {}
        # Frame for displaying the OEN model overlayed on the WSp for the MH
        self.frames["OENframe"] = ttk.Frame(self)
        # Frame for displaying Ellipse details and selecting them
        self.frames["ScrollFrame"] = ttk.Frame(self)
        # Frame for displaying relative frequencies
        self.frames["PieFrame"] = ttk.Frame(self)
        self.frames["OENframe"].grid(row=1,column=0)
        self.frames["ScrollFrame"].grid(row=1,column=1)
        self.frames["PieFrame"].grid(row=1,column=2)
    def DrawOEN(self, Es):
        # Assign figure as named variable so it stays accessible
        self.OENfig = Figure(figsize=(8,6),dpi=100,facecolor=(0,1,0,0))
        #Configure plot
        self.OENfig.suptitle(self.station.Name,fontsize=14, fontweight="bold")
        plot1 = self.OENfig.add_subplot(111)
        plot1.set_title(f"{self.month}, {self.hour}")
        self.station.put_WSp(plot1, Es)
        canvas = FigureCanvasTkAgg(self.OENfig,self.frames["OENframe"])
        canvas.draw()
        canvas.get_tk_widget().grid(column=1,row=1)
    def selectEllipse(self,E):
        self.Display[E] = self.Display[E]!=True
        Es = [i for i,Val in enumerate(self.Display) if Val == True]
        #print(Es)
        self.DrawOEN(Es)
    def show_f_pie(self):
        self.PieFig = Figure(figsize=(6,6),dpi=100)
        self.PieFig.suptitle("Relative Frequency of Ellipses")
        ax = self.PieFig.add_subplot(111)
        labels = ["0: Calms"]
        labels += [str(E+1)+": "+self.station.Wind_Names[E] for E in self.station.active]
        sizes = [self.station.f[E+1] for E in self.station.active]
        total_frequency = np.sum(sizes)
        if total_frequency<1:
            calms = 1-np.sum(sizes)
        else:
            print(f"SUM OF FREQUENCIES > 1 ({total_frequency})")
            sizes /= total_frequency
            calms = 0.0
        sizes = [calms, *sizes]#;print(sizes)
        ax.cla()
        ax.pie(sizes,labels=labels)
        canvas = FigureCanvasTkAgg(self.PieFig,self.frames["PieFrame"])
        canvas.draw()
        canvas.get_tk_widget().grid(column=0,row=0)
    def show_Ellipse_labels(self):
        self.labels,self.buttons = [],[]
        self.Display = [E in self.station.active for E in range(self.station.nE)]
        F = self.station.f[1:]
        self.frames["ScrollFrame"].destroy()
        self.frames["ScrollFrame"] = tk.Frame(self)
        self.frames["ScrollFrame"]["bg"]="white"
        self.frames["ScrollFrame"].grid(row=1,column=1)
        order = np.argsort(F)
        order = [x for x in order if x in self.station.active]
        order.reverse()
        for i,E in enumerate(order):
            F = self.station.f[E+1]*100
            W,S = self.station.W[E], self.station.S[E]
            T,R = self.station.T[E], self.station.R[E]
            #P = self.station.P[E]
            Spd = np.sqrt((W**2)+(S**2))
            Drn = np.rad2deg(np.arctan2(S,W))
            txt = ("="*20)+"\n"
            if Drn < 0:
                Drn += 360
            txt += f"Velocity: {Spd:.2f} knots\n Direction: {Drn:.2f} deg\nFrequency: {F:.2f}%\n"
            if (R!=0):
                txt+="Relative Humidity: {R:.2f}%\n".format(R=R)
            if (T!=0):
                txt+="Temperature: {T:.2f} C\n".format(T=T)
            #if (P!=0):
                #txt+="Sea-Level Pressure: {P:.2f} mbar\n".format(P=P)
            txt += "="*20
            self.labels.append(ttk.Label(self.frames["ScrollFrame"],text=txt,background="white"))
            self.labels[-1].grid(column=1,row=i+2)
            txt = ""
            try:
                txt += str(E+1)+": "+StationHelper.Wind_Names[self.station.ID][E]
            except:
                txt += "Wind "+str(E+1)
            self.buttons.append(ttk.Button(self.frames["ScrollFrame"],
                                      text=txt, 
                                      command=lambda s=E: self.selectEllipse(s)))
            self.buttons[-1].grid(column=0,row=i+2)
    # Called from StartPage, used to create and display a new
    # page that previews the OEN model
    def SiteSelected(self):
        # Make sure we have enough info to select the model
        if self.site==None or self.month==None or self.hour == None or self.MH == None:
            self.controller.show_page(StartPage)
            return
        # Make a figure in OENframe and plot the OEN preview in it --------
        # Save helpful identifying info to PreviewPage object
        self.siteID = StationHelper.Locations.index(self.site)
        self.station = StationHelper.stations[self.siteID].change_MH(self.MH)
        self.DrawOEN(-1)
        self.show_Ellipse_labels()
        self.show_f_pie()

###########################################################################
# --------- SamplePage ----------------------------------------------------
class SamplePage(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)



###########################################################################
########### FUNCTION DEFINITIONS ##########################################
###########################################################################

def main():
    App = TKapp()
    App.mainloop()

if __name__ == '__main__':
    main()
