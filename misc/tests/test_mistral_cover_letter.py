#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
import time
import sys

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils import get_resume_path

# Load environment variables
load_dotenv()

# Get Ollama host from environment or use default
ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
model = "mistral:latest"

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return ""

def generate_sample_cover_letter():
    """Generate a sample cover letter using Mistral"""
    
    # Check if Ollama is available
    try:
        url = f"{ollama_host}/api/tags"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"❌ Ollama server not available at {ollama_host}")
            return
            
        # Check if mistral model is available
        models = response.json().get('models', [])
        if not any(m.get('name') == model for m in models):
            print(f"❌ Model '{model}' not found in Ollama")
            return
    except Exception as e:
        print(f"❌ Error checking Ollama: {str(e)}")
        return
    
    # Sample job details
    job = {
        "title": "Software Developer",
        "company": "Example Tech",
        "location": "Montreal, QC",
        "url": "https://example.com/jobs/12345",
        "source": "linkedin",
        "id": "12345",
        "description": "We are looking for a Software Developer to join our team. The ideal candidate has experience with Python, JavaScript, and web development frameworks. Responsibilities include developing new features, maintaining existing code, and collaborating with cross-functional teams. Requirements: Bachelor's degree in Computer Science or related field, 1-3 years of experience in software development, proficiency in Python and JavaScript, experience with web frameworks like Django or Flask, and knowledge of database systems."
    }
    
    # Get resume text
    resume_path = get_resume_path()
    resume_text = ""
    if resume_path and os.path.exists(resume_path):
        resume_text = extract_text_from_pdf(resume_path)
        print(f"Loaded resume from {resume_path}")
    else:
        print("No resume found. Using placeholder resume text.")
        resume_text = """
        Sami Farhat
        Software Engineer
        
        EXPERIENCE
        Boeing - Application Software Developer
        May 2023 - Present
        - Developing a pilot bidding application using Python and modern web technologies
        - Implementing back-end services to improve automation and operational efficiency
        - Working with Python, XML, Bash scripting, and Oracle databases in a Linux environment
        - Following Agile methodologies for project management
        
        EDUCATION
        Concordia University - Bachelor of Computer Science
        2019 - 2023
        
        SKILLS
        Programming Languages: Python, JavaScript, Java, C++
        Web Technologies: HTML, CSS, React, Node.js
        Databases: SQL, MongoDB
        Tools: Git, Docker, Linux
        """
    
    # Get base cover letter
    base_cover_letter_path = "data/base_cover_letter.pdf"
    base_cover_letter_text = ""
    if os.path.exists(base_cover_letter_path):
        base_cover_letter_text = extract_text_from_pdf(base_cover_letter_path)
        print(f"Loaded base cover letter from {base_cover_letter_path}")
    else:
        print("No base cover letter found. Using placeholder cover letter text.")
        base_cover_letter_text = """
        Dear Hiring Manager,
        
        I am writing to express my strong interest in the [Position] position at [Company]. My name is Sami Farhat, and I am a recent graduate from Concordia University with a solid foundation in programming, gained through both academic coursework and practical work experiences.
        
        During an 8-month internship at Boeing as an Application Software Developer, I strengthened my Python expertise by working on back-end services to improve automation and operational efficiency. My responsibilities included developing features using Python and XML in a Linux environment, and I also gained hands-on experience with Bash scripting, Oracle databases, and Agile methodologies.
        
        After successfully completing my internship, I transitioned into a full-time role at Boeing, where I am leading the implementation of a groundbreaking pilot bidding application—the first of its kind in North America for Boeing.
        
        I am excited about the opportunity to contribute to [Company] and am eager to bring my skills and experiences to your team.
        
        Sincerely,
        Sami Farhat
        """
    
    # Sample system prompt - completely rewritten for better results
    system_prompt = """You are an expert cover letter writer with a specialty in tech industry applications. Your task is to create a highly personalized cover letter for Sami Farhat, a software developer currently working at Boeing.

IMPORTANT GUIDELINES:
1. ONLY mention experiences that are explicitly mentioned in Sami's resume - do not invent or reference any companies or experiences not in the resume
2. Focus primarily on Sami's experience at Boeing and his education at Concordia University
3. The letter must be addressed to the specific company and position in the job details
4. The letter must be signed "Sincerely, Sami Farhat" at the end
5. Replace any placeholders like [Position] or [Company] with the actual job details
6. Highlight specific skills from the resume that match the job requirements
7. Keep the letter professional, concise (300-400 words), and focused on value Sami can bring
8. Do not mention "DRW" or any other company not in Sami's resume
9. Use a natural, first-person writing style as if Sami wrote it himself

STRUCTURE:
- Opening paragraph: Express interest in the specific position and company
- Middle paragraphs: Highlight relevant experience at Boeing and skills that match the job requirements
- Closing paragraph: Express enthusiasm for the opportunity and desire to contribute
- Signature: "Sincerely, Sami Farhat"
"""
    
    # Sample user prompt
    user_prompt = f"""
JOB DETAILS:
Title: {job['title']}
Company: {job['company']}
Description: {job['description']}

SAMI'S RESUME:
{resume_text}

BASE COVER LETTER:
{base_cover_letter_text}

Create a personalized cover letter for this job application that focuses on Sami's actual experience at Boeing and his education at Concordia University. The letter should be addressed to {job['company']} for the {job['title']} position and signed "Sincerely, Sami Farhat".
"""
    
    # Combine prompts for Ollama
    combined_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    print(f"Generating cover letter with {model}...\n")
    start_time = time.time()
    
    try:
        # Make the request to Ollama
        url = f"{ollama_host}/api/generate"
        payload = {
            "model": model,
            "prompt": combined_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 1500
            }
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            cover_letter = result.get('response', '').strip()
            
            # Post-process to fix signature if needed
            if "[Your Name]" in cover_letter:
                cover_letter = cover_letter.replace("[Your Name]", "Sami Farhat")
                print("Fixed signature in cover letter")
            
            # Print the result
            print("Generated Cover Letter:")
            print("=" * 50)
            print(cover_letter)
            print("=" * 50)
            
            # Print generation time
            end_time = time.time()
            print(f"\nGeneration took {end_time - start_time:.2f} seconds")
            
            # Save the cover letter to a file for review
            os.makedirs("data/cover_letters", exist_ok=True)
            with open(f"data/cover_letters/test_cover_letter_{int(time.time())}.txt", "w") as f:
                f.write(cover_letter)
            print(f"Cover letter saved to data/cover_letters/test_cover_letter_{int(time.time())}.txt")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error generating cover letter: {str(e)}")

if __name__ == "__main__":
    generate_sample_cover_letter() 