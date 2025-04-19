import logging
from typing import Optional, List, Dict, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for interacting with Google's Gemini API."""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        """
        Initialize the Gemini client.
        
        Args:
            api_key (str): The Gemini API key
            model (str, optional): The model to use. Defaults to "gemini-pro".
        """
        self.api_key = api_key
        self.model_name = model
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        try:
            # Initialize the model
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Successfully initialized Gemini model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise
    
    async def generate_response(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Generate a response to the given prompt using the Gemini API.
        
        Args:
            prompt (str): The user's input prompt
            temperature (float, optional): Controls randomness. Defaults to 0.7.
            
        Returns:
            str: The generated response
        """
        try:
            # Generate a response using the Gemini model
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                )
            )
            
            # Extract and return the text from the response
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"I'm sorry, I encountered an error: {str(e)}"

    async def generate_image_response(self, prompt: str, image_data: bytes, mime_type: str = "image/jpeg") -> str:
        """
        Generate a response to a prompt with an image using the Gemini API.
        
        Args:
            prompt (str): The user's text prompt
            image_data (bytes): The image data
            mime_type (str, optional): The MIME type of the image. Defaults to "image/jpeg".
            
        Returns:
            str: The generated response
        """
        try:
            # Use the vision model for image processing
            vision_model = genai.GenerativeModel('gemini-pro-vision')
            
            # Prepare the image for the API
            image_parts = [
                {"mime_type": mime_type, "data": image_data},
                {"text": prompt}
            ]
            
            # Generate response with the image
            response = vision_model.generate_content(image_parts)
            
            # Extract and return the text
            return response.text
        except Exception as e:
            logger.error(f"Error generating image response: {str(e)}")
            return f"I'm sorry, I encountered an error processing the image: {str(e)}"
