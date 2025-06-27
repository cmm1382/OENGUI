# Calvin McGinnis - 6/25
# DataSite class for parsing data files into python objects
import numpy as np
from matplotlib.patches import Polygon

Locations  = ["Eglin","Albany","Prescott","Pueblo","Savannah","Winner"]
Hoffsets = [-6]
Time_Zones = ["CST"]

Months = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]
Hours = [  "0:00-1:00",   "1:00-2:00",   "2:00-3:00",   "3:00-4:00",
           "4:00-5:00",   "5:00-6:00",   "6:00-7:00",   "7:00-8:00",
           "8:00-9:00",  "9:00-10:00", "10:00-11:00", "11:00-12:00",
         "12:00-13:00", "13:00-14:00", "14:00-15:00", "15:00-16:00",
         "16:00-17:00", "17:00-18:00", "18:00-19:00", "19:00-20:00",
         "20:00-21:00", "21:00-22:00", "22:00-23:00", "23:00-24:00"]

def EllipsePatch(W,S,w,s,r,nSeg=64,PatchParams={}):
    piX2 = 2*np.pi # named variable for 2 pi
    # Create t vector with values (1:2pi)/nSeg for parametric definition
    # of ellipses
    eT = np.linspace(start = piX2/nSeg, stop = piX2, num=nSeg)
    xys = np.zeros((nSeg,2)) # Matrix to hold x(t), y(t)
    xys[:,0] = W + w*np.cos(eT)*np.cos(r) - s*np.sin(eT)*np.sin(r)
    xys[:,1] = S + w*np.cos(eT)*np.sin(r) + s*np.sin(eT)*np.cos(r)
    ellipse = Polygon(xys, **PatchParams)
    return ellipse

