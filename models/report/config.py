from pydantic import BaseModel

class EmailConfig(BaseModel):
    domains: list[str]
    suffixes: list[str]

class Config(BaseModel):
    admin_user_email: str = None
    reporting_channel_id: str
    roadmap_view_url: str
    email: EmailConfig
