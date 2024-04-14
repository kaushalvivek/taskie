import sys
import os
from pydantic import BaseModel
from typing import Optional
sys.path.append(os.environ['PROJECT_PATH'])
from models.linear import Project, User

class Reminder(BaseModel):
    user: User
    projects: list[Project]

class Report(BaseModel):
    reminders: Optional[list[Reminder]]
    best_updated_project: Optional[Project]
    exec_summary: Optional[str]