import os
import json
from docx import Document
import openai
from loguru import logger
from src.utils import get_resume_path

class ResumeCustomizer:
    def __init__(self, config):
        self.config = config
        self.user_profile = self._load_user_profile()
        
        # Set OpenAI API key from environment variable
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        if not openai.api_key:
            logger.warning("OpenAI API key not found. Resume and cover letter customization will be limited.")
    
    def _load_user_profile(self):
        """Load user profile from JSON file."""
        try:
            with open("data/user_profile.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("User profile not found. Creating a basic profile.")
            # Create a basic profile from config
            basic_profile = {
                "name": self.config['user']['name'],
                "email": self.config['user']['email'],
                "phone": self.config['user']['phone'],
                "linkedin": self.config['user']['linkedin'],
                "github": self.config['user']['github'],
                "skills": [],
                "experience": [],
                "education": [],
                "projects": []
            }
            
            # Save the basic profile
            os.makedirs("data", exist_ok=True)
            with open("data/user_profile.json", "w") as f:
                json.dump(basic_profile, f, indent=2)
            
            return basic_profile
    
    def tailor_resume(self, job):
        """Get the resume path for a specific job."""
        logger.info(f"Using resume for: {job['title']} at {job['company']}")
        
        # Simply return the path to the resume file
        resume_path = get_resume_path()
        if resume_path:
            logger.success(f"Using resume from {resume_path}")
            return resume_path
        else:
            logger.error("No resume file found")
            return None
    
    def generate_cover_letter(self, job):
        """Generate a cover letter for a specific job."""
        logger.info(f"Generating cover letter for: {job['title']} at {job['company']}")
        
        # Sanitize job details for filenames
        company = job['company'].replace(' ', '_').replace('/', '_')
        title = job['title'].replace(' ', '_').replace('/', '_')
        
        # Generate a template cover letter
        template = self._generate_template_cover_letter(job)
        
        # Save the cover letter
        output_filename = f"data/cover_letters/cover_letter_{company}_{title}.txt"
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        
        with open(output_filename, "w") as f:
            f.write(template)
        
        logger.success(f"Cover letter generated and saved to {output_filename}")
        return output_filename
    
    def _generate_template_cover_letter(self, job):
        """Generate a template cover letter."""
        template = f"""
        {self.config['user']['name']}
        {self.config['user']['email']}
        {self.config['user']['phone']}
        
        Dear Hiring Manager,
        
        I am writing to express my strong interest in the {job['title']} position at {job['company']}. My name is {self.config['user']['name']}, and I am a recent graduate from Concordia University with a solid foundation in programming, gained through both academic coursework and practical work experiences. Over the course of my studies, I have cultivated strong skills in various programming languages (C++ OOP, Java, Python, and assembly languages) and developed proficiency in multiple operating systems (Linux, Windows, and macOS).
        
        During an 8-month internship at Boeing as an Application Software Developer, I strengthened my Python expertise by working on back-end services to improve automation and operational efficiency. My responsibilities included developing features using Python and XML in a Linux environment, and I also gained hands-on experience with Bash scripting, Oracle databases, and Agile methodologies. This role allowed me to create and implement features that streamlined debugging in production, significantly improving system reliability and reducing troubleshooting time.
        
        After successfully completing my internship, I transitioned into a full-time role at Boeing, where I am leading the implementation of a groundbreaking pilot bidding application—the first of its kind in North America for Boeing. This system integrates seamlessly with other planning products, enhancing operational efficiency and pilot experience. Through this project, I have expanded my expertise in project management and innovative software solutions, reinforcing my passion for solving complex challenges.
        
        Beyond my professional roles, I have undertaken several projects that showcase my skills. These include:
        - Creating a process manager leveraging multithreading and virtual memory management.
        - Building a fully functioning portable breathalyzer and companion Android application.
        - Developing a real-time offline translation system, using RabbitMQ for efficient message routing and Docker for containerization with a Python FastAPI backend implementation.
        
        I am excited about the opportunity to contribute to {job['company']} and am eager to bring my skills and experiences to your team. Thank you for considering my application. I look forward to the possibility of discussing this exciting opportunity with you.
        
        Sincerely,
        {self.config['user']['name']}
        """
        
        return template 