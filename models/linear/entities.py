from pydantic import BaseModel
from pydantic.fields import Field
from typing import Optional
from enum import Enum

class ProjectStates(str, Enum):
    PLANNED = "planned"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELED = "canceled"
    BACKLOG = "backlog"

class User(BaseModel):
    id: str
    name: str
    email: str

class Team(BaseModel):
    id: str
    name: str

    # Check if team is related to engineering, product or design
    def is_epd(self):
        return self.name in ["Engineering", "Product", "Design"]

class TicketState(BaseModel):
    id: str
    name: str
    team: Team = Field(alias="team", default=None)
    
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

class TeamsNode(BaseModel):
    nodes: list[Team]

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str]
    target_date: Optional[str] = Field(None, alias="targetDate")
    state: ProjectStates
    project_updates: Optional[ProjectUpdatesNode]= Field(None, alias="projectUpdates")
    progress: Optional[float] = None
    url: Optional[str] = None
    lead: Optional[User] = None
    milestones: Optional[ProjectMilestonesNode] = Field(None, alias="projectMilestones")
    teams: Optional[TeamsNode] = None
    
class Ticket(BaseModel):
    id: str = Field(None, alias="id")
    title: str = Field(alias="title", description="A brief, descriptive, title for the ticket")
    description: str = Field(alias="description", description="A detailed description of the issue, suggestion or improvement -- covering all reported details.")
    slack_message_url: str = Field(alias="slack_message_url", description="The URL to the Slack message that triggered the ticket creation")
    team: Team = Field(alias="team", description="The team that will be responsible for the ticket", default=None)
    tags: list[str] = Field(alias="tags", description="A list of tags that help categorize the ticket", default=None)
    state: TicketState = Field(alias="state", description="The status of the ticket", default=None)
    priority: int = Field(alias="priority", description="The priority of the ticket", default=0)
    