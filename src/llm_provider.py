import os
import requests
import json
from loguru import logger

class LLMProvider:
    """Provider for Ollama LLM services"""
    
    def __init__(self, config):
        self.config = config
        
        # Set up Ollama
        self.ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
        self.ollama_model = config.get('llm', {}).get('ollama_model', 'llama2')
        logger.info(f"Using Ollama with model {self.ollama_model} at {self.ollama_host}")
    
    def generate_text(self, system_prompt, user_prompt, max_tokens=1500, temperature=0.7):
        """Generate text using Ollama"""
        return self._generate_with_ollama(system_prompt, user_prompt, max_tokens, temperature)
    
    def _generate_with_ollama(self, system_prompt, user_prompt, max_tokens=1500, temperature=0.7):
        """Generate text using Ollama API"""
        try:
            # Combine system and user prompts for Ollama
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Prepare the request
            url = f"{self.ollama_host}/api/generate"
            payload = {
                "model": self.ollama_model,
                "prompt": combined_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # Make the request
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating text with Ollama: {str(e)}")
            return None
    
    def is_available(self):
        """Check if Ollama is available"""
        return self._check_ollama_available()
    
    def _check_ollama_available(self):
        """Check if Ollama API is available"""
        try:
            url = f"{self.ollama_host}/api/tags"
            response = requests.get(url)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                if any(model.get('name') == self.ollama_model for model in models):
                    return True
                else:
                    logger.warning(f"Model {self.ollama_model} not found in Ollama")
                    return False
            else:
                logger.error(f"Ollama API check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Ollama API check failed: {str(e)}")
            return False 