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

class ProjectMilestone(BaseModel):
    id: str
    name: str
    description: Optional[str]
    target_date: Optional[str] = Field(..., alias="targetDate")
    created_at: str = Field(..., alias="createdAt")

class ProjectMilestonesNode(BaseModel):
    nodes: list[ProjectMilestone]

class ProjectUpdate(BaseModel):
    id: str
    created_at: str = Field(..., alias="createdAt")
    body: str
    url: str
    user: User
    diff: Optional[str] = Field(..., alias="diffMarkdown")

class ProjectUpdatesNode(BaseModel):
    nodes: list[ProjectUpdate]

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str]
    target_date: Optional[str] = Field(None, alias="targetDate")
    state: ProjectState
    project_updates: Optional[ProjectUpdatesNode]= Field(None, alias="projectUpdates")
    progress: Optional[float] = None
    url: Optional[str] = None
    lead: Optional[User] = None
    milestones: Optional[ProjectMilestonesNode] = Field(None, alias="projectMilestones")