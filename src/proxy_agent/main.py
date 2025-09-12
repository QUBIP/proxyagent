import os
import sys

sys.path.append(os.path.abspath("./src"))

import copy
import json
import logging
import threading

from flask import Flask, request
from werkzeug.serving import run_simple

from proxy_agent.format_adapters import (
    adapt_spd_algo_structure,
    byte_list_to_octect_string,
    extract_entries,
)
from proxy_agent.hybrid_key_requester import KeyExtractor
from proxy_agent.model.config import ProxyAgentConfig
from proxy_agent.netconf_connector import NetconfConnector
from proxy_agent.utils.io_utils import load_json_file
from proxy_agent.utils.log_utils import create_simple_logger

log = logging.getLogger(__name__)

class ProxyAgent:
    def __init__(self, config_path: str) -> None:

        config: ProxyAgentConfig = ProxyAgentConfig.model_validate(load_json_file(config_path))

        self._address = config.proxy_agent_address
        create_simple_logger(log_config=config.log)

        # Security Associations stored by SPI index.
        self._flask_app = Flask(__name__)
        self._configure_endpoints()

        self._netconf_connector_lock: threading.Lock = threading.Lock()
        self._netconf_connector: NetconfConnector = NetconfConnector(
            address=config.ccips_agent.address,
            credentials=config.ccips_agent.credentials,
            connection_timeout=120,
        )

        self._key_extractor: KeyExtractor = KeyExtractor(
            address=config.hybrid_module.address,
            public_nodes_info_path=config.hybrid_module.public_node_info_path,
        )

    def _configure_endpoints(self) -> None:
        self._flask_app.add_url_rule(rule="/ipsec-entries", view_func=self._register_entries, methods=["POST"])
        self._flask_app.add_url_rule(rule="/ipsec-entries", view_func=self._delete_entries, methods=["DELETE"])

        self._flask_app.add_url_rule(rule="/createqkd", view_func=self._add_hybrid_config, methods=["POST"])

    def start(self) -> None:
        log.info("[PROXY AGENT RUNNING ON %s]", self._address)
        run_simple(hostname=self._address.host, port=self._address.port, threaded=True, application=self._flask_app)

    ##### FLASK APP METHODS #####

    # POST method /ipsec-entries endpoint
    def _register_entries(self)-> dict[str, str]:
        content = request.data.decode('utf-8')

        extracted_entries = extract_entries(content)
        for entry in extracted_entries:
            log.debug("[MANAGING JSON ENTRY: %s]", entry)

            if "sad-entry" in entry: # SAD entry is processed
                log.debug("[SAD CONTENT RECEIVED]")

                thread = threading.Thread(
                    target=self._register_sad_entry,
                    args=(entry,),
                    name=f"sad-{entry['sad-entry']['name']}"
                )
                thread.start()

            elif "spd-entry" in entry: # SPD entry is processed
                log.debug("[SPD CONTENT RECEIVED]")

                thread = threading.Thread(
                    target=self._register_spd_entry,
                    args=(entry,),
                    name=f"spd-{entry['spd-entry']['name']}-{entry['spd-entry']['direction']}"
                )
                thread.start()

            else:
                # NO content to process, ERROR sent.
                log.error("[WRONG CONTENT]")

        return {"STATUS": "OK"}

    # DELETE method /ipsec-entries endpoint
    def _delete_entries(self) -> dict[str, str]:
        content = request.data.decode("utf-8")
        entries = extract_entries(content)

        for entry in entries:
            if "sad-entry" in entry:
                root_entry = {"sad" : { "sad-entry" : {entry["sad-entry"]["name"] : entry["sad-entry"]}}}
                with self._netconf_connector_lock:
                    self._netconf_connector.send_delete(root_entry, "sad-entry")
            elif "spd-entry" in entry:
                root_entry = {"spd" : { "spd-entry" : {entry["spd-entry"]["name"] : entry["spd-entry"]}}}
                with self._netconf_connector_lock:
                    self._netconf_connector.send_delete(root_entry, "spd-entry")

        return {"STATUS" : "OK"}

    # POST method /createqkd endpoint
    def _add_hybrid_config(self)-> dict[str, str]:
        content = request.data.decode("utf-8")
        new_config = json.loads(content)

        self._key_extractor.install_hybridization_config(new_config)
        return {"STATUS": "OK"}


    ##### SUPPORT METHODS #####

    def _register_sad_entry(self, sad_content: dict) -> None:
        log.debug(f"[WORKING ON SAD ENTRIES: \n{sad_content}]")

        spi: str = sad_content["sad-entry"]["ipsec-sa-config"]["spi"]
        selector: dict = sad_content["sad-entry"]["ipsec-sa-config"]["traffic-selector"]

        # Get the key from the hybridization module.
        raw_key =  self._key_extractor.get_hybrid_key(spi, selector, 20)
        log.debug(f"[SPIs AND KEY ASSOCIATED: SPI={spi} KEY={raw_key}]")

        adapted_key = byte_list_to_octect_string(raw_key)[:120]
        log.debug("[KEY ADAPTED TO: %s]", adapted_key)

        # Adapt key to the CCIPS Agent needs.
        log.info("[SETTING NEW KEY INTO THE RFC 9061 TEMPLATE.]")
        content_with_key = self._set_key_in_sad_template(sad_content, adapted_key)
        log.debug(f"[NEW CONTENT: \n {json.dumps(content_with_key, indent=4)}]")

        with self._netconf_connector_lock:
            # NETCONF:
            # With the initial content of the RFC9061, SPIs and Keys, the final configuration is sent to the CCIPS Agent.
            self._netconf_connector.send_new_config(content_with_key["ipsec-ikeless"])

    def _register_spd_entry(self, spd_content: dict) -> None:
        log.debug("[WORKING ON SPD ENTRIES]")
        adapted_entry = adapt_spd_algo_structure(spd_content)

        spd_from_root: dict = {
            "spd": {
                "spd-entry": {
                    adapted_entry["spd-entry"]["name"]: adapted_entry["spd-entry"]
                }
            }
        }
        log.debug(f"[FINAL SPD STRUCTURE: \n{json.dumps(spd_from_root, indent=4)}]")

        with self._netconf_connector_lock:
            # After the SDP structure is compliant with the 9061 RFC, we communicate with NETCONF to set the policies flows.
            self._netconf_connector.send_new_config(spd_from_root)


    def _set_key_in_sad_template(self, sad_content: dict, adapted_key: str) -> dict:
        """
        :param content: This is the packet sent from the CCIPS Controller. We will write into this configuration
        the key extracted from the hybrid module.
        :param spis_and_final_keys: The SPIs with the new key extracted from the Hybrid Module.
        :return: A new RFC 9061 Template with the keys installed.
        """
        new_content: dict = copy.deepcopy(sad_content)
        new_content_esp_config =  new_content["sad-entry"]["ipsec-sa-config"]["esp-sa"]

        new_content_esp_config["encryption"]["key"] = adapted_key
        new_content_esp_config["encryption"]["iv"] = adapted_key
        new_content_esp_config["integrity"]["key"] = adapted_key

        sad_structure: dict = {"sad-entry": {new_content["sad-entry"]["name"]: new_content["sad-entry"]}}

        return {"ipsec-ikeless": { "sad": sad_structure}}


def main(cfg_file_path: str) -> None:
    p_agent : ProxyAgent = ProxyAgent(cfg_file_path)
    p_agent.start()

if __name__ == '__main__':
    # CFG File for the Proxy Agent.
    main(sys.argv[1])
