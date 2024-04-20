'''
This module exposes the Ticketer service, capable of creating tickets in Linear, as a project manager.
'''
import sys
import os
sys.path.append(os.environ['PROJECT_PATH'])
from tools.linear import LinearClient
from tools.decider import Decider
from models.slack import Message
from .config import CHANNELS
class Ticketer:
    def __init__(self):
        self.linear = LinearClient()
        self.decider = Decider()
    
    def is_relevant(self, event: Message) -> bool:
        return event.channel_id in CHANNELS.keys()
    
    def trigger_ticket_creation(self, event: Message):
        if not self._is_ticket_worthy(event):
            return
        
    
    def _is_ticket_worthy(self, event: Message) -> bool:
        decision = self.decider.get_best_option(
            context="Is this message worthy of creating a ticket?",
            options=["Yes", "No"],
            criteria=["Relevance", "Importance"]
        )        

    def clarity(self, project_id: str, title: str, description: str) -> bool:
        pass

    def create_ticket(self, project_id: str, title: str, description: str):
        pass