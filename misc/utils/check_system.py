#!/usr/bin/env python3
import os
import sys
import platform
import subprocess
import requests
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load environment variables
load_dotenv()

def check_python_version():
    """Check Python version."""
    version = platform.python_version()
    print(f"Python version: {version}")
    if version < "3.8":
        print("❌ Python version is too old. Please use Python 3.8 or newer.")
    else:
        print("✅ Python version is sufficient.")
    print()

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        "beautifulsoup4",
        "playwright",
        "pyyaml",
        "python-docx",
        "numpy",
        "pandas",
        "requests",
        "loguru",
        "PyPDF2",
        "python-dotenv",
        "ollama"
    ]
    
    print("Checking required packages:")
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} is installed.")
        except ImportError:
            print(f"❌ {package} is not installed. Run: pip install {package}")
    
    print()

def check_playwright():
    """Check if Playwright browsers are installed."""
    try:
        result = subprocess.run(["playwright", "install", "--help"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        if result.returncode == 0:
            print("✅ Playwright is installed.")
            
            # Check if browsers are installed
            browsers = ["chromium", "firefox", "webkit"]
            for browser in browsers:
                try:
                    # This is a simple check - it doesn't guarantee the browser is fully installed
                    result = subprocess.run(["playwright", "install", browser, "--dry-run"], 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE, 
                                          text=True)
                    if "already installed" in result.stdout or "already installed" in result.stderr:
                        print(f"✅ Playwright {browser} is installed.")
                    else:
                        print(f"❓ Playwright {browser} may not be installed. Run: playwright install {browser}")
                except Exception:
                    print(f"❓ Could not check if Playwright {browser} is installed.")
        else:
            print("❌ Playwright CLI is not installed properly.")
    except FileNotFoundError:
        print("❌ Playwright is not installed. Run: pip install playwright && playwright install")
    
    print()

def check_ollama():
    """Check if Ollama is available."""
    ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
    print(f"Checking Ollama at {ollama_host}...")
    
    try:
        response = requests.get(f"{ollama_host}/api/tags")
        
        if response.status_code == 200:
            print("✅ Ollama server is running.")
            
            # Check available models
            models = response.json().get('models', [])
            if models:
                print("Available models:")
                for model in models:
                    print(f"  - {model.get('name')}")
            else:
                print("❌ No models found in Ollama.")
                print("   Run: ollama pull mistral:latest")
        else:
            print(f"❌ Ollama server returned status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {str(e)}")
        print("   Make sure Ollama is installed and running.")
    
    print()

def check_directories():
    """Check if required directories exist."""
    required_dirs = [
        "config",
        "data",
        "data/cover_letters",
        "logs"
    ]
    
    print("Checking required directories:")
    
    for directory in required_dirs:
        if os.path.exists(directory) and os.path.isdir(directory):
            print(f"✅ {directory} exists.")
        else:
            print(f"❌ {directory} does not exist. Creating it...")
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"  ✅ Created {directory}.")
            except Exception as e:
                print(f"  ❌ Error creating {directory}: {str(e)}")
    
    print()

def check_config_files():
    """Check if required configuration files exist."""
    config_file = "config/config.yaml"
    example_config = "config/config.yaml.example"
    
    print("Checking configuration files:")
    
    if os.path.exists(config_file):
        print(f"✅ {config_file} exists.")
    else:
        print(f"❌ {config_file} does not exist.")
        
        if os.path.exists(example_config):
            print(f"  ℹ️ You can copy {example_config} to {config_file}.")
        else:
            print(f"  ❌ {example_config} does not exist either.")
    
    print()

def check_resume_files():
    """Check if resume and cover letter files exist."""
    resume_file = "data/resume.pdf"
    cover_letter_file = "data/base_cover_letter.pdf"
    
    print("Checking resume and cover letter files:")
    
    if os.path.exists(resume_file):
        print(f"✅ {resume_file} exists.")
    else:
        print(f"❌ {resume_file} does not exist. Please add your resume.")
    
    if os.path.exists(cover_letter_file):
        print(f"✅ {cover_letter_file} exists.")
    else:
        print(f"❌ {cover_letter_file} does not exist. Please add your base cover letter.")
    
    print()

def main():
    """Run all checks."""
    print("=== System Check ===\n")
    
    check_python_version()
    check_dependencies()
    check_playwright()
    check_ollama()
    check_directories()
    check_config_files()
    check_resume_files()
    
    print("=== System Check Complete ===")

if __name__ == "__main__":
    main() 