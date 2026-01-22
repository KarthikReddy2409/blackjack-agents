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


class BlackjackGame:
    """keeps track of the game state like :hands, who's done, whose turn etc"""
    
    def __init__(self):
        self.players = ["Karthik", "Alice", "Bob", "Charlie"]
        self.hands = {p: [] for p in self.players}
        self.done = {p: False for p in self.players}
        # I used my name here, you can change it to your name
        self.current = "Karthik"
        self.waiting_for_dealer = False
    
    def get_current_player(self):
        return self.current
    
    def next_turn(self):
        order = ["Karthik", "Alice", "Bob", "Charlie"]
        try:
            idx = order.index(self.current)
        except ValueError:
            idx = 0
        
        for i in range(1, 5):
            next_idx = (idx + i) % 4
            if not self.done[order[next_idx]]:
                self.current = order[next_idx]
                return
        self.current = None  
    
    def draw(self, player):
        if player not in self.hands:
            return f"Error: '{player}' not in game"
        if self.done[player]:
            return f"{player} already finished"
        
        card = random.randint(2, 11)
        self.hands[player].append(card)
        total = sum(self.hands[player])
        
        msg = ""
        if total > 21:
            msg = " BUSTED!"
            self.done[player] = True
            self.next_turn()
        elif len(self.hands[player]) >= 3:
            msg = " (Max 3 cards reached)."
            self.done[player] = True
            self.next_turn()
        
        self.waiting_for_dealer = False
        return f"RESULT: {player} drew {card}. Hand: {self.hands[player]} (Total: {total}).{msg}"
    
    def stand(self, player):
        if player not in self.hands:
            return f"Error: '{player}' not in game"
        self.done[player] = True
        total = sum(self.hands[player])
        self.next_turn()
        self.waiting_for_dealer = False
        return f"RESULT: {player} stands with total {total}."
    
    def player_status(self, player):
        if player not in self.hands:
            return f"Error: '{player}' not found"
        total = sum(self.hands[player])
        return f"{player}'s hand: {self.hands[player]} (Total: {total}) - {'DONE' if self.done[player] else 'ACTIVE'}"
    
    def table_status(self):
        lines = ["--- Table ---"]
        for p in self.players:
            t = sum(self.hands[p])
            s = "DONE" if self.done[p] else "ACTIVE"
            lines.append(f"{p}: {self.hands[p]} ({t}) - {s}")
        lines.append(f"Turn: {self.current or 'Game Over'}")
        return "\n".join(lines)
    
    def is_finished(self):
        return all(self.done.values())
    
    def get_winner(self):
        lines = ["\n" + "="*40, "   FINAL RESULTS", "="*40]
        best = -1
        winners = []
        
        for p in self.players:
            t = sum(self.hands[p])
            bust = " (BUST)" if t > 21 else ""
            lines.append(f"  {p}: {self.hands[p]} = {t}{bust}")
            if t <= 21 and t > best:
                best = t
                winners = [p]
            elif t <= 21 and t == best:
                winners.append(p)
        
        lines.append("="*40)
        if len(winners) == 0:
            lines.append("Everyone busted! No winner")
        elif len(winners) == 1:
            lines.append(f"WINNER: {winners[0]} with {best}!")
        else:
            lines.append(f"TIE: {', '.join(winners)} with {best}")
        
        lines.append("\nTERMINATE")
        return "\n".join(lines)


game = BlackjackGame()


# functions that the dealer can call
def request_card(player: Annotated[str, "player name"]) -> str:
    """draw a card for the player"""
    return game.draw(player)

def request_stand(player: Annotated[str, "player name"]) -> str:
    """player stands with current hand"""
    return game.stand(player)

def check_hand(player: Annotated[str, "player name"]) -> str:
    """check a players hand"""
    return game.player_status(player)

def check_table() -> str:
    """see everyone's status"""
    return game.table_status()

def end_game() -> str:
    """calculate winner and end game"""
    return game.get_winner()


# the dealeronly agent with tools
dealer = AssistantAgent(
    name="Dealer",
    model_client=llm,
    tools=[request_card, request_stand, check_hand, check_table, end_game],
    system_message="""You're the Blackjack dealer.

You control the game:
- Only YOU can draw cards and process stands
- Players ask you to hit/stand, then you call the tools
- Turn order: Karthik -> Alice -> Bob -> Charlie

When someone says hit, call request_card for them.
When they say stand, call request_stand.
After everyone is done, call end_game.
When you see TERMINATE, say goodbye and stop."""
)

human = UserProxyAgent(name="Karthik")

# Alice - plays it safe
alice = AssistantAgent(
    name="Alice",
    model_client=llm,
    system_message="""You're Alice, a careful blackjack player.

You start with 0 cards! Only "Alice drew X" messages show YOUR hand.

Strategy:
- First turn: say "Hit me please" (you need cards!)
- Stand if you hit 12 or more
- Otherwise keep hitting

Keep responses short. You're polite but nervous about busting.
Don't stand with 0 cards - that makes no sense!"""
)

# Bob - likes to gamble
bob = AssistantAgent(
    name="Bob",
    model_client=llm,
    system_message="""You're Bob, you like taking risks at blackjack.

You start with 0 cards! Only "Bob drew X" messages show YOUR hand.

Strategy:  
- First turn: say "Hit me!" (gotta get cards first)
- Keep hitting until 18 or higher
- You'll take all 3 cards if you have to

Keep it short and confident. Say stuff like "let's go!" or "fortune favors the bold!"
Never stand with 0 cards."""
)

# Charlie - thinks about probability
charlie = AssistantAgent(
    name="Charlie",
    model_client=llm,
    system_message="""You're Charlie, analytical blackjack player.

You start with 0 cards! Only "Charlie drew X" messages are YOUR hand.

Strategy:
- First: say "Hit me" (start at zero)
- Hit if 16 or under, stand at 17+
- Base decisions on probability

Keep responses brief. Maybe mention odds sometimes.
Can't stand with 0 cards obviously."""
)


def pick_speaker(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
    """figures out who should talk next"""
    if not messages:
        return "Dealer"
    
    last = messages[-1]
    speaker = getattr(last, 'source', None)
    content = getattr(last, 'content', '') or ''
    if isinstance(content, list):
        content = str(content)
    
    if "terminate" in content.lower():
        return None
    
    curr = game.get_current_player()
    
    if curr is None or game.is_finished():
        return "Dealer"
    
    if speaker in ["Karthik", "Alice", "Bob", "Charlie"]:
        keywords = ["hit", "stand", "card", "hand", "deal", "draw"]
        if any(k in content.lower() for k in keywords):
            game.waiting_for_dealer = True
            return "Dealer"
    
    if speaker == "Dealer":
        return curr
    
    return curr


async def main():
    print("\n" + "="*60)
    print("    BLACKJACK - MULTI AGENT GAME")
    print("    Players: Karthik (you), Alice, Bob, Charlie")
    print("="*60 + "\n")

    stop_condition = TextMentionTermination("TERMINATE")

    chat = SelectorGroupChat(
        participants=[human, dealer, alice, bob, charlie],
        model_client=llm,
        termination_condition=stop_condition,
        selector_func=pick_speaker,
        allow_repeated_speaker=True,
    )

    await Console(chat.run_stream(
        task="Welcome to Blackjack! I am your Dealer. Let's play! Karthik, you're up first. Would you like to hit or stand?"
    ))


if __name__ == "__main__":
    print("\nStarting Blackjack...")
    print("Type 'hit' to draw, 'stand' to hold\n")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nGame ended. Thanks for playing!")
