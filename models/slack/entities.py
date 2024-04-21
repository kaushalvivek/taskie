from pydantic import BaseModel
from pydantic.fields import Field

class Message(BaseModel):
    id: str = Field(alias="client_msg_id", default=None)
    text: str = Field(alias="text")
    user_id: str = Field(alias="user")
    channel_id: str = Field(alias="channel", default=None)
    timestamp: float = Field(alias="ts")
    is_reply: bool = Field(alias="is_thread_reply", default=False)
    
    def get_message_from_event(event: dict):
        message = Message(**event)
        if "thread_ts" in event.keys():
            message.is_reply = True
        if "attachments" in event.keys():
            for attachment in event['attachments']:
                message.text += f'\n\nattached message:\n{attachment["text"]}'
        return message

    