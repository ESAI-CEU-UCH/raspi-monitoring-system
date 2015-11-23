#!/bin/bash
cp -R raspimon /usr/share/grafana/public/app/plugins/datasource/ &&
cd /usr/share/grafana/public/app/plugins/datasource/raspimon &&
find -name "*~" -exec rm -f {} ";"
