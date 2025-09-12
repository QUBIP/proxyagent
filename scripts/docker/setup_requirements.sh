#!/bin/bash

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt