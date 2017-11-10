#!/bin/bash

CURRENTDIR=`pwd`

# Resolve symlinks
BASEDIR=$0
while [ -h "$BASEDIR" ]; do
    ls=`ls -ld "$BASEDIR"`
    link=`expr "$ls" : '^.*-> \(.*\)$' 2>/dev/null`
    if expr "$link" : '^/' 2> /dev/null >/dev/null; then
        BASEDIR="$link"
    else
        BASEDIR="`dirname "$BASEDIR"`/$link"
    fi
done
BASEDIR=`dirname "$BASEDIR"`

PYTHON_DIR=/opt/gfa/python

if [ ! -f $PYTHON_DIR ]; then
  echo "ERROR: Unexpected environment."
  echo "ERROR: File $PYTHON_DIR to load gfa python not found."
  exit 1
else
  source $PYTHON_DIR ""
fi

python $BASEDIR/cta_gui.py $@

