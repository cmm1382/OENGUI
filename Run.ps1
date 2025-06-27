$App_Dir = $PWD
$VENV_Dir = Join-Path -Path $App_Dir -ChildPath "\Python\.VENV"
$VENV_Exists = Test-Path $VENV_Dir
$Py_Exists = Get-Command -ErrorAction SilentlyContinue -Type Application "python"

if (!($Py_Exists)){
    Write-Output "Python executable not found. Please make sure Python is installed on this computer"
    Exit
}

Set-Location .\Python
if (!($VENV_Exists)){
    & python .\Init.py
}

& .\.VENV\Scripts\activate
& python .\OENapp.py

Set-Location $App_Dir
& deactivate