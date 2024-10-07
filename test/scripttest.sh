#!/bin/bash

# Loop from 1 to 50
for ((i=1; i<=50; i++))
do
  echo $i
done

# Initialize a counter for the 60-second loop
counter=0

echo "awaiting input:"
read ASDF

echo "got input: $ASDF"

# Loop every 10 seconds until 60 seconds have passed
while [ $counter -lt 60 ]
do
  echo "Waited: $counter seconds"
  sleep 1
  counter=$((counter + 10))
done
