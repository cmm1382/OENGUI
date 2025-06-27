import os
import pandas as pd
from numpy import floor

dataDir = os.path.join(os.getcwd(),"data")

def save(df,stationName,tag):
    stationDataDir = os.path.join(dataDir,stationName)
    outputFile = os.path.join(stationDataDir,f"{stationName}.{tag}.csv")
    df.to_csv(outputFile,index=False)

def getHourly(stationName):
    stationDataDir = os.path.join(dataDir,stationName)
    hourlyAlignedFile = os.path.join(stationDataDir,f"{stationName}.Hourly.csv")
    return pd.read_csv(hourlyAlignedFile,parse_dates=["UTC"])

def checkData(stationName):
    stationDataDir = os.path.join(dataDir,stationName)
    if not os.path.isdir(stationDataDir):
        return 1
    dataFile = os.path.join(stationDataDir,f"{stationName}.Clean.csv")
    if not os.path.exists(dataFile):
        return 2
    hourlyAlignedFile = os.path.join(stationDataDir,f"{stationName}.Hourly.csv")
    if os.path.exists(hourlyAlignedFile):
        return 3
    return pd.read_csv(dataFile,parse_dates=["UTC"])

def makeHourly(dataFrame):
    startDate = dataFrame["UTC"].min()
    stopDate = dataFrame["UTC"].max()
    cols = list(dataFrame.columns)
    cols.remove("UTC")
    currentUTCs = pd.Series(dataFrame["UTC"])
    allUTCs = pd.Series(pd.date_range(start=startDate,end=stopDate,freq="h"))
    datesToGenI = allUTCs.index.difference(dataFrame["UTC"].index)
    datesToGen = allUTCs.iloc[datesToGenI]
    datesExisting = allUTCs.index.difference(datesToGenI)
    nRecordsFull = len(allUTCs)
    newData ={"UTC":allUTCs}
    for colName in cols:
        newData[colName] = [pd.NA]*nRecordsFull
    output = pd.DataFrame(data=newData,dtype="object")
    output.iloc[datesExisting] = dataFrame.iloc[datesExisting]
    for dateTime in datesToGen:
        year = dateTime.year
        month = dateTime.month
        day = dateTime.day
        hour = dateTime.hour
        lower_bound = pd.to_datetime(f"{year}-{month}-{day} {hour}:00:00")
        upper_bound = pd.to_datetime(f"{year}-{month}-{day} {hour}:59:59")
        available = currentUTCs[(currentUTCs>=lower_bound) & (currentUTCs<=upper_bound)]
        try:
            availableI = available.index[0]
        except:
            continue
        outputI = allUTCs[allUTCs==dateTime].index[0]
        output.iloc[outputI] = dataFrame.iloc[availableI]
    infoString = f"Replaced {len(set(datesToGenI))} observations with inconsistent minutes"
    return output, infoString

def interp(df,maxGap):
    interpColumns = ["Drn","MS10","AirT","DewT"]
    interpDF = df[interpColumns]
    interpDF = interpDF.interpolate(method="linear",limit=maxGap)
    df[interpColumns] = interpDF
    df.dropna(subset=interpColumns,inplace=True,ignore_index=True)
    needsTypeTag = df["Type"].isna()
    df.loc[needsTypeTag,"Type"] = "INT"
    needsDrnTag = df["DrnT"].isna()
    df.loc[needsDrnTag, "DrnT"] = "INT"
    return df

def makeWindFormat(df):
    dataInfoString = ""
    nRecords = df.shape[0]
    recordIndex = range(nRecords)
    def getSurroundingAvg(indices,colName):
        indices = pd.Series(indices)
        a0, af = indices-1, indices+1
        a0[a0<0]=0
        af[af>nRecords] = nRecords
        b0 = pd.Series(df.loc[a0,colName])
        bf = pd.Series(df.loc[af,colName])
        b0.index = indices
        bf.index = indices
        return (b0+bf)/2
    # Make meters per second column "MS"
    df["MS"] = df["MS10"].round(0)/10
    # Make initial knots column "Kts0"
    df["Kts0"] = df["MS"] * 1.944
    df["Kts0"] = df["Kts0"].round(0)
    df.round({"Drn":-1}) # assign Drn to 10 deg increments
    # Detect Calms
    markedCalm = df["DrnT"]=="C"
    foundCalm = df["MS10"]==0
    # Set Drn of Calms to 0
    if sum(markedCalm) > 0:
        df.loc[markedCalm,"Drn"] = 0
    if sum(foundCalm) > 0:
        df.loc[foundCalm,"Drn"] = 0
    # Correct Decadal knot artefacts
    df["Kts"] = df["Kts0"]
    over10 = df["Kts0"] > 10
    divBy10 = df["Kts0"].mod(10) == 0
    a = df.index[over10 & divBy10]
    aVals = pd.Series(df.loc[a,"Kts0"])
    bVals = getSurroundingAvg(a,"Kts0")
    b = (aVals-bVals) > 10
    c = a[b]
    df.loc[c,"Kts"] = df.loc[c,"Kts0"]/10
    dataInfoString += f"Corrected {len(set(c))} decadal knot artifacts\n"
    # Correct fat finger knot artefacts
    combos = [98,89,87,78,96,69,85,58,47,74,45,54,56,67,65,63,
            36,34,52,25,41,21,23,32,34,99,88,77,66,55,44,33,22]
    inCombos = [i for i in recordIndex if df.loc[i,"Kts0"] in combos]
    a = df.index[inCombos]
    b = getSurroundingAvg(a,"Kts0")
    c = [i for i in range(len(a)) if b.iloc[i] < max(10,df.loc[a[i],"Kts0"]*.15)]
    toReplaceI = a[c]
    toReplaceRange = range(len(toReplaceI))
    toReplace = df.loc[toReplaceI,"Kts0"]
    replacements = [max(floor(toReplace.iloc[i]/10),toReplace.iloc[i] % 10) for i in toReplaceRange]
    df.loc[toReplaceI,"Kts"] = replacements
    dataInfoString += f"Corrected {len(toReplace)} fat-finger knot artifacts\n"
    # Correct for FM-12 MS10=10xknots artefacts
    a = df.index[df["Type"]=="FM-15"]
    a = list(a)
    if a[-1] == nRecords-1:
        a = a[:-1]
    a = pd.Index(a)
    b = a[df.loc[a+1,"Type"]=="FM-12"]
    FM12IsRight = list(set(df.loc[b+1,"Type"]))[0] == "FM-12"
    FM15IsRight = list(set(df.loc[b,"Type"]))[0] == "FM-15"
    if FM12IsRight and FM15IsRight:
        dataInfoString += f"Found {len(b)} FM-12 records following FM-15 records"
    # Remove identical FM-12 after FM-15
    # Find and delete isolated observations
    # Detect artefacts using incremental changes in MS10 and Arc
    return df, dataInfoString

def getMHVDpdfs(df):
    nRecords = df.shape[0]
    # Tabulate data by MH
    # Calculate VDpdf for each MH

def getMHWSpdfs(df):
    pass
    # Convert MHVDpdfs to MHWSpdfs