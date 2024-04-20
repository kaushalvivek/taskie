import os
import sys
from rich import print as rprint
sys.path.append(os.environ['PROJECT_PATH'])
from models.slack import Message

def get_message_from_event(event: dict) -> Message:
    message = Message(**event)
    if "attachments" in event.keys():
        for attachment in event['attachments']:
            message.text += f'\n\nattached message:\n{attachment["text"]}'
    rprint(f"Message: {message}")
    return message