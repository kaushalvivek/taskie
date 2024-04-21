from pydantic import BaseModel

class ChannelConfig(BaseModel):
    channel_id: str
    mandatory_label_ids: list[str]

class TicketerConfig(BaseModel):
    slack_admin_user_id: str
    slack_channel_configs: list[ChannelConfig]