import os
import sys
import logging
import redis
from ratelimit import limits, sleep_and_retry
sys.path.append(os.environ['PROJECT_PATH'])
from models.slack import Message
from models.report import EmailConfig
from slack_sdk import WebClient

class SlackClient:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
        self.cache = redis.Redis()
    
    def post_message(self, channel_id: str, message=None, blocks=None):
        if message:
            self.client.chat_postMessage(channel=channel_id, text=message)
        elif blocks:
            self.client.chat_postMessage(channel=channel_id, blocks=blocks, mrkdwn=True, link_names=True)
        
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

    def get_tag_for_user(self, email: str, email_config: EmailConfig) -> str:
        user_name = email.split('@')[0]
        options = []

        for domain in email_config.domains:
            options.append(f"{user_name}@{domain}")

        for suffix in email_config.suffixes:
            if user_name.endswith(suffix):
                stripped_user_name = user_name[:-len(suffix)]
                for domain in email_config.domains:
                    options.append(f"{stripped_user_name}@{domain}")
        
        for option in options:
            try:
                response = self.client.users_lookupByEmail(email=option)
                if response["ok"] and response["user"] is not None:
                    return f"<@{response['user']['id']}>"
            except Exception as e:
                continue
        
        return user_name
