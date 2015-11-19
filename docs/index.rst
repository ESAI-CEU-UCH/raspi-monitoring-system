.. Raspi Monitoring System documentation master file, created by
   sphinx-quickstart on Thu Nov  5 10:58:23 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Raspi Monitoring System's documentation!
===================================================

Raspi Monitoring System (aka *raspimon*) is a system developed for low-cost
monitoring of households. It is intended to be uploaded into a Raspberry Pi
computer with internet connection. The system avoids writing any data in the SD
card extending its life time. In order to simplify the problem, one computer is
designated to be installed into one house, and the MAC address of its Ethernet
card identifies for configuration purposes. Configuration data is stored into a
MongoDB server located in our facilities which allow replication and sharding.
The system is some kind of modular application where every module has a simple
public interface (`start()`, `stop()`, `publish()`) and each one configures
itself using our cited MongoDB server or by other means through an internet
connection. Logging services have been developed to use mail messages instead of
log files.

Among the software developed for this project, we use open source libraries
adapted from other authors (`emonhub`, `plugwise` and `aemet` libraries), some
libraries taken as they are (`swutil`), and other utilities (for instance the
firmware code for EmonTX v3).

.. toctree::
   :maxdepth: 4

   raspi_mon_sys
   emonhub
   plugwise
   aemet
