import os
import sys
import slack_bolt
from rich import print as rprint
sys.path.append(os.environ['PROJECT_PATH'])
import mapper
from tasks.ticket import Ticketer
from models.slack import Message

app = slack_bolt.App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))

ticketer = Ticketer()

@app.event("message")
def handle_message_events(body):
    rprint(body)
    event_subtype = None
    if "subtype" in body["event"]:
        event_subtype = body["event"]["subtype"]
    if event_subtype and event_subtype in ["bot_message", "message_changed","message_deleted"]:
        return
    event = body["event"]
    message = mapper.get_message_from_event(event)
    if ticketer.is_relevant(message):
        ticketer.trigger_ticket_creation(message)
    return

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))