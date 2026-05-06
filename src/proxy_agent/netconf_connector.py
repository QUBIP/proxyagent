import logging
import time

import ncclient.manager
import xmltodict

from proxy_agent.model.core_types import NetworkAddress, UserCredentials

log = logging.getLogger(__name__)


class NetconfConnector:
    def __init__(
        self, address: NetworkAddress, credentials: UserCredentials, connection_timeout: int
    ) -> None:
        log.info("[STARTING THE NETCONF SESSION WITH THE CCIPS AGENT]")

        while True:
            try:
                self._manager: ncclient.manager.Manager = ncclient.manager.connect(
                    host=address.host,
                    port=address.port,
                    username=credentials.username,
                    password=credentials.password,
                    timeout=connection_timeout,
                    hostkey_verify=False,
                )
                break
            except Exception as e:
                log.error(f"[NETCONF INITIALIZATION FAILED BECAUSE OF: {e}]")
                time.sleep(1)
                log.info("[RETRYING NETCONF CONNECTION]")
        # except Exception as e:
        #     log.error(f"[ERROR HAPPEN WHEN CONNECTING TO NETCONF IN: {ip}:{port}\n\t{e}]")
        log.info("[NETCONF SESSION STARTED SUCCESSFULLY]")

    def _model_to_xml(self, final_content: dict) -> str:
        log.debug("Parsing JSON to XML")

        xml_model_data = xmltodict.unparse({ "ipsec-ikeless" : final_content}, full_document=False)
        return xml_model_data.replace("<ipsec-ikeless>", "<ipsec-ikeless xmlns=\"urn:ietf:params:xml:ns:yang:ietf-i2nsf-ikeless\">")

    def _send_edit_config_rpc(self, new_config: str) -> None:
        log.info("PREPARED NETCONF MESSAGE: %s", new_config)

        header: str = """<nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">\n"""
        footer: str = "</nc:config>"
        xml_content: str = f"{header}{new_config}{footer}"

        log.info("[CONNECTING CCIPS AGENT]")
        try:
            self._manager.edit_config(
                target="running", config=xml_content, test_option="test-then-set"
            )
        except Exception as e:
            log.error(f"[ERROR WHEN CONNECTING AGENT: {e}]")

    def send_new_config(self, final_content: dict) -> None:
        new_config = self._model_to_xml(final_content)

        self._send_edit_config_rpc(new_config)

    def send_delete(self, delete_content: dict, delete_location: str) -> None:

        xml_message = self._model_to_xml(delete_content)
        new_config: str = xml_message.replace(f"<{delete_location}>", f"<{delete_location} nc:operation=\"delete\">")

        self._send_edit_config_rpc(new_config)

    def cleanup(self) -> None:
        self._manager.close_session()
        log.info("Netconf session stopped.")