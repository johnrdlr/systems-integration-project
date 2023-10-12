#!/bin/bash

SERVICES=$2
currService=""

if [ $EUID -ne 0 ]; then
  if [ "$(id -u)" != "0" ]; then
    echo "root privileges are required" 1>&2
    exit 1
  fi
  exit 1
fi

function startService() {
    if systemctl is-active --quiet "$currService"; then
        echo "${currService} already running"
    else
        echo "Attempting to start"
        systemctl start "$currService"
        echo "Success"
    fi

}

function stopService() {
    echo "Attempting to stop ${currService}"
    systemctl stop --quiet "$service"
    echo "Success"
}

function checkService() {
    STATUS=$(systemctl is-active ${currService})
    echo "$STATUS"
}

for service in ${SERVICES//,/ }
do
    currService="${service}"
    if [ $1 = "start" ]; then
        startService
    fi
    if [ $1 = "stop" ]; then
        stopService
    fi
    if [ $1 = "status" ]; then
        checkService
    fi
done
