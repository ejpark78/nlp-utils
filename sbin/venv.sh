#!/usr/bin/env bash


sudo apt-get install python3-venv

#python3 -m venv $PWD/venv

pyvenv -h
pyvenv --copies $PWD/venv

cp ~/.pip/pip.conf $PWD/venv/

. /data/nlp_home/ejpark/workspace/crawler/venv/bin/activate

pip3 install -r requirement.txt

