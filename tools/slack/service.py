import os
import sys
import logging
from rich import print as rprint
sys.path.append(os.environ['PROJECT_PATH'])
from models.slack import Message
from slack_sdk import WebClient

class SlackClient:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    
    def post_message(self, channel_id: str, message: str):
        self.client.chat_postMessage(channel=channel_id, text=message)
        
    def reply_in_thread(self, channel_id: str, message: str, thread_ts: float):
        print(f"Replying in thread {thread_ts}")
        self.client.chat_postMessage(channel=channel_id, text=message, thread_ts=str(thread_ts))
    
    def get_channel_by_id(self, channel_id: str):
        response = self.client.conversations_info(channel=channel_id)
        if response["ok"]:
            return response["channel"]

    def get_permalink_for_message(self, message: Message) -> str:
        response = self.client.chat_getPermalink(channel=message.channel_id, message_ts=message.timestamp)
        if response["ok"]:
            return response["permalink"]
        return None
    
    def get_message_from_permalink(self, permalink: str) -> Message:
        self.logger.info(f"Fetching message from permalink: {permalink}")
        channel_id, message_ts_str = permalink.split("/")[-2:]
        message_ts_str = message_ts_str[1:]
        message_ts_seconds = message_ts_str[:10]
        message_ts_fraction = message_ts_str[10:]
        message_ts = float(f"{message_ts_seconds}.{message_ts_fraction}")
        response = self.client.conversations_history(channel=channel_id, latest=str(message_ts), inclusive=True, limit=1)
        if response["ok"]:
            self.logger.info(f"Message fetched successfully")
            message = response["messages"][0]
            message= Message.get_message_from_event(message)
            message.channel_id = channel_id # set channel_id as it is not present in the response
        return message