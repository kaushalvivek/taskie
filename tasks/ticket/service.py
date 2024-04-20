'''
This module exposes the Ticketer service, capable of creating tickets in Linear, as a project manager.
'''
import sys
import os
from rich import print as rprint
sys.path.append(os.environ['PROJECT_PATH'])
from tools.linear import LinearClient
from tools.slack import SlackClient
from tools.decider import Decider
from models.slack import Message
from .config import CHANNELS
class Ticketer:
    def __init__(self):
        self.linear = LinearClient()
        self.decider = Decider(model="gpt-4-turbo")
        self.slack = SlackClient()
    
    def is_relevant(self, event: Message) -> bool:
        return event.channel_id in CHANNELS.keys()
    
    def trigger_ticket_creation(self, event: Message):
        if not self._is_ticket_worthy(event):
            return
        
    def _is_ticket_worthy(self, event: Message) -> bool:
        channel = self.slack.get_channel_by_id(event.channel_id)
        decision_input = {
            "message": event.text,
            "channel_name": channel["name"],
        }
        decision, follow_up = self.decider.can_proceed(
            context = f'''- Someone has posted a Slack message on a channel: {channel['name']}.
- We're evaluating whether the message requires further action, through the creation of a Linear ticket or not.
- A Linear ticket if required if the message flags an issue, suggestion, or improvement which requires some action to be taken.
- The message might often not have enough context to be directly actionable, but that's okay, what matters is the intent behind the message.
''',
            action = "Create a Linear ticket from the message, for either the engineering team, or the design team to look in to.",
            input = str(decision_input),
            criteria = [
                "The message expresses a problem, a suggestion, or an improvement with the intent of getting it resolved",
                "The message REQUIRES further action, and isn't an FYI on an action already taken",
                "The message is not a general announcement or a social message",
            ]
        )        
        print(decision,follow_up)
        return decision

    def clarify(self, project_id: str, title: str, description: str) -> bool:
        pass

    def create_ticket(self, project_id: str, title: str, description: str):
        pass