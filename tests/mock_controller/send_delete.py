
import requests

host = "localhost"
port = 3000

url = f"http://{host}:{port}/register"

delete_sad = {
    "sad-entry" : {
        "name" : "Patata",
        "reqid" : 1233
    }
}


response = requests.delete(url=url, json=delete_sad)

print(response)