#!/usr/bin/env bash

# Shell script to be replaced with python when things stabilze.
#
# We expect the virtual environment to reside in the local folder venv.

d=`readlink -e .`;
echo $d;
for a in `ls *py`; do
    `gnome-terminal -x $d/venv/bin/python $a`;
done
