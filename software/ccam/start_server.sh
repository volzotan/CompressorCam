#!/bin/sh

# export FLASK_APP=fserv/fserver.py
# flask run --host=0.0.0.0

gunicorn -b 0.0.0.0:80 fserv.fserver:app