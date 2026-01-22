# Blackjack with AI Opponents

So I built this terminal-based blackjack game where you play against 3 AI agents. Honestly, I started this as an interview take home project and wanted to see if I could get multiple agents to actually interact properly. It turned out to work pretty well!

## What's this about?

It's blackjack game, but you're playing against bots that have different "personalities":

- **You** — do whatever you want, your strategies are up to you
- **Alice** — plays it safe, stops early
- **Bob** — keeps hitting, likes to push his luck
- **Charlie** — overthinks everything

## You'll need

- Python 3.12 or newer
- An OpenAI API key ()

## How to run this?

Set up a venv:
```bash
python3 -m venv venv
source venv/bin/activate
```


Install Dependencies:
```bash
pip install -r requirements.txt
```

Now the API key, make a `.env` file:
```bash
echo "OPENAI_API_KEY=your-key-goes-here" > .env
```

Or just export it:
```bash
export OPENAI_API_KEY="your-key-goes-here"
```

## Playing

Run the python file:
```bash
python blackjack.py
```

You'll get something like:
```
--------------------------------------------------------
     BLACKJACK: MULTI-AGENT EDITION 
   Players: Karthik (You), Alice, Bob, Charlie
------------------------------------------------------
```

When it's your turn, currently your turn's name is set to 'Karthik' but you can change it to your name if you need, else you can continue assuming your player name as 'Karthik' and just type `hit` or `hit me` to draw, or `stand` when you're done. Then sit back and watch the AI players do their thing.

## Quick rules

- Everyone starts empty-handed
- Max 3 cards per player
- Cards are worth 2-11 (randomly)
- Go over 21? Bust, you're out
- Highest score under 21 wins

## Sample round

```
Enter your response: hit
---------- TextMessage (Karthik) ----------
hit
---------- ToolCallSummaryMessage (Dealer) ----------
RESULT: Karthik drew 9. Hand: [9] (Total: 9).

Enter your response: hit
---------- ToolCallSummaryMessage (Dealer) ----------
RESULT: Karthik drew 7. Hand: [9, 7] (Total: 16).

Enter your response: stand
---------- ToolCallSummaryMessage (Dealer) ----------
RESULT: Karthik stands with total 16.

---------- TextMessage (Alice) ----------
Hit me please!
...

--------------------------------------
   FINAL RESULTS
---------------------------------------
  Karthik: [9, 7] = 16
  Alice: [5, 5, 7] = 17
  Bob: [6, 4, 3] = 13
  Charlie: [10, 2, 9] = 21
-------------------------------------
WINNER: Charlie with a score of 21!
```

## Under the hood

AutoGen framework is used, GPT-4o-mini for the agent brains. The whole thing runs on a SelectorGroupChat, the agents will take turns and route their moves through the Dealer.

So the flow looks like:
* You + the 3 AI agents (Alice, Bob, Charlie) all say "hit me" or "stand"
* Messages go to the Dealer
* Dealer has tools to actually draw cards and update scores
* Everyone sees what happened, then next player goes

That's it. It is straightforward once you see it in action.

