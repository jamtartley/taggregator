#!/usr/bin/env bash
clear
python3 -m venv venv
source venv/bin/activate
pip3 install --upgrade pytest
clear
python3 -m pytest -v
pip3 install -e . > /dev/null 2>&1
tagf "$@"
