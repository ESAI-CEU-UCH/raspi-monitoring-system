#!/bin/bash
# cp -R raspimon /usr/share/grafana/public/app/plugins/datasource/
cp -R raspimon_pandas /usr/share/grafana/public/app/plugins/datasource/

# cd /usr/share/grafana/public/app/plugins/datasource/raspimon &&
# find -name "*~" -exec rm -f {} ";"

cd /usr/share/grafana/public/app/plugins/datasource/raspimon_pandas &&
find -name "*~" -exec rm -f {} ";"
