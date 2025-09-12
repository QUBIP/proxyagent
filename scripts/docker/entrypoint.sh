#!/bin/bash

# bash /ProxyAgent/FullScript.sh
echo "##### PA-CFGFILE: $CFGFILE #########"

source venv/bin/activate
python src/proxy_agent/main.py ${CFGFILE}

tail -f logs/logfile.log
