#!/bin/bash
sudo systemctl start pigpiod
sudo systemctl enable pigpiod
sudo cp vinpy.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl start vinpy
sudo systemctl enable vinpy

