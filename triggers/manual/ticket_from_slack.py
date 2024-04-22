'''
This script accepts a message permalink from Slack as argument, and initiates ticket creation.
'''
import sys
import os
import logging
sys.path.append(os.environ['PROJECT_PATH'])
from tools.slack import SlackClient
from models.slack import Message
from tasks.ticket import Ticketer

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python3 ticket_from_slack.py <message_permalink>")
        sys.exit(1)
    message_permalink = sys.argv[1]
    slack = SlackClient(logger)
    message = slack.get_message_from_permalink(message_permalink)
    ticketer = Ticketer(logger)
    if ticketer.is_relevant(message):
        ticketer.trigger_ticket_creation(message)
    