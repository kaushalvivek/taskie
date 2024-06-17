import sys
import os
from pydantic import BaseModel
from pydantic.fields import Field
from enum import Enum
from typing import Optional
sys.path.append(os.environ['PROJECT_PATH'])
from models.linear import Project, User

class ReminderType(Enum):
    UPDATE = "update"
    PLANNING = "planning"

class Reminder(BaseModel):
    user: User
    projects: list[Project]

class RiskUpdate(BaseModel):
    project_name: str = Field(None, description="Name of the project")
    project_milestone: str = Field(None, description="The milestone that is at risk")
    why: str = Field(None, description="A VERY BRIEF reason for why the project is at risk")
    what_next: str = Field(None, description="A VERY BRIEF summary of what the project lead has shared as the next steps")

class Report(BaseModel):
    best_update: Project = None
    risks : list[RiskUpdate] = None
    reminders: list[Reminder] = None
    projects_with_updates: list[Project] = None
    projects_without_updates: list[Project] = None
