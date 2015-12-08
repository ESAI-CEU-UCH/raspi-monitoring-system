#!/bin/bash
export STARTED_AT_BOOT=$1
export STARTUP_SLEEP=$2

cd $HOME/raspi-monitoring-system
export PYTHONPATH=$(pwd)

screen -S raspi_log -d -m python raspi_mon_sys/MailLoggerServer.py /etc/mail_credentials.json
screen -S raspi_main -d -m python raspi_mon_sys/MainMonitoringSystem.py

if [[ "$STARTED_AT_BOOT" = "yes" ]]; then
    # Monitorization of screen list for systemd startup script.
    while screen -list | grep -q raspi
    do
        sleep 2
    done
fi
