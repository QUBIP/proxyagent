# Proxy Agent

## Contents
* [Introduction](#introduction)
* [Installation](#installation)
* [Configuring the proxy agent](#configuring-the-proxy-agent)

## Introduction

Proxy agent is an intermediate module between the CCIPS Controller and the CCIPS Agent.
This module is in charge of managing the key request between the different endpoints that will form the ipsec tunnel.

---

It will receive a json packet from the CCIPS Controller, this packet information is based on the RFC 9061 model.We can think of this model as a template for building ipsec infrastructure.

With the parameters contained in this template,
the proxy agent will construct an ETSI GS QKD 004 request that it will send to the hybridization module.

The hybridization module will reply with the key for that request and the proxy agent will end up inserting this key in the original template sent by the CCIPS Controller.

Finally, with the template filled in, it will communicate with the CCIPS Agent to install the relevant security associations.

## Installation

### Bare installation

In order to have the Proxy Agent working we only need to create a virtual environment and run the proxy_agent.py script.
An example is attached:

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To run the Proxy Agent we only need to run the "proxy_agent.py" script with the configuration file. An exaple is attached:

```shell
python src/proxy_agent.py config/proxy_agent.json
```

### Docker

While the proxy agent can be run directly, the tool that is usually used when deploying this component is Docker. Whether you use base docker or docker compose there are some things you may need to know:
- The building process requires an argument, that is `CFGFILE`. It contains the path to the configuration file you want to use for that instance of docker, for example, `config/proxy_agent.json`.
- In the current version of the project it will allways copy the public node info in `config/public_node_info.json`. Any changes that configuration must be done in that file.
- The proxy agent requires the port in `proxy_agent_address` expose so it can receive instructions from controllers that do not belong to any docker network the proxy agent belongs.

## Configuring the proxy agent

### Main configuration

The parameters of the config file are:

```json
{
  "proxy_agent_address" : {
    "host" : "hostWhereTheProxyAgentWillRun",
    "port" : 3000 # Port where the proxy will run
  },
  "log":{
      "file": "loggerFile",
      "level": "loggerLevel"
  },
  "hybrid_module": {
    "address": {
      "host" : "hostWhereTheHybridModuleIsLocated",
      "port" : 24030 # Port where the hybridation module is located
    },
    "public_node_info_path" : "./path/to/public_node_info.json"
  },
  "ccips_agent": {
    "address": {
      "host" : "hostWhereTheCCIPSAgentIsLocated",
      "port" : 12938 # Port where the ccips agent is located
    },
    "credentials" : {
      "username": "usernameToAccessToCcipsAgent",
      "password": "passwordForCcipsAgent"
    }
  }
}
```
Check the config/proxy_agent.json to see an example correctly formatted and configured.

### Public node information

This files contain usefull information about the nodes in the QKD/Hybridization network:

Note: The keys in the dictionary are the prefix of the side of the ipsec tunnel the information belongs to.

```json
{
    "10.0.0.11/32": {
        "node_id":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "proxy_agent_ip": "192.168.159.35",
        "role": {
            "192.168.123.200": "SERVER",
            "192.168.123.300": "SERVER"
        }
    },
    "10.0.0.20/32":{
        "node_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "proxy_agent_ip": "192.168.159.21",
        "role": {
            "192.168.123.100": "CLIENT",
            "192.168.123.300": "SERVER"
        }
    },
    "192.168.123.300": {
        "node_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "proxy_agent_ip": "192.168.159.37",
        "role": {
            "192.168.123.100": "CLIENT",
            "192.168.123.200": "CLIENT"
        }
    }
}
```