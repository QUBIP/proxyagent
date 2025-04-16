#!/bin/bash

# bash /ProxyAgent/FullScript.sh
echo "##### PA-CFGFILE: $CFGFILE #########"

source venv/bin/activate
python src/proxy_agent.py cfgs/${CFGFILE}

tail -f logs/logfile.log
