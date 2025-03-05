import requests
import json
from typing import Optional, Dict, Any, List
import time

class OllamaService:
    """Service for interacting with local Ollama models"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        """
        Initialize the Ollama service
        
        Args:
            base_url: Base URL for Ollama API
            model: Default model to use
        """
        self.base_url = base_url
        self.model = model
        
    def generate(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response from the Ollama model
        
        Args:
            prompt: The prompt to send to the model
            options: Additional options for generation
            
        Returns:
            str: The generated response
        """
        url = f"{self.base_url}/api/generate"
        
        # Default options
        default_options = {
            "temperature": 0.4,  # Lower temperature for more focused summaries
            "top_p": 0.9,
            "num_predict": 4096,  
        }
        
        # Override defaults with any provided options
        if options:
            default_options.update(options)
        
        # Prepare request
        data = {
            "model": self.model,
            "prompt": prompt,
            "options": default_options,
            "stream": False
        }
        
        # Make request
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            raise Exception(f"Ollama API error: {response.text}")
    