class Station:
    def __init__(self, Lines, MH=0):
        Params = dict()
        for li in Lines:
            li = li.strip().split("=")
            k = li[0].strip().replace(" ","_")
            if k == "Wind_Names":
                v = [x.strip() for x in li[1].split(",")]
            else:
                v = li[1].strip().replace(" ","_")
            Params[k] = v
        self.__dict__ = Params
        self.Config = Lines
        self.MH = MH
        self.get_OEN(MH=MH)
        self.get_WSp(MH=MH)
        self.get_MH_weather(MH=MH)
    def __repr__(self):
        out = ""
        for k in self.__dict__.keys():
            v = self.__dict__[k]
            out += f"{k} = {v}\n"
        return out
    def get_WSp(self,MH=0):
        wspfile = self.Wind_Vector_Probability_Field_file
        with open(wspfile) as f:
            # Read WSp from CSV. ASSUMES FORMATTING FOLLOWS COOK's
            #  Line)      Contents                 | Notes
            #----------------------------------------------------------
            #     1) <Station>.WSp.Interp.csv      | Filename (ignored)
            #     2) <nMH>, <N>, <N>, <incWS>      | Format (WSps are nMHxNxN tensor,
            #                                      |         N=2*nWS+1, maxWS=nWS*incWS
            #                                      |         W,S in [-maxWS,maxWS])
            #     3) 1                             | MH #
            #     4) *1st line of WSp for MH = 1*  | WSp
            #       ...                            |...
            # nWS+4) 2                             | MH #
            # nWS+5) *1st line of WSp for MH = 2*  | WSp
            #       ...   
            f.readline()          # Expect <Station>.WSp.Interp.csv
            head = f.readline()               # Expect <nMH>, <nWS>, <nWS>, <incWS>
            [_,nWS,_,incWS] = head.split(",") 
            self.nWS = np.floor(int(nWS)/2) # Infer nWS from N (see above)
            # Need to convert from string to int for addition
            self.incWS=int(incWS)
            mWS = int(nWS)
            lines = f.readlines() # Go ahead and get the rest of the file
            output = [] # Initialize list as empty buffer to read into
            # Iterate over file
            for i,li in enumerate(lines):
                # If there is only 1 comma separated value in the line
                if len(li.split(","))==1:
                    # If the current line converted to integer equals chosen MH
                    if (int(li.strip())==MH+1):
                        line1 = i+1 # Mark 1st line of desired WSp in file
            # Walk through file from first desired line to last line of WSp
            for i in range(line1,line1+mWS):
                output.append(lines[i].strip().split(",")) # Add to out buffer
            output = np.asarray(output,dtype=float)
            self.wsp=np.fliplr(np.transpose(output))
            # Flip upside down so plt.imshow shows it rightside up
            #self.wsp = np.flipud(np.transpose(output))
    def put_WSp(self, ax, Es=None):
        Z = self.wsp
        maxWS = max(np.sqrt(np.power(self.W,2)+np.power(self.S,2))+(self.w+self.s)/2)
        maxWS = max(maxWS,10) # minimum range of plot is -10:10 knts
        nWS,incWS = int(self.nWS),self.incWS
        x = np.arange(-nWS, nWS+incWS, incWS)
        zs = np.zeros((1+(2*nWS),1))
        extent = (-nWS,nWS,-nWS,nWS)
        wsp = ax.imshow(Z, extent=extent,cmap="gnuplot2")
        ax.plot(x,zs,"w--")
        ax.plot(zs,x,"w--")
        limits = (-maxWS,maxWS)
        labs = np.round(np.linspace(-maxWS,maxWS,7))
        ax.set_xlim(limits)
        ax.set_xticks(labs)
        ax.set_xticklabels(0-labs)
        ax.set_ylim(limits)
        ax.set_yticks(labs)
        ax.set_yticklabels(0-labs)
        ax.set_xlabel("Westerly Component of Wind (Knots)")
        ax.set_ylabel("Southerly Component of Wind (Knots)",labelpad=-2)
        if Es == -1:
            Es = self.active
        for E in Es:
            W,S,w,s,r = -self.W[E], -self.S[E], self.w[E], self.s[E], -self.r[E]
            #print(f"W={W}, S={S}, w={w}, s={s}, r={r}") # DEBUG CODE
            options = {"fill":False,"ec":"w"}
            ellipse = EllipsePatch(W,S,w,s,r,PatchParams=options)
            ax.add_patch(ellipse)
            ax.text(W,S,str(E+1),color="k",backgroundcolor="w")
    def get_OEN(self, MH=0,fTol=1e-4):
        file = self.OEN_data_file
        with open(file) as f:
            labels = f.readline().strip("\"")
            self.labels = labels[:-1].split(",")
            lines = f.readlines()
            data = np.zeros((len(lines),len(self.labels)))#; print(data.shape) # DEBUG CODE
            for i,li in enumerate(lines):
                data[i,:] = li.split(",")
        data = np.asarray(data,dtype=float)
        f_i, W_i, S_i, w_i, s_i, r_i = [],[],[],[],[],[]
        T_i, R_i, P_i = [],[],[]
        for i in range(len(self.labels)):
            lab = self.labels[i][1:]
            if lab.startswith("f"):
                f_i.append(i)
            elif lab.startswith("W"):
                W_i.append(i)
            elif lab.startswith("S"):
                S_i.append(i)
            elif lab.startswith("w"):
                w_i.append(i)
            elif lab.startswith("s"):
                s_i.append(i)
            elif lab.startswith("r"):
                r_i.append(i)
            elif lab.startswith("T"):
                T_i.append(i)
            elif lab.startswith("R") and "Rsq" not in lab:
                R_i.append(i)
            elif lab.startswith("P"):
                P_i.append(i)
        self.RMSE = data[MH,0]
        self.f = data[MH,f_i]
        self.W = data[MH,W_i]
        self.S = data[MH,S_i]
        self.w = data[MH,w_i]
        self.s = data[MH,s_i]
        self.r = data[MH,r_i]
        self.T = data[MH,T_i]
        self.R = data[MH,R_i]
        self.P = data[MH,P_i]
        self.nE = len(self.W)
        self.active = np.array([i-1 for i in range(1,self.nE+1)if self.f[i]>fTol])
    def get_MH_weather(self,MH=0):
        Hist = self.Historic_Records
        with open(Hist) as f:
            labs = f.readline().strip()
            labs=list(labs.replace("\"","").replace("TD3505.","").split(","))
            lines = f.readlines()
            self.nRecords=len(lines)
            wanted_cols = ["UTC","Vel","Drn","RH","AirT","MH"]
            data = dict()
            for col in wanted_cols:
                data[col] = []
            thisMH = str(MH+1)
            for i,li in enumerate(lines):
                this_line = li.split(",")
                MHcol = labs.index("MH")
                MHi = this_line[MHcol]
                if MHi == thisMH:
                    for desired in wanted_cols:
                        current_col = labs.index(desired)
                        data[desired].append(this_line[current_col])
            self.data_names = list(data.keys())
            self.nRecords = len(data[self.data_names[0]])
            self.Data = data
    def change_MH(self, MH):
        return Station(self.Config,MH=MH)



with open("Options.txt") as f:
    First_Char = ""
    while First_Char != ">":
        li = f.readline()
        First_Char = li[0]
    Config_Lines = f.readlines()
    Month_Line = Config_Lines[[i for i in range(len(Config_Lines)) if "Month Name" in Config_Lines[i]][0]]
    Month_Format = Month_Line.strip().replace(" ","").split("=")[-1].lower()
    if Month_Format == "short":
        Months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    elif Month_Format == "numeric":
        Months = list(range(1,13))
    
    start_indices = [i+1 for i in range(len(Config_Lines)) if Config_Lines[i].startswith("Start")]
    stop_indices = [i for i in range(len(Config_Lines)) if Config_Lines[i].startswith("End")]

    stations = []
    n=0
    for startI, endI in zip(start_indices,stop_indices):
        Temp = Station(Config_Lines[startI:endI],MH=0)
        Station.ID = n
        stations.append(Temp)