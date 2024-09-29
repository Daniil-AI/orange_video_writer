#!/bin/bash

cd /home/orangepi/Desktop/orange_video_writer
source .venv/bin/activate
export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.9/site-packages/cv2/python-3.9/
DISPLAY=:0 python3 main.py
