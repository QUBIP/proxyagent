
from pydantic import BaseModel

# OPEN CONNECT

class  OpenConnectQos(BaseModel):
    key_chunk_size: int
    max_bps: int
    min_bps: int
    jitter: int
    priority: int
    timeout: int
    ttl: int
    metadata_mimetype: str

class OpenConnectMessage(BaseModel):
    source: str
    destination: str
    qos: OpenConnectQos

# GET KEY

class GetKeyMetadata(BaseModel):
    size: int = 46 # Size of the metadata buffer
    buffer: str = "The metadata field is not used for the moment."

class GetKeyMessage(BaseModel):
    key_stream_id: str
    index: int
    metadata: GetKeyMetadata

# CLOSE

class CloseMessage(BaseModel):
    key_stream_id: str