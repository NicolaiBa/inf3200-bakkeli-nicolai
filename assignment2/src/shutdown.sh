#!/bin/bash

# Executable
directory="CWD" #current working directory
executable="node.py";
username="USERNAME"
filename="nodelist.txt"

# Lists of nodes
if [ "$#" -eq 0 ]; then
  nodes=()
  while read -r line
  do
    nodes+=($line)
  done < "$filename"
else
  nodes=("$@")
fi

for node in "${nodes[@]}"
do
  echo "Signal $node to shutdown"
  ssh -q $node kill -INT $(ssh -q $node ps U $username | grep [n]ode.py | awk '{print $1}')
done
