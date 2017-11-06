#!/usr/bin/env bash

option="
 --delete
 --exclude=.git
 --exclude=.idea
 --exclude=.ipynb_checkpoints
 --exclude=.pycharm_helpers
 --exclude=.ssh
 --exclude=__pycache__
 --exclude=data
 --exclude=docker
 --exclude=example
 --exclude=log
 --exclude=metastore_db
 --exclude=tmp
 --exclude=wrap
 --exclude=resource
 --exclude=parser
 --exclude=model
 --exclude=notebook
 --exclude=venv
"

push.sh meru00 "$option --exclude NlpUtils"
