'''
Writer is an intelligent service, capable of generating, and re-writing content for various purposes.
'''
import openai
import json
import logging

class Writer:
    def __init__(self, model="gpt-3.5-turbo", logger=logging.getLogger(__name__)):
        self.model = model
        self.logger = logger

    def summarize(self, context: str, word_limit: int, input: str) -> str:
        system_instruction = f'''
# Mission
You are the most efficient, eloquent, and articulate communicator in the world. Your mission is to summarize the input shared \
with you into a concise, coherent, and comprehensive output within the given word limit while retaining the essence of the input.

# Context
{context}

# Instructions
1. Summarize the input into a coherent and concise output.
2. You MUST adhere to a word limit of {word_limit}. UNDER NO CIRCUMSTANCES should your output EVER exceed this limit.
3. Retain the essence of the input, and as much information as possible within the word limit.
'''
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": input}]
        self.logger.debug(f"Messages: {messages}")
        response = openai.chat.completions.create(
            model = self.model,
            messages = messages,
            temperature=0
        )
        self.logger.debug(f"Response: {response}")
        return response.choices[0].message.content