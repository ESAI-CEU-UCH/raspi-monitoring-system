#!/bin/bash
if [[ ! -e node_modules ]]; then
    npm install mongo-express
fi
echo "Warning!!! Requires SSH tunnel to raspimondbserver 27018 port"
OLDPWD=$(pwd)
cd node_modules/mongo-express/
node app.js &
sleep 5
gnome-open http://localhost:8081
wait
cd $OLDPWD
