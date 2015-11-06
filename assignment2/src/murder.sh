#!/bin/bash

# Executable
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
  ssh -q $node pkill -9 -u $username -f python
done
