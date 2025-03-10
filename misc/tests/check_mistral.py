#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Get Ollama host from environment or use default
ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')

def check_mistral_available():
    """Check if Mistral model is available in Ollama"""
    try:
        # Check if Ollama server is running
        url = f"{ollama_host}/api/tags"
        print(f"Checking Ollama at {url}...")
        
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ Ollama server is running!")
            
            # Get available models
            models = response.json().get('models', [])
            if models:
                print("\nAvailable models:")
                for model in models:
                    print(f"- {model.get('name')}")
                
                # Check specifically for mistral
                if any(model.get('name') == "mistral:latest" for model in models):
                    print("\n✅ Mistral model is available!")
                else:
                    print("\n❌ Mistral model not found. You need to pull it:")
                    print("Run: docker exec -it ollama ollama pull mistral")
            else:
                print("\nNo models found. You may need to pull models:")
                print("Run: docker exec -it ollama ollama pull mistral")
            
            return True
        else:
            print(f"❌ Ollama server returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {str(e)}")
        print("\nMake sure your Ollama container is running:")
        print("1. Check with: docker ps | grep ollama")
        print("2. Start if needed: docker-compose up -d")
        return False

if __name__ == "__main__":
    check_mistral_available() 