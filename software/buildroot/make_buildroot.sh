#!/bin/sh

# building the python-picamera package fails if this environment variable is not set.
# See: https://github.com/waveform80/picamera/issues/578
export READTHEDOCS=True

make