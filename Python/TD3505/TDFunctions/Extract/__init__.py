import gzip as gz
import os
import pandas as pd
import numpy as np

GZdir = os.path.join(os.getcwd(),"GZ")
dataDir = os.path.join(os.getcwd(),"data")
allGZs = [os.path.join(GZdir,fname) for fname in os.scandir(GZdir)]

TD3505names = [
    "nvbl","USAF","WBAN","UTC","Dom","Lat","Long",
    "Type","Elev","CLI","QCname","Drn","DrnQ","DrnT","MS10","MS10Q",
    "Ceiling","CeilQ","CeilTyp","CAVOK","Visib","VisQ","VisVar",
    "VisObQ","AirT","AirTQ","DewT","DewTQ","Press","PressQ","Additional"
]

constantCols = ["USAF","WBAN","Lat","Long"]

TD3505sizes = (4,6,5,12,1,6,7,5,5,5,4,3,1,1,4,1,5,1,1,1,6,1,1,1,5,1,5,1,5,1,500)
badQualityCodes = (3,7)
susQualityCodes = (2,6)
missingTD = (999,9999,99999,999999)

def CheckGZ(idString, startYear, stopYear):
    extractGZs = [os.path.join(GZdir,f"{idString}-{year}.gz") for year in range(startYear,stopYear+1)]
    missingData = []
    for GZfile in extractGZs:
        if not GZfile in allGZs:
            missingData.append(GZfile)
            continue
    return None if missingData == [] else missingData

def ExtractGZ(idString, startYear, stopYear, stationName):
    extractGZs = [os.path.join(GZdir,f"{idString}-{year}.gz") for year in range(startYear,stopYear+1)]
    outputDir = os.path.join(dataDir,stationName)
    if not os.path.isdir(outputDir):
        os.mkdir(outputDir)
    #array = np.ndarray()
    df = pd.DataFrame(columns=TD3505names)
    for GZfile in extractGZs:
        with gz.open(GZfile,mode="rt",encoding="utf-8",errors="ignore") as inFile:
            newDf = pd.read_fwf(inFile,widths=TD3505sizes)
            newDf.columns = list(range(newDf.shape[1]))
            dropCols = range(31,len(newDf.columns))
            newDf.drop(dropCols)
            newDf.columns = TD3505names
            df = pd.concat([df, newDf],axis=0,ignore_index=True)
    nColumns = df.shape[1]
    dropCols = df.columns[list(range(31,nColumns))]
    df.drop(dropCols,axis="columns",inplace=True)
    return df

def CleanData(dataFrame):
    keepCols = ["UTC","Type","Drn","DrnQ","DrnT","MS10","MS10Q","AirT","AirTQ","DewT","DewTQ"]
    needCols = ["UTC","Drn","DrnT","MS10","AirT","DewT"]
    dropCols = [col for col in TD3505names if col not in keepCols]
    dataFrame.drop(dropCols,axis="columns",inplace=True)
    qualityCol = [col for col in keepCols if "Q" in col]
    nRows = dataFrame.shape[0]
    badRows = []
    NAcount = 0
    for i in range(nRows):
        row = dataFrame.iloc[i]
        missingVal = any([0 if val not in missingTD else 1 for val in row])
        badQuality = any([0 if row[col] not in badQualityCodes else 1 for col in qualityCol])
        #susQuality = any([0 if row[col] not in susQualityCodes else 1 for col in qualityCol])
        hasNan = any([0 if not pd.isna(row[col]) else 1 for col in needCols])
        if missingVal or badQuality or hasNan:
            badRows.append(i)
    badRows = list(set(badRows))
    dataFrame.drop(badRows,axis="rows",inplace=True)
    dataFrame.drop(qualityCol,axis="columns",inplace=True)
    return dataFrame

def Save(dataFrame,stationName):
    outFile = os.path.join(dataDir,stationName,f"{stationName}.Clean.csv")
    dataFrame.to_csv(outFile,index=False)