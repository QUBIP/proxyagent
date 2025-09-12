

import copy
import json
import logging
import re

log = logging.getLogger(__name__)

def extract_entries(input_string: str) -> list[dict]:
    """
    Extracts and parses multiple JSON objects from a given string.

    Args:
        input_string (str): A string containing multiple JSON objects.

    Returns:
        list: A list of dictionaries representing the parsed JSON objects.
    """
    log.debug("[EXTRACTING ENTRIES]")
    try:
        entries = []
        stack = 0
        json_objects = []
        current_object = ""

        # Scan the input string character by character
        for char in input_string:
            if char == "{":
                stack += 1
            if char == "}":
                if stack > 0:
                    stack -= 1

            # Append characters to current JSON object
            current_object += char

            # If stack is empty, we have a complete JSON object
            if stack == 0 and current_object.strip():
                json_objects.append(current_object.strip())
                current_object = ""

        # Parse each detected JSON object
        for obj in json_objects:
            try:
                parsed_json = json.loads(obj)
                if "spd-entry" in parsed_json or "sad-entry" in parsed_json:
                    entries.append(parsed_json)
            except json.JSONDecodeError as e:
                log.error(f"Skipping invalid JSON object due to error: {e}")
        return entries

    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def adapt_spd_algo_structure(received_spd_entry: dict) -> dict:
    """ A transformation is necessary from the structure in the esp-algorithm container that we received 
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

    Args:
        spd_entry (dict): A dictionary conatining a spd-entry received from the CCIPS controller.

    Returns:
        dict: A new dictionary with the correct structure.
    """
    log.info("[ADAPTING SPD ENTRY ESP ALGORITHM STRUCTURE]")

    new_spd_entry = copy.deepcopy(received_spd_entry)
    new_entry_sa_config = new_spd_entry["spd-entry"]["ipsec-policy-config"]["processing-info"]["ipsec-sa-cfg"] 
    
    log.info("[INITIAL SPD ipsec-sa-config: %s]", new_entry_sa_config)
    esp_algo_adapted: dict = {
        "integrity": [new_entry_sa_config["esp-algorithms"]["integrity"]],
        "encryption": {
            new_entry_sa_config["esp-algorithms"]["encryption"]["id"]: new_entry_sa_config["esp-algorithms"]["encryption"]
        }
    }
    new_entry_sa_config["esp-algorithms"] = esp_algo_adapted

    log.info("[ADAPTED SPD ipsec-sa-config: %s]", new_entry_sa_config)
    return new_spd_entry

def _hex_string_to_octect_string(hex_string: str) -> str:
    """ Transforms a hex string into octect format
    
    Args:
        hex_string (str): String in hex format (0x0123456789abdef)

    Returns:
        str: String in octect format (01:23:45:67:89:....)
    """

    hex_pairs: list[str] = re.findall(r".{1,2}", hex_string)

    # This procedure introduce a ":" at the end, we return the key without that.
    return ":".join(hex_pairs)

def byte_list_to_octect_string(received_list: list) -> str:
    """ Transforms an array of bytes into a string in octect format

    Args:
        received_list (list): A list of bytes ([123, 23, 90, 200]), this was tested with list[int]

    Returns:
        str: A string in octect format (7B:17:5A:C8)
    """

    # HEX KEY: 0x0123456789abdef
    hex_string = ''.join('{:02x}'.format(x) for x in received_list)
    log.debug("[HEX STRING: %s]", hex_string)

    # OCTET FORMAT KEY: 01:23:45:67:89:....
    return _hex_string_to_octect_string(hex_string)
