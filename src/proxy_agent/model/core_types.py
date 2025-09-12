
from pydantic import BaseModel


class NetworkAddress(BaseModel):
    host: str
    port: int

    def __str__(self) -> str:
        return f"{self.host}:{self.port}"

class UserCredentials(BaseModel):
    username: str
    password: str