# Rocket League Quick Chat Analyzer

Tracks and analyzes the quick chats you send during Rocket League matches. Connects to your controller, records every d-pad combo in real time, and shows you breakdowns of what you actually spam.

## What it does

- Detects quick chats from your controller's d-pad inputs
- Shows a live feed of chats as you play
- Saves your history across sessions
- Analysis tab with charts — most used chats, combos, patterns
- Runs in the system tray so it stays out of the way

## Requirements

- Windows
- A controller connected via USB or Bluetooth
- Rocket League (obviously)

## How to use

1. Download `QCAnalyzer.exe` from the [Releases](../../releases) page
2. Run it; no install needed
3. Go to the **Setup** tab and map your quick chat layout if needed
4. Switch to the **Recording** tab and hit **Start Recording**
5. Play some games
6. Check the **Analysis** tab when you're done

The app saves your chat history automatically so data carries over between sessions. You can clear it anytime from the Recording tab.

## Building from source

```
pip install -r requirements.txt
python app.py
```
