#!/bin/bash

app_name="VPN Handler (intel).app"

#  builds the application from scratch and launches
rm -r -f build && \
    rm -r -f dist && \
    python setup.py py2app && \
    cd dist && \
    sleep 1 && \
    open -a "$app_name" && \
    cd ../
