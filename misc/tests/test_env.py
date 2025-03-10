#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if OLLAMA_HOST is set
ollama_host = os.environ.get('OLLAMA_HOST')
if ollama_host:
    print(f"OLLAMA_HOST found in environment: {ollama_host}")
else:
    print("OLLAMA_HOST not found in environment variables, using default: http://localhost:11434")

# Print the contents of .env file (be careful with sensitive info)
try:
    with open('.env', 'r') as f:
        lines = f.readlines()
        print("\nContents of .env file:")
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                print(line.strip())
except FileNotFoundError:
    print(".env file not found") 