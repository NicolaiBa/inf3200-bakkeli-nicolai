#!/bin/bash

# Executable
directory="CWD" #current working directory
executable="node.py";
username="USERNAME"
filename="nodelist.txt"

tests=300
NodesInTotal=0
# Lists of all nodes
if [ "$#" -eq 0 ]; then
  nodes=()
  while read -r line
  do
    nodes+=($line)
    NodesInTotal=$((NodesInTotal+1))
  done < "$filename"
else
  nodes=("$@")
fi

# Boot all processes
for node in "${nodes[@]}"
do
  echo "Booting node" $node
  nohup ssh $node bash -c "'python $directory$executable'"  > /dev/null 2>&1 &
done

randnum=$(($RANDOM % $NodesInTotal))

echo "NodesInTotal: $NodesInTotal"
echo "Random number test: $randnum"
echo "TotalNodeList: ${nodes[@]}"
echo "Random node: ${nodes[randnum]}"

while [ $tests -gt 0 ]
do
  echo "TestsLeft: $tests"
  tests=$((tests-1))
  activenodes=()
  ActiveCount=0
  for node in "${nodes[@]}"
  do
    if [ $(ssh -q $node ps U $username | grep [n]ode.py | awk '{print $1}') -ne 0 ]; then
      activenodes+=($node)
      ActiveCount=$((ActiveCount+1))
    fi
  done

  availableIndexCount=${#activenodes[@]}
  echo "availableIndexCount: $availableIndexCount"
  indexes=( $(shuf -e $(seq 0 $(($ActiveCount-1)))) )
  echo "indexes:  "${indexes[@]}""
  for index in "${indexes[@]}"
  do
      testspr=10
      while [ $testspr -gt 0 ]
      do
        testspr=$((testspr-1))
        curl -X GET uvrocks.cs.uit.no:8020/ElectionTest
        sleep 0.8
      done
      availableIndexCount=$((availableIndexCount-1))
      echo "AvailableIndexs: $availableIndexCount"
      randomAvailableNode=${activenodes[index]}
      echo "randomAvailableNode:  $randomAvailableNode"

      ssh -q $randomAvailableNode kill -INT $(ssh -q $randomAvailableNode ps U $username | grep [n]ode.py | awk '{print $1}')

  done
  sleep 2

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

done

for node in "${nodes[@]}"
do
  echo "Signal $node to shutdown"
  ssh -q $node kill -INT $(ssh -q $node ps U $username | grep [n]ode.py | awk '{print $1}')
done
