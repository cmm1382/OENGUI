To get started, run the powershell or bash script, depending on your system.

The script should install a new python virtual environment to the local directory
and install all required packages there.

Note that python must be callabale as "python" or "py" on Windows and "python3" on POSIX

The only POSIX machines I have tested on are Ubuntu WSL and Ubuntu Desktop, but any machine
that runs bash and has python callabale as "python3" should operate similarly; the only 
real consideration is if the system used a different format than $python3 <script> <argv> <argv>...