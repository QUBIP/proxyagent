# Proxy Agent

## Contents
* [Proxy Agent Module](#pam)
* [Installation Guide](#installation-guide)
* [How to Test](#how-to-test)
* [Docker Version](#docker-version)

### Proxy Agent Module <a name="pam"></a>

Proxy agent is an intermediate module between the CCIPS Controller and the CCIPS Agent. 
This module is in charge of managing the key request between the different endpoints that will form the ipsec tunnel. 
It will receive a json packet from the CCIPS Controller, this packet information is based on the RFC 9061 model.
We can think of this model as a template for building ipsec infrastructure. With the parameters contained in this template, 
the proxy agent will construct an ETSI GS QKD 004 request that it will send to the hybridization module. 
The hybridization module will reply with the key for that request and the proxy agent will end up inserting this key in the original template sent by the CCIPS Controller. 
Finally, with the template filled in, it will communicate with the CCIPS Agent to install the relevant security associations.  

### Installation guide <a name="installation-guide"></a>

In order to have the Proxy Agent working we only need to create a virtual environment and run the proxy_agent.py script.
An example is attached: 

```shell
python3 -m venv proxyAgentVenv
source proxyAgentVenv/bin/activate
pip install -r requirements.txt
```

### How to test <a name="how-to-test"></a>

To launch the Proxy Agent we only need to run the "proxy_agent.py" script with the configuration file. An exaple is attached:

```shell
python src/proxy_agent.py cfgs/proxy_agent.json
```
The parameters of the config file are: 

```json
{
  "proxy_agent": {
    "ip": "IPWhereTheProxyAgentWillRun",
    "port": "PortWhereTheProxyAgentWillRun",
    "log":{
        "file":"loggerFile",
        "level":"loggerLevel"
    }
  },
  "hybrid_module": {
    "address": ["IPWhereTheHybridModuleIsLocated", "PortOftheHybridModule"]
  },
  "ccips_agent": {
    "address": ["IPWhereTheCCIPSAgentIsLocated", "PortOftheCCIPSAgent"],
    "user": "userAccestoCCIPSAgent",
    "pass": "passForCCIPSAgent"
  }
}
```
Check the cfgs/proxy_agent.json to see an example correctly formatted and configured.

### Docker Version <a name="docker-version"></a>

If you prefer, you can install docker and docker-compose. When you have both installed you can run the docker-compose
defined in the root of the project, and you will have a docker running a Proxy Agent. You need to reconfigure the docker-compose.yml 
in order to allow external connections to the docker running the Proxy Agent. 

```shell
docker-compose down; docker-compose up --build
```

