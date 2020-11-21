#!/bin/bash

HTTP=$(which http)

if [ ! -x "$HTTP" ]; then
    echo 'You need HTTPie to run this script!'
    echo 'sudo pip3 install httpie'
    exit 1
fi

URL=:8080

set -x

http GET $URL/bookings
http GET $URL/bookings/42