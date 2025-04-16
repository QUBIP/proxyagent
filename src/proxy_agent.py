import sys, os
import time
import threading
from ncclient.transport.session import *
from flask import Flask, request, Response
from werkzeug.serving import run_simple
import simplejson as json
from ncclient import manager
from ncclient.transport.session import *
import pyangbind.lib.pybindJSON as pbJ

sys.path.append(os.getcwd())
import utils.pyYang.ietf_i2nsf_ikeless as ikelessClass
from utils.logerutil import create_simple_logger
from hybrid_key_requester import Key_Extractor
from utils.PyangbindXMLEncoder import XMLEncoder

class ProxyAgent:
    def __init__(self, cfg):

        with open(f"{cfg}") as f:
            self._config: dict = json.load(f)

        with open(f"cfgs/public_node_info.json") as f:
            self.public_nodes_info: dict = json.loads(f.read())

        self._log: logging.Logger = create_simple_logger(level=self._config["proxy_agent"]["log"]["level"],
                                                         filename=self._config["proxy_agent"]["log"]["file"])

        # Security Associations stored by SPI index.
        self._SAs: dict = {}
        self._spis_tunnels: dict = {}
        self._flask_app = Flask(__name__)
        self._configure_endpoints()
        self._netconf_connector: manager.connect_ssh = self._get_netconf_connector()
        self._init_controller(self._config["proxy_agent"]["ip"], self._config["proxy_agent"]["port"])

    def _configure_endpoints(self):
        @self._flask_app.route('/register', methods=['POST'])
        def register():
            content = request.data.decode('utf-8')
            n_content = self.extract_entries(content)
            for i, entry in enumerate(n_content, 1):
                j_entry_str: str = json.dumps(entry)  
                j_entry_dict: dict = json.loads(j_entry_str)
                self._log.debug(f"[RECEIVED DATA: \n - {i}: \n{json.dumps(j_entry_dict)}]")
                self._process_request(j_entry_dict)
            return {"STATUS": "OK"}

    def extract_entries(self, input_string):
        """
        Extracts and parses multiple JSON objects from a given string.
    
        Args:
            input_string (str): A string containing multiple JSON objects.
    
        Returns:
            list: A list of dictionaries representing the parsed JSON objects.
        """
        self._log.debug("[EXTRACTING ENTRIES]")
        try:
            entries = []
            stack = []
            json_objects = []
            current_object = ""
    
            # Scan the input string character by character
            for char in input_string:
                if char == "{":
                    stack.append(char)
                if char == "}":
                    if stack:
                        stack.pop()
    
                # Append characters to current JSON object
                current_object += char
    
                # If stack is empty, we have a complete JSON object
                if not stack and current_object.strip():
                    json_objects.append(current_object.strip())
                    current_object = ""
    
            # Parse each detected JSON object
            for obj in json_objects:
                try:
                    parsed_json = json.loads(obj)
                    if "spd-entry" in parsed_json or "sad-entry" in parsed_json:
                        entries.append(parsed_json)
                except json.JSONDecodeError as e:
                    self._log.error(f"Skipping invalid JSON object due to error: {e}")
            return entries
    
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []
    
    def _get_netconf_connector(self):
        ip: str = self._config["ccips_agent"]["address"][0]
        port: int = self._config["ccips_agent"]["address"][1]
        user: str = self._config["ccips_agent"]["user"]
        neto_password: str = self._config["ccips_agent"]["pass"]

        try:
            m: manager.connect_ssh = manager.connect(host=ip, port=port, username=user,
                                                     password=neto_password, hostkey_verify=False)
            return m
        except Exception as e:
            self._log.error(f"[ERROR HAPPEN WHEN CONNECTING TO NETCONF IN: {ip}:{port}\n\t{e}]")
        return ""

    def _init_controller(self, ip, port):
        self._log.info(f"[PROXY AGENT RUNNING ON {ip}:{port}]")
        run_simple(hostname=ip, port=int(port), threaded=True, application=self._flask_app)

    def sad_management(self, sad_content):
        self._log.debug(f"[WORKING ON SAD ENTRIES: \n{sad_content}]")

        sad_structure: dict = {"sad-entry": {sad_content["sad-entry"]["name"]: sad_content["sad-entry"]}}
        new_content: dict = {"ipsec-ikeless": { "sad": sad_structure}}
        # Extract SPI and Tunneling IP to create the Key request
        spis_and_tunnels = self._extract_spis_and_tunneling_info_from_model(new_content)

        # With SPI and Tunneling IP, SPI and KeyRequest is generated
        self._spis_and_key_requests = self._generate_hybrid_key_request(spis_and_tunnels)
        self._log.debug(f"[SPIS AND TUNNELS: \n{json.dumps(self._spis_and_key_requests, indent=4)}]")

        # With SPI and KeyRequest, the request to the Hybrid module is done.
        spis_and_keys: dict = {}
        spis_and_final_keys: dict = {}
        for k, v in self._spis_and_key_requests.items():
            spis_and_keys[k] = self.request_key(v)
        self._log.debug(f"[SPIs AND KEY ASSOCIATED: \n{json.dumps(spis_and_keys)}]")

        for k, v in spis_and_keys.items():
            spis_and_final_keys[k] = self._adapt_key(v)

        self._log.debug(f"[SPIs with Keys: \n{json.dumps(spis_and_final_keys)}]")

        # Adapt key to the CCIPS Agent needs.
        self._log.info("[SETTING NEW KEY INTO THE RFC 9061 TEMPLATE.]")
        content_with_key = self.set_key_in_template(new_content, spis_and_final_keys)
        self._log.debug(f"[NEW CONTENT: \n {json.dumps(content_with_key, indent=4)}]")

        # NETCONF:
        # With the initial content of the RFC9061, SPIs and Keys, the final configuration is sent to the CCIPS Agent.
        self._communicate_with_netconf(new_content["ipsec-ikeless"])

    def spd_management(self, content: dict):
        self._log.debug("[WORKING ON SPD ENTRIES]")
        top_ikeless_class: str = "yc_ipsec_ikeless_ietf_i2nsf_ikeless__ipsec_ikeless"
        def generate_esp_algo_structure(initial_config: dict) -> dict:
            """
            :param initial_config: SPD Data that we will receive from the CCIPS Controller .
                                   We need to adapt it to the "esp-algorithms" structure to the 9061 format for being able
                                   to build the xml netconf message correctly.

            -> Final result:
             "esp-algorithms": {
                "integrity": [2],
                "encryption": {
                    "1": {
                        "id": 1,
                        "algorithm-type": 3,
                        "key-length": 128,
                        "__yang_order": 0
                    }
                }
            }
            :return:
            """
            self._log.debug(f"[INITIAL CONFIG: \n{json.dumps(initial_config, indent=4)}]")
            esp_algo_received: dict = initial_config["spd-entry"]["ipsec-policy-config"]["processing-info"] \
                ["ipsec-sa-cfg"]["esp-algorithms"]
            esp_algo_adapted: dict = {
                "integrity": [esp_algo_received["integrity"]],
                "encryption": {
                    esp_algo_received["encryption"]["id"]: esp_algo_received["encryption"]
                }
            }
            return esp_algo_adapted

        spd_structure: dict = {"spd-entry": {
            content["spd-entry"]["name"]: content["spd-entry"]}
        }

        """
            A transformation is necessary from the structure in the esp-algorithm container that we received 
            to the official standard 9061 Template, this is necessary to build the XML NETCONF message at the end:
                * What we received:                    
                  "esp-algorithms": {
                      "integrity": "5",
                      "encryption": {
                        "id": 1,
                        "algorithm-type": "12",
                        "key-length": "32"
                      }
                   }
                * What we need to send:
                  "esp-algorithms": {                                                                                                                                                                        
                      "integrity": ["5"]                                                                                                                                                                         
                      "encryption": {                                                                                                                                                                        
                          "1": {                                                                                                                                                                             
                             "id": 1,                                                                                                                                                                       
                             "algorithm-type": 3,                                                                                                                                                           
                             "key-length": 128                                                                                                                                                              
                          }                                                                                                                                                                                  
                      }
            1) The correct esp-algorithm structure is first generated from the information that we receive.
            2) The old information is deleted from the original information.
            3) The information generated in the 1) step is added into a dictionary that will be the final structure 
                json formatted.
            4) This information is encapsulated into an upper herarchy level structure int SPD xml tree
            5) When everything is ready, transform the information to the final XML.   
               This must be done in the Proxy Agent each time we receive a configuration from the CCIPS Controller.
            """
        # 1)
        esp_algo_adapted: dict = generate_esp_algo_structure(content)
        # 2)
        del spd_structure["spd-entry"][content["spd-entry"]["name"]]["ipsec-policy-config"]["processing-info"][
            "ipsec-sa-cfg"]["esp-algorithms"]
        # 3)
        spd_structure["spd-entry"][content["spd-entry"]["name"]]["ipsec-policy-config"]["processing-info"][
            "ipsec-sa-cfg"] \
            ["esp-algorithms"] = esp_algo_adapted
        self._log.debug(f"[FINAL SPD ALGO STRUCTURE: \n{json.dumps(spd_structure, indent=4)}]")
        
        # After the SDP structure is compliant with the 9061 RFC, we communicate with NETCONF to set the policies flows.
        self._communicate_with_netconf({"spd": spd_structure})

    def sad_and_spd_management(self, content):
        self.sad_management(content)
        self.spd_management(content)

    def _process_request(self, content:dict):
        # SAD entry is processed
        if "sad-entry" in content.keys():
            self._log.debug(f"SAD CONTENT RECEIVED: \n{content}")
            thread = threading.Thread(target=self.sad_management, args=(content,))
            thread.start()
        
        # SPD entry is processed
        elif "spd-entry" in content.keys():
            self._log.debug(f"SPD CONTENT RECEIVED: \n{content}")
            self.spd_management(content)
        else:
            # NO content to process, ERROR sent.
            self._log.error(f"[WRONG CONTENT: \n{content}]")
            return "ERROR"
        return "OK"

    def return_id_of_the_node(self, ip) -> str:
        """
        :param ip: Parameter used to extract the id of the node from the public node information.
        :return:
        """
        return self.public_nodes_info[ip]["id"]

    def set_key_in_template(self, content: dict, spis_and_final_keys: dict) -> dict:
        """
        :param content: This is the packet sent from the CCIPS Controller. We will write into this configuration
                        the key extracted from the hybrid module.
        :param spis_and_final_keys: The SPIs with the new key extracted from the Hybrid Module.
        
        :return: A new RFC 9061 Template with the keys installed.
        """
       
        new_content: dict = content.copy()
        for _, v in new_content['ipsec-ikeless']['sad']['sad-entry'].items():
            v['ipsec-sa-config']['esp-sa']['encryption']['key'] = \
                spis_and_final_keys[v['ipsec-sa-config']['spi']]
            v['ipsec-sa-config']['esp-sa']['encryption']['iv'] = \
                spis_and_final_keys[v['ipsec-sa-config']['spi']]
            v['ipsec-sa-config']['esp-sa']['integrity']['key'] = \
                spis_and_final_keys[v['ipsec-sa-config']['spi']]
        return new_content

    def request_key(self, key_request: dict):
        def hybrid_app_v(key_request):
            # Hybrid_module Test
            h_ke: Key_Extractor = Key_Extractor(self._log, 
                                                self._config["hybrid_module"]["address"][0],
                                                self._config["hybrid_module"]["address"][1],
                                                key_request, 1200)
            key = h_ke.get_hybrid_key()
            self._log.info(f"[KEY FROM HYBRID MODULE: \n{key}]")
            return key
        
        self._log.info(f"[REQUESTING KEY FOR: \n{key_request}]")
        
        # HYBRID REQUESTER: 
        key = hybrid_app_v(key_request)
        return key

    def _extract_spis_and_tunneling_info_from_model(self, template_9061: dict):
        """
        :param template_9061: It is a json formatted message containing information of the 9061 model.
                              It will extract the information of the SPIs and the Nodes implies in the SA in order to
                              build a Key Request to the Hybrid Module.
        :return dictionary spi_tunnels: A dictionary structure is returned with the SPI identifier and the tunnel relevant parameters.
        """
        spi_and_tunnels: dict = {}
        for k, v in template_9061['ipsec-ikeless']['sad']['sad-entry'].items():
            spi_and_tunnels[v['ipsec-sa-config']['spi']] = v['ipsec-sa-config']['traffic-selector']
            self._log.info(f"[SAs with SPI {v['ipsec-sa-config']['spi']} STORED]")
        return spi_and_tunnels

    def _generate_hybrid_key_request(self, spis_and_tunnels) -> dict:
        """
        This process will generate the key request for the Hybrid Module according to the SPIs and the IDs of the
        nodes in the configuration file.
        An ETSI GS QKD 004 key request format is prepared ofr connecting with the Hybridization Module.
        """
        key_requests: dict = {}
        for k, v in spis_and_tunnels.items():
            key_requests[k] = {
                "command": "OPEN_CONNECT",
                "data": {
                    "source": f"qkd://SPI_{k}@{self.return_id_of_the_node(v['local-prefix'])}?hybridization=xoring&kem_mec=Kyber512",
                    "destination": f"qkd://SPI_{k}@{self.return_id_of_the_node(v['remote-prefix'])}?hybridization=xoring&kem_mec=Kyber512",
                    "qos": {
                        "key_chunk_size": 20,
                        "max_bps": 32,
                        "min_bps": 32,
                        "jitter": 0,
                        "priority": 0,
                        "timeout": 0,
                        "ttl": 0,
                        "metadata_mimetype": "application/json"
                    }
                }
            }
        return key_requests

    def _communicate_with_netconf(self, final_content: dict) -> str:
        top_ikeless_class: str = "yc_ipsec_ikeless_ietf_i2nsf_ikeless__ipsec_ikeless"
        status: str = "OK"
        header: str = """<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">\n"""
        footer: str = "</config>"
        try:
            self._log.info("[CONNECTING TO CCIPS AGENT]")
            pyObject =  pbJ.loads(json.dumps(final_content), ikelessClass, top_ikeless_class)
            xml_content: str  = f"{header}" + f"{XMLEncoder.serialise(pyObject)}" + f"{footer}"
            self._netconf_connector.edit_config(target='running', config=xml_content,
                                                test_option='test-then-set')
        except Exception as e:
            self._log.error(f"[ERROR: \n\t{e}]")
            status = "ERROR"
        return status
    
    def _adapt_key(self, key):
        def build_octet_key_format(l_key):
            key_formatted: str = ""
            for i in range(0, len(l_key), 2):
                key_formatted += l_key[i:i + 2] + ":"
            # This procedure introduce a ":" at the end, we return the key without that.
            return key_formatted[:-1]
        hex_key = ''.join('{:02x}'.format(x) for x in key)
        self._log.debug(f"[HEX KEY: {hex_key}]")
        key_to_deliver: str = build_octet_key_format(hex_key)
        return key_to_deliver[:120]


def main(cfg_file_path: str):
    _ : ProxyAgent = ProxyAgent(cfg_file_path)

if __name__ == '__main__':
    # CFG File for the Proxy Agent.
    main(sys.argv[1])
