In order for the code to run must the following be done:
Open the startup file and change the directory string to the contain the
location of the source code.

Start the startup program by running:
"bash startup.sh"

Run the python file "storage_frontend.py" followed by the names of the
nodes located in the node list in startup.sh.
"python storage_frontend.py compute-1-1 compute-1-2 compute-1-3"

Each of these processes should be run in their own terminal.

To output the amount of data stored on the backend nodes do the following:
Open a new terminal while the other processes are running.
Issue a GET request with "/size" as key.
  For "instance curl -X GET uvrocks.cs.uit.no:8002/size"
