#!/bin/bash

export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/appengine-token.json"
export GAE_ENV="localdev"
python3 main.py