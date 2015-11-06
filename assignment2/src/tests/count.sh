#!/bin/bash

# Executable
directory="CWD" #current working directory
executable="node.py";
username="USERNAME"
filename="1.txt"

i=0
count=0
while read -r line
do
  i=$((i+1))
  count=$(echo "$count + $line"|bc)
  echo $count
done < "$filename"
echo $i
