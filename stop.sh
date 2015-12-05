#!/bin/bash
waitpid(){
    pid=$1
    while kill -0 "$pid" 2> /dev/null; do
        sleep 0.5
    done
}

for mask in "raspi_mon_sys/MainMonitoringSystem.py" "raspi_mon_sys/MailLoggerServer.py"; do
    pid=$(pgrep -f "python $mask")
    if [[ ! -z $pid ]]; then
        kill -2 $pid
        sleep 2
        kill -9 $pid
        waitpid $pid
        echo "Sleeping 2 seconds after killing the process"
        sleep 2
    fi
done
