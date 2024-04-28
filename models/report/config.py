from pydantic import BaseModel


class Config(BaseModel):
    roadmap_id: str
    admin_user_email: str = None
    reporting_channel_id: str
    roadmap_view_url: str
    domains: list[str]
