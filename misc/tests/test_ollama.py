import os
import requests
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Get Ollama host from environment or use default
ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
ollama_model = "mistral:latest"  # Using Mistral model with tag

def check_ollama_available():
    """Check if Ollama is available and list available models"""
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
            else:
                print("\nNo models found. You may need to pull a model:")
                print("Run: ollama pull llama2")
            
            return True
        else:
            print(f"❌ Ollama server returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {str(e)}")
        print("\nMake sure Ollama is installed and running:")
        print("1. Install Ollama from https://ollama.ai/")
        print("2. Start the Ollama server")
        print("3. Pull a model with: ollama pull llama2")
        return False

def test_ollama_generation():
    """Test generating text with Ollama"""
    if not check_ollama_available():
        return
    
    # Check if the model exists
    url = f"{ollama_host}/api/tags"
    response = requests.get(url)
    models = response.json().get('models', [])
    
    if not any(model.get('name') == ollama_model for model in models):
        print(f"\n❌ Model '{ollama_model}' not found. Pulling it now...")
        print(f"Run this command manually: ollama pull {ollama_model}")
        return
    
    # Test generation
    print(f"\nTesting text generation with model '{ollama_model}'...")
    
    try:
        url = f"{ollama_host}/api/generate"
        payload = {
            "model": ollama_model,
            "prompt": "Write a short greeting in 10 words or less.",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 50
            }
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Generation successful!")
            print(f"Response: {result.get('response', '')}")
        else:
            print(f"\n❌ Generation failed with status code: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"\n❌ Error during generation: {str(e)}")

if __name__ == "__main__":
    test_ollama_generation() 