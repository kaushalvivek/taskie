import sys
import os
from pydantic import BaseModel
from typing import Optional
sys.path.append(os.environ['PROJECT_PATH'])
from models.linear import Project, User

class Reminder(BaseModel):
    user: User
    projects: list[Project]

class BestUpdate(BaseModel):
    project: Project
    chain_of_thought: str = None

class Report(BaseModel):
    summary: str = None
    reminders: list[Reminder] = None
    best_update: BestUpdate = None
