#! /bin/bash
App_Dir=$(pwd)
VENV_Dir="$App_Dir/Python/.VENV"

if ! [ -x "$(command -v python3)" ]; then
  echo "Python executable not found. Please make sure Python is installed on this computer" >&2
  exit 1
fi

cd "./Python"
if ! test -d $VENV_Dir; then
    echo Setting up virtual environment...
    python3 Init.py
fi

source ./.VENV/bin/activate
python3 ./OENapp.py

cd $App_Dir
deactivate