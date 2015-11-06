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

inactivenodes=()
for node in "${nodes[@]}"
do
  if [ $(ssh -q $node ps U $username | grep [n]ode.py | awk '{print $1}')  ]; then
    inactivenodes+=($node)
  fi
done

availablenodes=()
for tnode in "${nodes[@]}"
do
  ident="True"
  for inode in "${inactivenodes[@]}"
  do
    if [ $tnode == $inode ]; then
      ident="False"
    fi
  done
  if [ $ident == "True" ]; then
    availablenodes+=($tnode)
  fi
done

# Boot shutdown processes
for node in ${availablenodes[@]}
do
  echo "Booting node" $node
  nohup ssh $node bash -c "'python $directory$executable'"  > /dev/null 2>&1 &
done
