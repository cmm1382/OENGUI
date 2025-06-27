import os
from venv import create

cwd = os.getcwd()
venv_dir = os.path.join(cwd,r".VENV")
if not os.path.exists(venv_dir):
    env = create(venv_dir,with_pip=True)

if os.name != "nt":
    activation_script = "source " + os.path.join(venv_dir,"bin","activate")
    platformString = "Posix"
else:
    activation_script = os.path.join(venv_dir,"Scripts","activate")
    platformString = "Windows"

if os.name != "nt":
    py_executable = os.path.join(venv_dir,"bin","python3")
else:
    py_executable = os.path.join(venv_dir,"Scripts","python.exe")

os.system(f"{py_executable} -m pip install --upgrade pip")
os.system(f"{py_executable} -m pip install -r Requirements.txt")
