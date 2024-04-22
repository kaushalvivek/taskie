from pydantic import BaseModel
from pydantic.fields import Field

class ChannelConfig(BaseModel):
    channel_id: str
    mandatory_label_ids: list[str] = Field(alias="mandatory_label_ids", default=None)

class TicketerConfig(BaseModel):
    slack_admin_user_id: str
    slack_channel_configs: list[ChannelConfig]