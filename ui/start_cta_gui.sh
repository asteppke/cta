#!/bin/bash

PYTHON_DIR=/opt/gfa/python

if [ ! -f $PYTHON_DIR ]; then
  echo "ERROR: Unexpected environment."
  echo "ERROR: File $PYTHON_DIR to load gfa python not found."
  exit 1
else
  source $PYTHON_DIR ""
fi

python cta_gui.py $@

