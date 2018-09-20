#!/bin/bash
set -o errexit

DEVICE_NAME=""
ATTACH="-attach"

usage()
{
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "    -d <device name>     Device name (e.g. SAR-CCTA-ESA)"
    echo "    -n                   Do not attach to existing caQtDM. Open new caQtDm."
    echo "    -h                   This help"
}

while getopts ":d:nh" o; do
    case "${o}" in
        d)
            DEVICE_NAME=${OPTARG}
            ;;
        n)
            ATTACH=""
            ;;
        h)
            usage
            exit 0
            ;;
        *)
            usage
            exit 1
            ;;
    esac
done

if [ $OPTIND -le 1 ]; then
    usage
    exit 1
fi

if [ -z $DEVICE_NAME ]; then
    usage
    exit 1
fi

macro="P=$DEVICE_NAME:"
caqtdm $ATTACH -macro "$macro" performance.ui &
