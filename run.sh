#!/usr/bin/env bash

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pyinstaller
pyinstaller tag_finder.py
deactivate
rm -rf ~/.tag_finder
cp -R dist/tag_finder ~/.tag_finder
ln -sf ~/.tag_finder/tag_finder /usr/local/bin/tag_finder
chmod +x /usr/local/bin/tag_finder
