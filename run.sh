#!/bin/bash
cd $HOME/raspi-monitoring-system
export PYTHONPATH=$(pwd)

screen -d -m python raspi_mon_sys/MailLoggerServer.py /etc/mail_credentials.json
screen -d -m python raspi_mon_sys/MainMonitoringSystem.py
