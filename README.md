# Discord Gemini AI Bot

A Discord bot that leverages Google's Gemini AI to respond to user queries and commands.

## Features

- Respond to text queries using Google's Gemini Pro model
- Analyze images with Gemini Pro Vision model
- Command system for easy interaction
- Configurable via environment variables
- Support for long responses by splitting messages

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- A Discord bot token
- A Google Gemini API key

### Setting Up in Replit

1. Create a new Replit or open your existing one
2. Import this project into Replit:
   - You can upload the files directly through Replit's file uploader
   - Or, clone from a Git repository if you've pushed the code there

3. Set up the environment variables in Replit:
   - Go to the "Secrets" tab (lock icon) in the sidebar
   - Add the following secrets:
     - `DISCORD_TOKEN`: Your Discord bot token
     - `GEMINI_API_KEY`: Your Google Gemini API key

4. Install the required packages:
   - Google Generative AI library: `pip install google-generativeai`
   - Discord.py library: `pip install discord.py`
   - Python-dotenv: `pip install python-dotenv`

5. Run the bot by clicking the "Run" button or typing `python main.py` in the Shell

### Getting API Keys

#### Discord Bot Token
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" tab and click "Add Bot"
4. Under the "Token" section, click "Copy" to copy your bot token
5. Enable "Message Content Intent" under Privileged Gateway Intents

#### Gemini API Key
1. Go to the [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key for use in your bot

### Inviting the Bot to Your Server

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Go to the "OAuth2" tab and then "URL Generator"
4. Select the following scopes:
   - `bot`
   - `applications.commands`
5. In the "Bot Permissions" section, select:
   - "Read Messages/View Channels"
   - "Send Messages"
   - "Embed Links"
   - "Attach Files"
   - "Read Message History"
6. Copy the generated URL and paste it in your browser to invite the bot to your server

## Using the Bot

The bot supports the following commands:

- `!ask [question]` - Ask Gemini AI a question
- `!analyze [optional prompt]` - Analyze an attached image with Gemini AI
- `!help_gemini` - Show help information for the bot

## Customization

You can customize the bot by modifying the following files:

- `config.py` - Configuration loading and defaults
- `commands.py` - Command definitions and handler functions
- `bot.py` - Bot initialization and event handlers
- `gemini_client.py` - Interaction with the Gemini API

## Troubleshooting

- If the bot is not responding, check the console output for any error messages
- Ensure that you've properly set up the environment variables
- Make sure the bot has the necessary permissions in your Discord server
- Verify that the Gemini API key is valid and has access to the required models

## License

This project is licensed under the MIT License.
