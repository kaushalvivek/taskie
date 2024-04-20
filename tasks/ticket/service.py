'''
This module exposes the Ticketer service, capable of creating tickets in Linear, as a project manager.
'''
import sys
import os
sys.path.append(os.environ['PROJECT_PATH'])
from tools.linear import LinearClient

class Ticketer:
    def __init__(self):
        self.linear = LinearClient()
    
    def should_create_ticket(self, project_id: str, title: str, description: str) -> bool:
        pass

    def clarity(self, project_id: str, title: str, description: str) -> bool:
        pass

    def create_ticket(self, project_id: str, title: str, description: str):
        pass