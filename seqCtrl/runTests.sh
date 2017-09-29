#!/bin/bash

if [ ! -f GNUmakefile ]; then
  echo "There is now GNUmakefile in the current directory."
  echo "It seems you are not in cta root directory."
  echo "Aborting"
  exit
fi

if [ ! -f  /opt/gfa/python ]; then
  echo "Can not find /opt/gfa/python."
  echo "Required python environment not found."
  echo "Aborting"
  exit
fi

source /opt/gfa/python

python -m unittest seqCtrl.test.TestSeqCtrl.test_basic
