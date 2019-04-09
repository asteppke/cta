How to build and install cta_lib package in local conda environment
-------------------------------------------------------------------
[]$ source /opt/gfa/python 3.6
[]$ conda create -c paulscherrerinstitute --name cta_lib python=3.6 numpy pyepics
[]$ source activate cta_lib
[]$ conda build conda-recipe
[]$ conda install --use-local cta_lib

How to uninstall cta_lib package from local conda environment
-------------------------------------------------------------
[]$ conda remove --name cta_lib cta_lib
