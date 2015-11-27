# Raspi monitoring system

The monitoring system developed for raspberry-pi under the project GV/2015/088.

**Important!!!** All the code and utilities will be uploaded into the folder:
  **raspi_mon_sys**

## Useful links

- [ESAI-CEU-UCH/PlugwiseOnLinux](https://github.com/ESAI-CEU-UCH/PlugwiseOnLinux)
  forked from
  [hackstuces/PlugwiseOnLinux](https://github.com/hackstuces/PlugwiseOnLinux).

- [ESAI-CEU-UCH/Plugwise-2-py](https://github.com/ESAI-CEU-UCH/Plugwise-2-py) forked from [SevenW/Plugwise-2-py](https://github.com/SevenW/Plugwise-2-py).

- [Blog entry about PlugwiseOnLinux https](//blog.karssen.org/2011/11/20/using-plugwise-adapters-with-linux/).

- [Adding RTC to Rpi](http://thepihut.com/blogs/raspberry-pi-tutorials/17209332-adding-a-real-time-clock-to-your-raspberry-pi).

- [Adding RTC to emonPi](http://openenergymonitor.blogspot.com.es/2015/07/adding-rtc-to-emonpi.html).

- [Configure Raspberry Pi without cables](http://blog.self.li/post/63281257339/raspberry-pi-part-1-basic-setup-without-cables).

## Project outline

The project is structured in several folders.

```
|
|- docs/ documentation generated with Python sphynx.
|
|- etc/ content which should be configured and added to etc folder.
|
|- raspi_mon_sys/ Python package with monitoring system utilities.
|
|- notes/ some annotations related with the project.
|
|- swutil/ package needed by OpenEnergyMonitor.
|
|- test/ some unit tests (incomplete).
|
\- utils/ utilities related with the project, as Grafana data sources.
```

### Execution and installation at Raspberry Pi

The monitoring system has been prepared to be executed and stopped through two
shellscripts. Both require the code at `$HOME/raspi-monitoring-system/`. So,
you can start the system.

```
$ ./start.sh
```

Or stop the system:

```
$ ./stop.sh
```

Note that `start.sh` uses screen command to execute in background some Python
processes. `stop.sh` sends a keyboard break signal to the processes, waits
until their successful end and waits an additional time to allow next processes
to be acknowledge of previous one dead. In order to execute at boot this system
we have written a `systemd` script, which can be installed and executed as
follows:

```
$ sudo cp etc/systemd/system/raspimon.service /etc/systemd/system
$ sudo systemctl daemon-reload
$ sudo systemctl enable raspimon
$ sudo systemctl start raspimon
```

### Persistence server side

The system uses a MongoDB storage for historical data analytics. MongoDB storage
can be managed using *monogo-express* utility, and it can be executed (you need
*gnome-open*) doing:

```
$ cd utils/database_manager/
$ ./execute.sh
```

This will open a window in your browser using *gnome-open* and through this
window you can check database status. However, a better to analyze this data is
using [Grafana](http://grafana.org/) in the same server where MongoDB is
installed. You will need to copy the plugin located at
`utils/grafana_datasources/raspimon_pandas/` using this commands:

```
$ cd utils/grafana_datasources/raspimon_pandas/
$ sudo ./install.sh
$ sudo cp ../../../etc/init/raspimon_pandas.conf /etc/init/
$ sudo service grafana-server stop
$ sudo service grafana-server start
$ sudo service
$ sudo initctl reload
$ sudo initctl start raspimon_pandas
```

## Acknowledgments

- Maarten Damen for his Plugwise unleashed report.
- Hackstuces for his Pair Plugwise On Linux script.
- Seven Watt for Plugwise-2-py library, and also to Sven Petai and Maarten Damen
  for the python-plugwise and POL v0.2.
- The team of Open Energy Monitor project for their emonhub library and their
  different firmware source code for EmonTX v3.
