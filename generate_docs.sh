#!/bin/bash
# sphinx-apidoc -o docs raspi_mon_sys/
oldpwd=$(pwd)
cd docs/
make html
make latexpdf
cd $oldpwd
