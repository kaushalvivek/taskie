import os
import sys
import slack_bolt
from rich import print as rprint

sys.path.append(os.environ['PROJECT_PATH'])
from tasks.ticket import Ticketer
from models.slack import Message

app = slack_bolt.App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))

ticketer = Ticketer()

@app.event("message")
def handle_message_events(body):
    event = body["event"]
    rprint(event)
    message = Message(**event)
    if ticketer.is_relevant(message):
        ticketer.trigger_ticket_creation(message)
    return

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
