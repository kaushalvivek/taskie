'''
This module exposes the Ticketer service, capable of creating tickets in Linear, as a project manager.
'''
import sys
import os
import logging
import json
from rich import print as rprint
sys.path.append(os.environ['PROJECT_PATH'])
from tools.linear import LinearClient
from tools.slack import SlackClient
from tools.decider import Decider
from tools.writer import Writer
from models.slack import Message
from models.linear import Ticket, Teams
from .config import CHANNELS


BASE_CONTEXT = "We are creating a Linear ticket to take further action, \
based on the shared Slack message. You'd be shared the content of the Slack message."
class Ticketer:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.linear = LinearClient()
        self.decider = Decider(model="gpt-4-turbo", logger=logger)
        self.writer = Writer(logger=logger)
        self.slack = SlackClient()
        self.logger = logger
    
    def is_relevant(self, event: Message) -> bool:
        return event.channel_id in CHANNELS.keys()
    
    def trigger_ticket_creation(self, event: Message):
        if not self._is_ticket_worthy(event):
            return
        ticket = self._parse_ticket(event)
        # self.linear.create_ticket(ticket)
        
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
        self.logger.debug(f"Decision: {decision}, Follow-up: {follow_up}")  
        if not decision and follow_up:
            self._ask_follow_up(self, event, follow_up)
        return decision

    def _parse_ticket(self, event: Message) -> Ticket:
        ticket = Ticket(
            title = self.writer.summarize(context= f"{BASE_CONTEXT} You must come up with a great title.", word_limit=10, input=event.text),
            description = event.text,
            slack_message_url = f"https://slack.com/archives/{event.channel_id}/p{event.timestamp}",
            team = self._get_team(event),
        )
        self.logger.debug(f"Ticket: {ticket.model_dump()}")
        self.slack.reply_in_thread(event.channel_id, f"ticket: {json.dumps(ticket.model_dump(), indent=4)}", event.timestamp)
        return ticket

    def _get_team(self, event: Message) -> Teams:
        team = self.decider.get_best_option(context= f"{BASE_CONTEXT} You must decide the best team pick the ticket up, and execute on it. Slack message: {event.text}", 
                                                options=Teams.__members__.keys(), criteria=["The team must be the best equipped to act on the next steps for the ticket"])
        print(f"Team: {team}")
        return Teams.ENGINEERING
    
    def _ask_follow_up(self, event: Message, follow_up: str) -> bool:
        self.slack.reply_in_thread(event.channel_id, follow_up, event.timestamp)
