import os
from dotenv import load_dotenv

def load_config():
    """
    Load configuration from environment variables or .env file
    
    Returns:
        dict: Configuration dictionary
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Return configuration dictionary
    return {
        "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN", ""),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        # Add more configuration variables as needed
        "MAX_RESPONSE_LENGTH": int(os.getenv("MAX_RESPONSE_LENGTH", "2000")),
        "ALLOWED_CHANNELS": os.getenv("ALLOWED_CHANNELS", "").split(",") if os.getenv("ALLOWED_CHANNELS") else None,
        "ALLOWED_ROLES": os.getenv("ALLOWED_ROLES", "").split(",") if os.getenv("ALLOWED_ROLES") else None,
    }
