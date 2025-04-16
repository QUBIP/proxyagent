#!/bin/bash

# Install essentials
apt update -y
apt upgrade -y
apt install -y build-essential openssh-server python3-dev gcc git vim virtualenv gnupg curl wget nano iputils-ping iproute2 python3-pip zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev libxml2-dev libffi-dev python3-lxml python3-cffi python3-distutils 

virtualenv -p python3 venv/
source venv/bin/activate

pip3 install --upgrade pip
pip3 install --upgrade pip setuptools wheel
pip3 install -r requirements.txt
pip3 install -r ProxyAgent_requirements.txt
