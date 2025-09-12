#!/bin/bash
set -x
flag=0

# ----------------------------------------
# Tunnel Controller ip
controller_ip=127.0.0.1

# Netopeer server ip. The port of the netoserver is by default on 830
# Case Network HOST -> HOST
control_network_ip=127.0.0.1
remote_control_network_ip=10.20.20.17

data_network_ip=10.20.20.15
remote_data_network_ip=10.20.20.17

internal_network_ip=10.20.20.0/27
remote_internal_network_ip=10.20.20.0/27

# NEW CFG CALL
cfg="{\"control_network_ip\":\"$control_network_ip\",\"data_network_ip\":\"$data_network_ip\",\"internal_network_ip\":\"$internal_network_ip\",\"remote_internal_network_ip\":\"$remote_internal_network_ip\",\"remote_data_network_ip\":\"$remote_data_network_ip\",\"remote_control_network_ip\":\"$remote_control_network_ip\"}"
#fi

Response=$(curl --header "Content-Type: application/json" --data $cfg --request POST http://$controller_ip:3000/register)

#flag=1
echo $Response
if [ $Response == "OK" ]
then
  flag=1
elif [ $Response == "ERROR" ]
then
  flag=0
  sleep 3
else
  flag=0
fi


