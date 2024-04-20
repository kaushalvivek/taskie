from pydantic import BaseModel
from pydantic.fields import Field

class Message(BaseModel):
    id: str = Field(alias="client_msg_id", default=None)
    text: str = Field(alias="text")
    user_id: str = Field(alias="user")
    channel_id: str = Field(alias="channel")
    timestamp: float = Field(alias="ts")
    is_reply: bool = Field(alias="is_thread_reply", default=False)
    