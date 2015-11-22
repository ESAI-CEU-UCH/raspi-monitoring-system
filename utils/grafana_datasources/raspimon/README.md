# Raspimon MongoDB Time Series plugin for Grafana

Raspimon MongoDB is an schema for time-series data storage using a MongoDB
database. It has been implemented to connect using a default database and
collection names. This can be parametrized in the future.

## Installation guide

Copy ```raspimon/``` into ```<grafana-2.x.x source
directory>/public/app/plugins/datasource/``` directory and restart Grafana
server. Then proceed as you would normally do with any built-in plugin by adding
it through the data source menu.  Be sure to set URL to the http port for
`http://localhost:5000`.
