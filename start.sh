#!/bin/bash
export STARTED_AT_BOOT=$1
export STARTUP_SLEEP=$2

cd $HOME/raspi-monitoring-system
export PYTHONPATH=$(pwd)

screen -d -m python raspi_mon_sys/MailLoggerServer.py /etc/mail_credentials.json
screen -d -m python raspi_mon_sys/MainMonitoringSystem.py

if [[ "$STARTED_AT_BOOT" = "yes" ]]; then
    # For systemd startup script.
    while true; do sleep 3600; done
fi
