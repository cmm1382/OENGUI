import sys
import ToWindDF as helper
import tkinter as tk
import matplotlib.pyplot as plt
import pandas as pd

stationName = sys.argv[1]
UTCOffset = sys.argv[2]
maxFill = 3

df = helper.checkData(stationName)

if type(df) == int:
    if df == 1:
        exit()
    if df == 2:
        exit()
    if df == 3:
        df = helper.getHourly(stationName)
else:
    df,info = helper.makeHourly(df)
    helper.save(df,stationName,"Hourly")
    df = helper.getHourly(stationName)

df = helper.interp(df,maxFill)

df,info = helper.makeWindFormat(df)
print(df)
print(info)