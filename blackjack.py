"""
Blackjack game with AI agents - uses AutoGen for the multi-agent setup
"""

import os
import random
import asyncio
from typing import Annotated, Sequence
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient


# loading env variables
load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Set OPENAI_API_KEY in .env file")

# setup the model client
llm = OpenAIChatCompletionClient(model="gpt-4o-mini", api_key=api_key, model_info={"vision": True, "function_calling": True, "json_output": True, "family": "gpt-4o-mini", "structured_output": True,}, temperature=0.7, max_tokens=1000)