#!/bin/bash

# Base URL
base_url="http://localhost:5173/game_tournament/8/"

# Number of times to open the link
times_to_open=8

generate_random_name() {
    echo $(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 8 | head -n 1)
}

# Loop through the numbers and open each URL in the default browser
for ((i=1; i<=times_to_open; i++))
do
    random_name=$(generate_random_name)
    # Construct the URL
    url="${base_url}${random_name}"
    
    # Open the URL in the default web browser
    explorer.exe "$url"
    
    # Sleep for 1 second between each open
    sleep 1
done
