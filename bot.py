import os
import logging
import asyncio
import discord
from discord.ext import commands
from config import load_config
from gemini_client import GeminiClient
from commands import register_commands

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Discord bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent to read messages
bot = commands.Bot(command_prefix="!", intents=intents)

# Create Gemini client
gemini_client = None

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info("Bot is ready and connected to Discord!")
    
    # Set bot status
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, 
        name="!ask commands"
    ))

@bot.event
async def on_message(message):
    """Process incoming messages."""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
        
    # Process commands
    await bot.process_commands(message)

async def run_bot(config_from_db=False, log_callback=None):
    """
    Initialize and run the Discord bot.
    
    Args:
        config_from_db (bool): Whether to load config from database (if available)
        log_callback (callable): Function to call for logging
    """
    global gemini_client
    
    # Custom logging function
    def log(level, message):
        if log_callback:
            log_callback(level, message, "BOT")
        if level == "ERROR":
            logger.error(message)
        elif level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
    
    # Load configuration
    config = load_config()
    discord_token = config.get("DISCORD_TOKEN")
    gemini_api_key = config.get("GEMINI_API_KEY")
    
    if not discord_token:
        error_msg = "Discord token not found. Please set the DISCORD_TOKEN environment variable."
        log("ERROR", error_msg)
        return
        
    if not gemini_api_key:
        error_msg = "Gemini API key not found. Please set the GEMINI_API_KEY environment variable."
        log("ERROR", error_msg)
        return
    
    # Initialize Gemini client
    try:
        log("INFO", "Initializing Gemini client...")
        gemini_client = GeminiClient(api_key=gemini_api_key)
        log("INFO", "Gemini client initialized successfully")
    except Exception as e:
        log("ERROR", f"Failed to initialize Gemini client: {str(e)}")
        return
    
    # Register commands
    try:
        log("INFO", "Registering bot commands...")
        register_commands(bot, gemini_client, config_from_db, log_callback)
        log("INFO", "Bot commands registered successfully")
    except Exception as e:
        log("ERROR", f"Failed to register commands: {str(e)}")
        return
    
    # Run the bot
    log("INFO", "Starting Discord bot...")
    try:
        await bot.start(discord_token)
    except Exception as e:
        log("ERROR", f"Discord bot error: {str(e)}")
    finally:
        log("INFO", "Discord bot has been shut down")

def run_bot_sync():
    """Synchronous wrapper for run_bot for backward compatibility."""
    asyncio.run(run_bot())

if __name__ == "__main__":
    run_bot_sync()
