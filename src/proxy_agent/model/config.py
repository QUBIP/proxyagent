
from pydantic import BaseModel

from proxy_agent.model.core_types import NetworkAddress, UserCredentials

## Base Config ##

class LoggingConfig(BaseModel):
    file: str
    level: str

class HybridModuleConfig(BaseModel):
    address: NetworkAddress
    public_node_info_path: str

class NetconfConfig(BaseModel):
    address: NetworkAddress
    credentials: UserCredentials

class ProxyAgentConfig(BaseModel):
    proxy_agent_address: NetworkAddress
    log: LoggingConfig
    hybrid_module: HybridModuleConfig
    ccips_agent: NetconfConfig
