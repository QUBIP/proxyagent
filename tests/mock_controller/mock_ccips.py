import json
import time
import requests
import sys, os
sys.path.append(os.getcwd())
from pyangbind.lib.serialise import pybindIETFXMLDecoder
import pyangbind.lib.pybindJSON as pbJ
import sys, os
from threading import Thread
sys.path.append(os.getcwd())

def send_json_configuration_to_proxy_agent(test):
    print(f"[STARTING SENDING CONFIGURATION]")
    headers = {"Content-Type": "application/json"}
    with open(f"{test['test_file']}") as f:
        j_dict_config: dict = json.loads(f.read())
    print(f"[JSON MESSAGE: \n{json.dumps(j_dict_config, indent=4)}]")

    url: str = f"http://{test['ip']}:{test['port']}/register"
    requests.post(url, json=j_dict_config, headers=headers)
    print(f"RESPONSE: {requests.status_codes}")

def main():
    proxy_agent_test_sad: dict = {
        "1":{
            "ip": "192.168.159.35",
            "port": 3000,
            "test_file": "docs/templates/json/TID_SadEntry.json"
        },
        "2":{
            "ip": "192.168.159.21",
            "port": 3000,
            "test_file": "docs/templates/json/TID_SadEntry.json"
        }
     }

    for _, test in proxy_agent_test_sad.items():
        thread = Thread(target=send_json_configuration_to_proxy_agent, args=(test,))
        thread.start()
    
    print("WATING FOR INSTALL SPDs")
    time.sleep(10)

    proxy_agent_test_spd: dict = {
        "1":{
            "ip": "192.168.159.35",
            "port": 3000,
            "test_file": "docs/templates/json/TID_SpdEntry.json"
        },
        "2":{
            "ip": "192.168.159.21",
            "port": 3000,
            "test_file": "docs/templates/json/TID_SpdEntry.json"
        }
    }

    for _, test in proxy_agent_test_spd.items():
        thread = Thread(target=send_json_configuration_to_proxy_agent, args=(test,))
        thread.start()

if __name__ == "__main__":
    main()
