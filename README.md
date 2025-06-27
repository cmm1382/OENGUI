# OEN_Vis_Tool
### Visualization tool for the Offset Elliptical Normal model parameter set.<br>
**No support is guaranteed and testing has only been completed on Windows.**<br>

This is a work in progress, the ultimate goal is to add a comprehensive GUI environment
to the Offset Elliptical Normal analysis framework for modeling seasonal and diurnal
trends at the local level based on historic data. This can be completed with some 
knowledge of R using the resources archived at NJ Cook's personal webpage

Sample sites are included with the script, additional analyses can be completed using the software at [njcook.uk](http://www.njcook.uk/).

Work is underway on software to complete analysis with no established timeline.

# Setting Up the Tool

To get started, run the powershell or bash script, depending on your system.

The script should install a new python virtual environment to the local directory
and install all required packages there.

Note that python must be callabale as "python" or "py" on Windows and "python3" on POSIX

The only POSIX machines I have tested on are Ubuntu WSL and Ubuntu Desktop, but any machine
that runs bash and has python callabale as "python3" should operate similarly; the only 
real consideration is if the system used a different format than 
'''bash
$python3 script argv argv...
'''
# Extensibility

A goal of this project is to encourage people to look into the open source Wind Engineering Cookbook for R that is hosted at [njcook.uk](http://www.njcook.uk/). 

## Adding a site

After downloading the R software and completing the OEN analysis of a site, in order to add the models to the tool, they must be saved as a CSV. Currently the OEN app is not agnostic to the column headers so, a specific file structure must be used. Each site has 3 data files associated with it: XXXX.Flagged_Obs.csv, XXXX.OEN.Weather.csv, and XXXX.WSP.Interp.csv. The format of these files must match the files currently found in the *data* directory. I hope to add more support for this in the future, it has not really been implemented now.