#/bin/bash

curl -X 'POST' \
   'http://192.168.159.239:5000/ccips' \
   -H 'accept: application/json' \
   -H 'Content-Type: application/json' \
   -d '{
   "nodes": [
        {
          "ipData": "10.0.0.20",
          "ipControl": "192.168.159.21"
        },
        {
          "ipData": "10.0.0.11",
          "ipControl": "192.168.159.35"
        }

],
"encAlg": [
   "aes-cbc"
],
"intAlg": [
   "sha2-256"
],
"softLifetime": {
   "nTime": 25
},
"hardLifetime": {
   "nTime": 50
 }
}'
