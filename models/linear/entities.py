from pydantic import BaseModel
from pydantic.fields import Field
from typing import Optional
from enum import Enum

class ProjectState(str, Enum):
    PLANNED = "planned"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELED = "canceled"
    BACKLOG = "backlog"

class User(BaseModel):
    id: str
    name: str
    email: str

class ProjectUpdate(BaseModel):
    id: str
    created_at: str = Field(..., alias="createdAt")
    body: str
    url: str
    user: User

class ProjectUpdatesNode(BaseModel):
    nodes: list[ProjectUpdate]

class Project(BaseModel):
    id: str
    name: str
    description: str
    target_date: Optional[str] = Field(..., alias="targetDate")
    state: ProjectState
    project_updates: Optional[ProjectUpdatesNode]= Field(..., alias="projectUpdates")
