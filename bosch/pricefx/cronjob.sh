#!/bin/bash

source=$HOME/.bashrc
PYTHONPATH=/usr/bin/python3

cd /home/bosch/pricefx
python3 /home/bosch/pricefx/pricefx.py &&
bash /home/bosch/blob-storage/auto_transfer.sh &&

cd /home/bosch/blob-storage
python3 /home/bosch/blob-storage/blob-start.py
