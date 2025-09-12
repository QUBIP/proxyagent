import logging
import socket

from pydantic import BaseModel

from proxy_agent.model.core_types import NetworkAddress
from proxy_agent.model.enums import HybridizationMethod, PqcAlgorithm
from proxy_agent.model.messages import (
    CloseMessage,
    GetKeyMessage,
    GetKeyMetadata,
    OpenConnectMessage,
    OpenConnectQos,
)
from proxy_agent.utils.io_utils import load_json_file, send_socket_request

log = logging.getLogger(__name__)

class HybridizationConfig(BaseModel):
    use_qkd: bool
    pqc_algorithm: PqcAlgorithm
    hybridization_method: HybridizationMethod

def get_hybrid_module_url(spi: str, node_id: str, hybrid_config: HybridizationConfig) -> str:
    return f"hybrid://SPI_{spi}@{node_id}?hybridization={hybrid_config.hybridization_method}&kem_mec={hybrid_config.pqc_algorithm}"


class KeyExtractor():
    def __init__(self, address: NetworkAddress, public_nodes_info_path: str) -> None:

        self._address: NetworkAddress = address
        self.public_nodes_info: dict = load_json_file(public_nodes_info_path)
        
        self.hybrid_key_configs: dict[str, HybridizationConfig] = {}
        self.default_hybridization_config: HybridizationConfig = HybridizationConfig(
            use_qkd=True,
            pqc_algorithm=PqcAlgorithm.ML_KEM512,
            hybridization_method=HybridizationMethod.XORING,
        )

    @staticmethod
    def _get_hybridization_config_id(endpoint1: str, endpoint2: str) -> str:

        if endpoint1 < endpoint2:
            return f"{endpoint1}/{endpoint2}"
        else:
            return f"{endpoint2}/{endpoint1}"

    def _get_node_id(self, prefix: str) -> str:
        """
        :param ip: Parameter used to extract the id of the node from the public node information.
        :return:
        """
        return self.public_nodes_info[prefix]["node_id"]

    def _get_hybridization_config(self, selector: dict) -> HybridizationConfig:
        hybrid_config_id = self._get_hybridization_config_id(
            endpoint1=self.public_nodes_info[selector["local-prefix"]]["proxy_agent_ip"],
            endpoint2=self.public_nodes_info[selector["remote-prefix"]]["proxy_agent_ip"],
        )

        if hybrid_config_id in self.hybrid_key_configs:
            return self.hybrid_key_configs[hybrid_config_id]
        else:
            log.error(f"{hybrid_config_id} has no hrybridization config, using the default one")
            return self.default_hybridization_config


    def get_hybrid_key(self, spi: str, selector: dict, key_size: int) -> list:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as kdfix_socket:
            # Connect to the server
            kdfix_socket.connect((self._address.host, self._address.port))
            log.info("Hybrid Module connected to KDFix server at %s", self._address)


            hybrid_config = self._get_hybridization_config(selector)
            oc_qos= OpenConnectQos(
                key_chunk_size=key_size,
                max_bps=32,
                min_bps=32,
                jitter=0,
                priority=0,
                timeout=0,
                ttl=0,
                metadata_mimetype="application/json",
            )

            oc_message = OpenConnectMessage(
                source=get_hybrid_module_url(spi, self._get_node_id(selector["local-prefix"]), hybrid_config),
                destination=get_hybrid_module_url(spi, self._get_node_id(selector["remote-prefix"]), hybrid_config),
                qos=oc_qos,
            )

            oc_response = send_socket_request(kdfix_socket, "OPEN_CONNECT", oc_message)

            # Ensure session is established
            if oc_response.get("status") != 0:
                log.info("[FAILED TO OPEN CONNECTION. EXITING...]")
                # TODO: Return mock key here ?
                raise Exception("The OPEN_CONNECT request failed")

            key_stream_id = oc_response["key_stream_id"]


            gk_message = GetKeyMessage(key_stream_id=key_stream_id, index=0, metadata=GetKeyMetadata())
            gk_response = send_socket_request(kdfix_socket, "GET_KEY", gk_message)

            # We store the key extracted.
            key = gk_response["key_buffer"]

            # Close the connection
            send_socket_request(kdfix_socket, "CLOSE", CloseMessage(key_stream_id=key_stream_id))

            return key

    def install_hybridization_config(self, new_config: dict) -> None:
        config_id = self._get_hybridization_config_id(new_config["endpoint1"], new_config["endpoint2"])
        hybrid_key_config = HybridizationConfig(
            use_qkd=new_config["use-qkd"],
            pqc_algorithm=PqcAlgorithm.parse_from_string(new_config["pqc-algorithm"]),
            hybridization_method=HybridizationMethod.parse_from_string(new_config["hybridization-method"])
        )

        self.hybrid_key_configs[config_id] = hybrid_key_config
        log.info("[NEW CONFIGURATION FOR %s INSTALLED: %s]", config_id, hybrid_key_config)