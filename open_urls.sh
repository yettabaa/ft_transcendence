#!/bin/bash

# Base URL
base_url="http://localhost:5173/game_tournament/"

# Number of times to open the link
times_to_open=8


# Loop through the numbers and open each URL in the default browser
for ((i=1; i<=times_to_open; i++))
do
    # Construct the URL
    url="${base_url}${i}"
    
    # Open the URL in the default web browser
    explorer.exe "$url"
    
    # Sleep for 1 second between each open
    sleep 1
done
