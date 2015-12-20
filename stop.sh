#!/bin/bash
waitpid(){
    pid=$1
    while kill -0 "$pid" 2> /dev/null; do
        sleep 0.5
    done
}

BREAK_TIME=4
ACK_TIME=2

for mask in "raspi_mon_sys/MainMonitoringSystem.py" "raspi_mon_sys/OpenEnergyMonitor.py" "raspi_mon_sys/PlugwiseMonitor.py" "raspi_mon_sys/MailLoggerServer.py"; do
    pid=$(pgrep -n -f "python $mask")
    if [[ ! -z $pid ]]; then
        kill -2 $pid
        echo "Sleeping $BREAK_TIME seconds to allow process termination"
        sleep $BREAK_TIME
        kill -9 $pid 2> /dev/null
        waitpid $pid
        echo "Sleeping $ACK_TIME seconds to allow other process acknowledgement"
        sleep $ACK_TIME
    fi
done
