#!/bin/sh

# export FLASK_APP=fserv/fserver.py
# flask run --host=0.0.0.0

# gunicorn -b 0.0.0.0:80 fserv.fserver:app    \
# --workers=2                                 \
# --log-file /media/storage/log_gunicorn.log  \
# --log-level debug                           \
# --timeout 30

gunicorn -b 0.0.0.0:80 fserv.fserver:app    \
--workers=2                                 \
--timeout 30
