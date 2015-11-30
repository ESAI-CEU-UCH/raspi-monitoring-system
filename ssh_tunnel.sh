#!/bin/bash
# This script requires SSH keys properly configured. It has been prepared to be
# executed at startup as a system daemon. This tunnel allow to connect to mongodb
# in raspimondbserver machine.
su ssh_tunnel -c 'autossh -f -N -C -L 27018:localhost:27018 ssh_tunnel@raspimondbserver'
