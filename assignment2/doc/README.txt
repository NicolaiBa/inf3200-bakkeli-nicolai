In order for the code to run must the following be done:
Open the startup file and change the directory string to the contain the
location of the source code.

Start the startup program by running: "bash startup.sh"

Run the python file "frontend.py" followed by the names of the
nodes located in the node list in startup.sh.

Each of these processes should be run in their own terminal.

To output the amount of data stored on the backend nodes do the following:
Open a new terminal while the other processes are running.
Issue a GET request with "/size" as key.
  For instance curl -X GET uvrocks.cs.uit.no:8020/getCurrentLeader

There are some bash scripts created to add and kill nodes in the network.
These are:
    startup.sh
    add.sh
    shutdown.sh
    owntest.sh
    count.sh
    murder.sh

NB!!  murder.sh is a script that should not be used.
      It was created as a last possible solution to end processes who didn't stop as they should.
      Read the file before use!!!

These scripts require that you add the current working directory and user name in the initial variables to work.

The most important are these:
    startup.sh  start processes and checks if they are alive (and does not require any further input).
    add.sh      starts new processes that are not running (avoids creating processes for nodes that are active).
    shutdown.sh kills processes that are running (by gentle shutdown).

The rest were created for testing purposes:
    murder.sh   forcefully kills every python process on the cluster under your user name (avoid use!!).
    owntest.sh  adds and kills processes and issues get requests to the nodes.
    count.sh    sums the test results from owntest.sh.

Most of these scripts creates or kills nodes on the network.
The nodes selected are listed in nodelist.txt.
Most of these scripts can be inputted with node names.
  For example, "bash shutdown.sh compute-1-0" will only kill the process on compute-1-0.
