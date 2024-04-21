import os
import sys
sys.path.append(os.environ['PROJECT_PATH'])
from models.slack import Message
from slack_sdk import WebClient

class SlackClient:
    def __init__(self):
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