import socket
import json
from threading import Thread

class Key_Extractor(Thread):
    def __init__(self,log, host, port, key_request: dict, key_size: int):
        self._key: list = [1, 2, 3, 4, 5, 6]
        self._key_request = key_request
        self._log = log

        self._host: str = host
        self._port: int = port

        self._config: dict = {
            "open_connect_file": "",
            "key_size": key_size,
        }

        self._responses: dict = {
            "open_connect": {},
            "get_key": {},
            "close": {}
        }

    def get_hybrid_key(self,):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as kdfix_socket:
            # Connect to the server
            kdfix_socket.connect((self._host, self._port))
            self._log.info(f"Hybrid Module connected to KDFix server at {self._host}:{self._port}")

            # Send the OPEN_CONNECT request
            kdfix_socket.sendall(json.dumps(self._key_request).encode("utf8"))

            # Receive the OPEN_CONNECT response
            oc_response = json.loads(kdfix_socket.recv(65057).decode("utf8"))
            self._log.info(f"[OPEN_CONNECT RESPONSE: {oc_response}]")

            self._responses["open_connect"] = oc_response

            # Ensure session is established
            if oc_response.get("status") != 0:
                self._log.info("[FAILED TO OPEN CONNECTION. EXITING...]")
                return "ERROR"

            key_stream_id = oc_response["key_stream_id"]

            gk_request = {
                "command": "GET_KEY",
                "data": {
                    "key_stream_id": key_stream_id,
                    "index": 0,
                    "metadata": {
                        "size": int(self._config["key_size"]),
                        "buffer": "The metadata field is not used for the moment."
                    }
                }
            }
            self._log.info(f"[GET KEY REQUEST: \n{json.dumps(gk_request, indent=4)}]")

            # Send the GET_KEY request
            kdfix_socket.sendall(json.dumps(gk_request).encode("utf8"))

            # Wait to receive the GET_KEY response
            while True:
                gk_response_bytes = kdfix_socket.recv(65057)
                if gk_response_bytes:
                    gk_response = json.loads(gk_response_bytes.decode("utf8"))
                    break

            self._log.info(f"\n[GET_KEY RESPONSE: {gk_response}]")

            self._responses["get_key"] = gk_response

            # We store the key extracted.
            self._key = gk_response["key_buffer"]

            # Create the CLOSE request
            cl_request = {
                "command": "CLOSE",
                "data": {
                    "key_stream_id": key_stream_id
                }
            }

            # Send the CLOSE request
            kdfix_socket.sendall(json.dumps(cl_request).encode("utf8"))

            # Receive the CLOSE response
            cl_response = json.loads(kdfix_socket.recv(65057).decode("utf8"))
            self._log.info(f"[CLOSE response: {cl_response}]")

            self._responses["close"] = cl_response
            return self._key

    def return_key(self):
        return self._key

    def run(self):
        self.get_hybrid_key()
