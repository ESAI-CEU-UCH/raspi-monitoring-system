# Pair Plugwise on Linux

**ATTENTION** we were unable to pair using Linux, so we recommended Windows for
pairing :(

## Instructions

This version pairs your Plugwise Circles and Circle+ on Linux.

This version is prepared to work with our monitoring system, so it loads the
data from our MongoDB server.

The pairing is done only when your sockets are initialized. To initialize,
connect your Circle during 3 seconds and then disconnect it during 3
seconds. Repeat it 3 times.

After run the command (it will ask you for the admin password):

```
$ ./initial_connection.sh
```

And finally execute:

```
$ ./run_pairing.sh
```

**Remember** that this software needs a SSH tunnel with our MongoDB server in
order to load the connections network of all Circle and Circle+ devices.

## Original README content

For the moment, this version pairs sockets with identity "000D6F00003".
It works on firmwares 2008-03-10 (Circle+) and 2008-08-26 (USB stick).

### Cloning

go to a folder (for example /home/user/hackstuces) and run:

```
$ git clone git://github.com/hackstuces/PlugwiseOnLinux.git
$ cd PlugwiseOnLinux
```

### Configuring

run the command:

`apt-get install python-serial`

### Using

go to the folder PlugwiseOnLinux and run : 

`$ python pair_pol_v1.py`


### Notes

The pairing is done only when your sockets are initialized. To initialize,
connect your Circle during 3 seconds and then disconnect it during 3
seconds. Repeat it 3 times.

After, run the command:

`$ stty -F /dev/ttyUSB0 ispeed 115200 ospeed 115200 cs8 -parenb`

During the pairing (choose m in the menu), the Circle+ have to turn off (during
few seconds) then turn on.
