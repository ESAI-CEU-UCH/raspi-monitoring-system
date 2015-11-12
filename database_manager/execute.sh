#!/bin/bash
if [[ ! -e node_modules ]]; then
    npm install mongo-express
fi
echo "Warning!!! Requires SSH tunnel to esainet01 27018 port"
OLDPWD=$(pwd)
cd node_modules/mongo-express/
node app.js
cd $OLDPWD
