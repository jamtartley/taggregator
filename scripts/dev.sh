#!/usr/bin/env bash
clear
python3 -m venv venv
source venv/bin/activate
pip3 install --upgrade pytest
clear
python3 -m pytest -v
python3 setup.py install > /dev/null 2>&1
tagg "$@"
deactivate
