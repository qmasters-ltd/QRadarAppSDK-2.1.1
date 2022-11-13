#!/bin/bash

export FLASK_APP=app
export FLASK_RUN_HOST=0.0.0.0
export APP_ROOT=/opt/app-root
export SECRET_KEY=${QRADAR_APP_UUID}

trap 'kill -- -$$' EXIT

cd $APP_ROOT && flask run 2>&1 | tee -a $APP_ROOT/store/log/startup.log
