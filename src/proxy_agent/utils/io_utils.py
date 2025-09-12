
import json
import logging
import socket

from pydantic import BaseModel

log = logging.getLogger(__name__)

def send_socket_request(sock: socket.socket, command_name: str, data: BaseModel) -> dict:

    request = {
        "command" : command_name,
        "data" : data.model_dump()
    }

    log.info(f"[{command_name} REQUEST: \n{json.dumps(request, indent=4)}]")
    sock.sendall(json.dumps(request).encode())

    response = json.loads(sock.recv(65057).decode("utf8"))
    log.info(f"[{command_name} RESPONSE: {response}]")

    return response

def load_json_file(file_path: str) -> dict:
    """Load the contents of a JSON file."""
    with open(file_path, "r") as file:
        return json.load(file)