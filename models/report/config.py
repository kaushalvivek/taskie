from pydantic import BaseModel


class Config(BaseModel):
    roadmap_id: str
    admin_user_email: str = None
