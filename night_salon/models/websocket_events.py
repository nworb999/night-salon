from pydantic import BaseModel
from typing import Literal, Dict, Any, Union

class WebsocketConnect(BaseModel):
    status: Literal["granted"]
    client_id: str

class ClientWebsocketConnectEvent(BaseModel):
    event: Literal["connect"]
    data: Dict[str, Any]

class WebsocketData(BaseModel):
    data: Union[WebsocketConnect, ClientWebsocketConnectEvent]

class ClientWebsocketEvent(BaseModel):
    event: str
    client_id: str
    data: dict 