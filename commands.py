import io
import logging
import discord
from discord.ext import commands
from typing import List, Optional

logger = logging.getLogger(__name__)

def register_commands(bot, gemini_client, config_from_db=False, log_callback=None):
    """
    Register all bot commands.
    
    Args:
        bot: The Discord bot instance
        gemini_client: The Gemini API client
        config_from_db: Whether to load configurations from database
        log_callback: Function to call for logging
    """
    # Custom logging function
    def log(level, message):
        if log_callback:
            log_callback(level, message, "COMMANDS")
        if level == "ERROR":
            logger.error(message)
        elif level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
    
    @bot.command(name="ask", help="Ask a question to Gemini AI")
    async def ask(ctx, *, question: str):
        """
        Command to ask Gemini AI a question.
        
        Args:
            ctx: The command context
            question: The question to ask
        """
        if not question:
            await ctx.send("Please provide a question to ask Gemini.")
            return
            
        # Let the user know the bot is thinking
        async with ctx.typing():
            try:
                # Generate a response from Gemini
                response = await gemini_client.generate_response(question)
                
                # Handle Discord's message length limitation
                if len(response) <= 2000:
                    await ctx.send(response)
                else:
                    # Split long responses into multiple messages
                    chunks = split_response(response)
                    for chunk in chunks:
                        await ctx.send(chunk)
                        
            except Exception as e:
                logger.error(f"Error in ask command: {str(e)}")
                await ctx.send(f"I'm sorry, I encountered an error: {str(e)}")
    
    @bot.command(name="analyze", help="Analyze an image with Gemini AI")
    async def analyze(ctx, *, prompt: Optional[str] = "Describe this image in detail"):
        """
        Command to analyze an image with Gemini AI.
        
        Args:
            ctx: The command context
            prompt: Optional prompt to guide the analysis
        """
        # Check if an image is attached
        if not ctx.message.attachments:
            await ctx.send("Please attach an image to analyze.")
            return
            
        attachment = ctx.message.attachments[0]
        
        # Check if the attachment is an image
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await ctx.send("The attachment must be an image file.")
            return
            
        # Let the user know the bot is thinking
        async with ctx.typing():
            try:
                # Download the image
                image_data = await attachment.read()
                mime_type = attachment.content_type
                
                # Generate a response from Gemini
                response = await gemini_client.generate_image_response(prompt, image_data, mime_type)
                
                # Handle Discord's message length limitation
                if len(response) <= 2000:
                    await ctx.send(response)
                else:
                    # Split long responses into multiple messages
                    chunks = split_response(response)
                    for chunk in chunks:
                        await ctx.send(chunk)
                        
            except Exception as e:
                logger.error(f"Error in analyze command: {str(e)}")
                await ctx.send(f"I'm sorry, I encountered an error analyzing the image: {str(e)}")
    
    @bot.command(name="help_gemini", help="Shows help information for Gemini AI commands")
    async def help_gemini(ctx):
        """
        Command to show help information about Gemini AI commands.
        
        Args:
            ctx: The command context
        """
        embed = discord.Embed(
            title="Gemini AI Bot Commands",
            description="Here are the commands you can use with this bot:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="!ask [question]",
            value="Ask Gemini AI a question or prompt it to generate content.",
            inline=False
        )
        
        embed.add_field(
            name="!analyze [optional prompt]",
            value="Analyze an attached image with Gemini AI. Add an optional prompt to guide the analysis.",
            inline=False
        )
        
        embed.add_field(
            name="!help_gemini",
            value="Show this help message.",
            inline=False
        )
        
        embed.set_footer(text="Powered by Google Gemini AI")
        
        await ctx.send(embed=embed)

def split_response(response: str, max_length: int = 2000) -> List[str]:
    """
    Split a long response into multiple chunks for Discord's message length limitation.
    
    Args:
        response: The response to split
        max_length: Maximum length of each chunk
        
    Returns:
        List of response chunks
    """
    # If the response is already short enough, return it as is
    if len(response) <= max_length:
        return [response]
        
    chunks = []
    current_chunk = ""
    
    # Split by paragraphs first for more natural breaks
    paragraphs = response.split('\n\n')
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed the limit
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            # If current_chunk is not empty, add it to chunks
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # If the paragraph itself is too long, split it
            if len(paragraph) > max_length:
                # Split by lines
                lines = paragraph.split('\n')
                for line in lines:
                    if len(current_chunk) + len(line) + 1 > max_length:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                        
                        # If the line itself is too long, split it by words
                        if len(line) > max_length:
                            words = line.split(' ')
                            for word in words:
                                if len(current_chunk) + len(word) + 1 > max_length:
                                    chunks.append(current_chunk.strip())
                                    current_chunk = word + " "
                                else:
                                    current_chunk += word + " "
                        else:
                            current_chunk = line + "\n"
                    else:
                        current_chunk += line + "\n"
            else:
                current_chunk = paragraph + "\n\n"
        else:
            current_chunk += paragraph + "\n\n"
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
