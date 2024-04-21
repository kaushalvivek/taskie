'''
This module exposes the Ticketer service, capable of creating tickets in Linear, as a project manager.
'''
import sys
import os
import logging
import json
import uuid
sys.path.append(os.environ['PROJECT_PATH'])
from tools.linear import LinearClient
from tools.slack import SlackClient
from tools.decider import Decider
from tools.writer import Writer
from models.slack import Message
from models.linear import Ticket, Team, TicketState
from .config import CHANNELS, SLACK_ADMIN_USER_ID


BASE_CONTEXT = "We are creating a Linear ticket to take further action, \
based on the shared Slack message. You'd be shared the content of the Slack message."
class Ticketer:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.linear = LinearClient(logger)
        self.decider = Decider(model="gpt-4-turbo", logger=logger)
        self.writer = Writer(logger=logger)
        self.slack = SlackClient()
        self.logger = logger
    
    def is_relevant(self, event: Message) -> bool:
        return event.channel_id in CHANNELS
    
    def trigger_ticket_creation(self, event: Message):
        if event.is_reply:
            # TODO: check if parent message has a ticket associated with it
            # if no, then consider this ticket for ticket creation
            return
        if not self._is_ticket_worthy(event):
            return
        ticket = self._parse_ticket(event)
        self.linear.create_ticket(ticket)
        self.linear.attach_slack_message_to_ticket(ticket)
        ticket.url = self.linear.get_ticket_by_id(ticket).url
        self.slack.reply_in_thread(event.channel_id, f"Ticket created: {ticket.url}\n\ncc <@{SLACK_ADMIN_USER_ID}>", event.timestamp)
        
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
            self._ask_follow_up(event, follow_up)
        return decision

    def _parse_ticket(self, event: Message) -> Ticket:
        self.logger.debug(f"Event: {event.model_dump_json()}")
        ticket = Ticket(
            id= str(uuid.uuid4()),
            title = self.writer.summarize(context= f"{BASE_CONTEXT} You must come up with a great title. DO NOT use the word title.", word_limit=10, input=event.text),
            description = event.text,
            slack_message_url = self.slack.get_permalink_for_message(event),
            team = self._get_team(event),
        )
        ticket.state = self._get_ticket_state(event, ticket.team)
        self.logger.debug(f"Ticket: {ticket.model_dump()}")
        return ticket

    def _get_team(self, event: Message) -> Team:
        teams = self.linear.list_teams()
        team_names = [team.name for team in teams]
        team_idx = self.decider.get_best_option(context= f"{BASE_CONTEXT} You must decide the best team pick the ticket up, and execute on it. Slack message: {event.text}", 
                                                options=team_names, criteria=["The team must be the best equipped to act on the next steps for the ticket"])
        return teams[team_idx]

    def _get_ticket_state(self, event: Message, team: Team) -> TicketState:
        team_states = self.linear.list_states_for_team(team)
        state_names = [state.name for state in team_states]
        state_idx = self.decider.get_best_option(context= f"{BASE_CONTEXT} You must choose the TODO state, so that the team can act on the ticket. Slack message: {event.text}", 
                                                options=state_names, criteria=["Figure out the TODO state from the available states."])
        return team_states[state_idx]

    def _ask_follow_up(self, event: Message, follow_up: str) -> bool:
        tagged_follow_up = f"{follow_up}\n\ncc: <@{SLACK_ADMIN_USER_ID}>\n\nPS: I can't create tickets from replies today, I'll be smarter soon!"
        self.slack.reply_in_thread(event.channel_id, tagged_follow_up, event.timestamp)
