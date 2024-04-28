'''
Decider is an intelligent servie. It exposes methods to help make the best choice.
'''
import openai
import json
import logging
class Decider:
    def __init__(self, model="gpt-3.5-turbo", logger=logging.getLogger(__name__)):
        self.model = model
        self.logger = logger
        pass

    # This method should return the best option provided the decision criteria and the options
    def get_best_option(self, context: str, options: list[str], criteria: list[str]):
        formatted_options = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
        formatted_criteria = "\n".join([f"{i+1}. {criterion}" for i, criterion in enumerate(criteria)])
        system_instruction = f'''
# Mission
You are an expert at deciding the best option for any situation. Your mission is to return the best option out of a \
given set of options by carefully considering the decision criteria.

# Context
{context}

# Decision Criteria (sorted by importance)
{formatted_criteria}

# Instructions
1. Think carefully from first principles and provide the best option based on the context and the decision criteria.
2. You MUST respond in the given output format.
3. Your response MUST be a valid JSON.

# Format

## Input
Options:
1. Option 1
2. Option 2
... (as many as the number of options)

## Output
{{
    "chain_of_thought": (the chain of thought that led to the decision),
    "best_option": (index of the best option)
}}
'''
        response = openai.chat.completions.create(
            model = self.model,
            messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Options:\n{formatted_options}"}
            ],
            temperature=0
        )
        response_json = json.loads(response.choices[0].message.content)
        self.logger.debug(f"Response: {response_json}")
        return response_json["best_option"]-1

    # This method should return whether to proceed with an action or not, along with follow-ups if any
    def can_proceed(self, context: str, action: str, input: str, criteria: list[str], examples: list[str] = []):
        formatted_criteria = "\n".join([f"{i+1}. {criterion}" for i, criterion in enumerate(criteria)])
        formatted_examples = "\n".join([f"{i+1}. {example}" for i, example in enumerate(examples)])
        system_instruction = f'''
# Mission
You are an expert at deciding whether to proceed with an action or not. Your mission is to determine whether to proceed \
with the given action by carefully considering the provided context, and the decision criteria.

# Context
{context}

# Action
{action}

# Decision Criteria (sorted by importance)
{formatted_criteria}

# Instructions
1. Think carefully from first principles and decide whether to proceed with the given action or not.
2. If you feel that the provided context is insufficient, ask for more information. ONLY DO THIS IF NECESSARY.
3. You MUST respond in the given output format.
4. Your response MUST be a valid JSON.

# Format

## Input
(information provided by the user to make the decision on)

## Output
{{
    "chain_of_thought": (the chain of thought that led to the decision),
    "can_proceed": true/false (whether to proceed with the action or not),
    "follow_ups": (any a follow-up question if necessary) -- OPTIONAL, ONLY IF can_proceed is false and more information is needed
}}
'''
        if examples:
            system_instruction += f'''\n\n# Examples
{formatted_examples}
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
        response_json = json.loads(response.choices[0].message.content)
        return response_json["can_proceed"], response_json.get("follow_ups", None)