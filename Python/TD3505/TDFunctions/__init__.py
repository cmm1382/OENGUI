import shutil
import tempfile
import urllib.request
import os
import os.path

def GetTempFile(url,verbose=False):
    """
    Parameters: 
        url - string, expected to be an http resource
        verbose - whether or not to print information to console
    Returns:
        tmp_file.name - name of a temporary file containing the contents of 
            the web resource hosted at <url>
    """
    if verbose:
        print(f"Preparing to get file from {url}")
    with urllib.request.urlopen(url) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(response, tmp_file)
    return(tmp_file.name)

def FileFromUrl(url,saveLocation,overwrite=False,verbose=False):
    """
    Parameters:
        url - string, expected to be an http resource
        saveLocation - path of file to give to urlretrieve as string
        overwrite - whether or not to overwrite existing files
        verbose - whether or not to print information to console
    Returns:
        Void
    """
    if verbose:
        print(f"Saving {url} to {saveLocation}")
    if not overwrite:
        if os.path.isfile(saveLocation):
            if verbose:
                print(f"File {saveLocation} already exists")
            return
    if verbose:
        print("Preparing to get file from above url")
    try:
        fp = open(saveLocation)
    except IOError:
        # If not exists, create the file
        fp = open(saveLocation, 'w+')
    fp.close()
    urllib.request.urlretrieve(url,saveLocation)


def LocateStation(Lat,
                  Lon,
                  Lat_Range = 1,
                  Lon_Range = 1,
                  exclude = []
                  ):
    """
    Parameters:
        Lat - Target latitude of stations to search for in degrees (+/-)
        Lon - Target longitude of stations to search for in degrees (+/-)
        Lat_Range - Acceptable difference in latitude from target in degrees (+/-)
        Lon_Range - Acceptable difference in longitude form target in degrees (+/-)
        Exclude - Name of undesired stations as string; as in "STATION NAME" from history file
    Returns:
        0 - Reached the end of the history file without finding a match 
                                OR
            Found a match that was missing fields
        StationDict - python dictionary with the column names and values of the history file as
                        keys/values respectively
    """
    with open("TD3505History.csv", "r", encoding='utf-8') as f:
        History_Length = sum(1 for _ in f)
    with open("TD3505History.csv") as f:
        Header = f.readline()
        ColNames = Header.replace("\"","").replace("\n","").split(",")
        LatIndex, LonIndex = ColNames.index("LAT"), ColNames.index("LON")
        LatDiff,LonDiff = Lat_Range + 1, Lon_Range + 1
        LinesRead = 0
        current = []
        while ((LatDiff > Lat_Range or LonDiff > Lon_Range) and LinesRead < History_Length):
            LinesRead += 1
            current = f.readline().replace("\"","").replace("\n","").split(",")
            if len(current) != len(ColNames):
                continue
            if exclude and (current[2] in exclude):
                continue
            currentLat,currentLon = current[LatIndex],current[LonIndex]
            if currentLat == "":
                currentLat = Lat + Lat_Range + .001
            else:
                currentLat = float(currentLat)
            if currentLon == "":
                currentLon = Lon + Lon_Range + .001
            else:
                currentLon = float(currentLon)
            LatDiff,LonDiff = abs(currentLat-Lat),abs(currentLon-Lon)
    if LinesRead == History_Length:
        return 0
    elif len(ColNames)==len(current):
        output = {}
        for i in range(len(ColNames)):
            output[ColNames[i]] = current[i]
        #print(output,"\n",exclude)
        return output
    else:
        return 0

def getTD3505GZ(StationDict, FirstYear=1900, LastYear=2050, verbose=False):
    """
    Parameters:
        StationDict - python dictionary as from LocateStation()
        FirstYear - optional, first year of data to get, if available
        LastYear - optional, last year of data to get, if available
        verbose - whether or not to print information to console
    """
    cwd = os.getcwd()
    years = [int(StationDict["BEGIN"][0:4]),int(StationDict["END"][0:4])]
    years[0] = max((years[0],FirstYear))
    years[1] = min((years[1],LastYear))
    if (not os.path.exists("GZ")):
        os.mkdir("GZ")
    SiteString = "ftp://anonymous:anonymous@ftp.ncdc.noaa.gov//pub/data/noaa/"
    years = range(years[0],years[1]+1)
    os.chdir(os.path.join(cwd,"GZ"))
    for y in years:
        filename = f"{StationDict['USAF']}-{StationDict['WBAN']}-{y}.gz"
        GetString = SiteString + f"{y}/" + filename
        PutString = os.path.join(".","GZ",filename)
        if verbose:
            print(f"Saving {GetString} to {PutString}")
        try:
            FileFromUrl(GetString,filename)
        except:
            os.remove(filename)
    
    validated = []
    for GZfile in os.scandir():
        validated.append(GZfile.name)

    os.chdir(cwd)
    return validated

