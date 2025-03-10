import os
import json
import threading
import queue
import time
from loguru import logger
from datetime import datetime
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from src.llm_provider import LLMProvider
from src.utils import get_resume_path

# Load environment variables from .env file
load_dotenv()

class CoverLetterGenerator:
    def __init__(self, config, max_workers=3):
        self.config = config
        self.llm_provider = LLMProvider(config)
        self.base_cover_letter_path = "data/base_cover_letter.pdf"
        self.resume_path = get_resume_path()
        self.output_directory = "data/cover_letters"
        self.max_workers = max_workers  # Maximum number of concurrent threads
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_directory, exist_ok=True)
        
        # Check if LLM provider is available
        if not self.llm_provider.is_available():
            logger.warning("LLM provider not available. Cover letter customization will be limited.")
        
        # Extract resume text once to avoid repeated file I/O
        self.resume_text = ""
        if self.resume_path and os.path.exists(self.resume_path):
            self.resume_text = self._extract_text_from_pdf(self.resume_path)
            if not self.resume_text:
                logger.warning("Failed to extract text from resume PDF")
        
        # Extract base cover letter text once to avoid repeated file I/O
        self.base_cover_letter_text = ""
        if os.path.exists(self.base_cover_letter_path):
            self.base_cover_letter_text = self._extract_text_from_pdf(self.base_cover_letter_path)
            if not self.base_cover_letter_text:
                logger.warning("Failed to extract text from base cover letter PDF")
    
    def generate_cover_letter(self, job):
        """Generate a customized cover letter for a specific job."""
        if not self.llm_provider.is_available():
            logger.warning("LLM provider not available. Using base cover letter without customization.")
            return self._use_base_cover_letter(job)
        
        try:
            # Check if we have the necessary files
            if not self.base_cover_letter_text:
                logger.error("Base cover letter text not available")
                return None
            
            # Get job details
            job_title = job.get('title', 'Unknown Position')
            company = job.get('company', 'Unknown Company')
            job_description = job.get('description', '')
            
            # Prepare system prompt
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
            
            # Prepare user prompt
            user_prompt = f"""
JOB DETAILS:
Title: {job_title}
Company: {company}
Description: {job_description}

APPLICANT'S RESUME:
{self.resume_text}

BASE COVER LETTER:
{self.base_cover_letter_text}

Create a personalized cover letter for this job application that focuses on Sami's actual experience at Boeing and his education at Concordia University. The letter should be addressed to {company} for the {job_title} position and signed "Sincerely, Sami Farhat".
"""
            
            # Generate cover letter
            logger.info(f"Generating cover letter for {job_title} at {company}")
            cover_letter_text = self.llm_provider.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            if not cover_letter_text:
                logger.error("Failed to generate cover letter text")
                return None
            
            # Post-process the cover letter to ensure correct signature
            if "[Your Name]" in cover_letter_text:
                cover_letter_text = cover_letter_text.replace("[Your Name]", self.config['user']['name'])
                logger.info("Fixed signature in cover letter")
            
            # Save cover letter to file
            return self._save_cover_letter(cover_letter_text, job)
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            return None
    
    def _extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file."""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return None
    
    def _save_cover_letter(self, cover_letter, job):
        """Save the cover letter to a file and return the filename."""
        # Create a filename based on job details
        company = job.get('company', 'Unknown').replace(' ', '_')
        title = job.get('title', 'Position').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"{self.output_directory}/{company}_{title}_{timestamp}.txt"
        
        # Save the cover letter
        with open(filename, 'w') as f:
            f.write(cover_letter)
        
        logger.info(f"Saved customized cover letter to {filename}")
        return filename
    
    def generate_cover_letters_batch(self, jobs):
        """Generate cover letters for multiple jobs in parallel using threads."""
        if not jobs:
            logger.warning("No jobs provided for cover letter generation")
            return {}
        
        if not self.llm_provider.is_available():
            logger.warning("LLM provider not available. Using base cover letter without customization.")
            results = {}
            for job in jobs:
                results[job['id']] = self._use_base_cover_letter(job)
            return results
        
        # Check if we have the necessary files
        if not self.base_cover_letter_text:
            logger.error("Base cover letter text not available")
            return {}
        
        # Create a thread pool
        results = {}
        job_queue = queue.Queue()
        
        # Add jobs to the queue
        for job in jobs:
            job_queue.put(job)
        
        # Create and start worker threads
        threads = []
        for _ in range(min(self.max_workers, len(jobs))):
            thread = threading.Thread(target=self._worker_thread, args=(job_queue, results))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        logger.info(f"Generated {len(results)} cover letters using {self.max_workers} threads")
        return results
    
    def _worker_thread(self, job_queue, results):
        """Worker thread for processing jobs."""
        while True:
            try:
                # Get a job from the queue
                job = job_queue.get(block=False)
                
                # Get job details
                job_id = job.get('id', 'unknown')
                job_title = job.get('title', 'Unknown Position')
                company = job.get('company', 'Unknown Company')
                job_description = job.get('description', '')
                
                logger.info(f"Thread processing job: {job_title} at {company}")
                
                # Prepare system prompt
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
                
                # Prepare user prompt
                user_prompt = f"""
JOB DETAILS:
Title: {job_title}
Company: {company}
Description: {job_description}

APPLICANT'S RESUME:
{self.resume_text}

BASE COVER LETTER:
{self.base_cover_letter_text}

Create a personalized cover letter for this job application that focuses on Sami's actual experience at Boeing and his education at Concordia University. The letter should be addressed to {company} for the {job_title} position and signed "Sincerely, Sami Farhat".
"""
                
                # Generate cover letter
                cover_letter_text = self.llm_provider.generate_text(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=2000,
                    temperature=0.7
                )
                
                if cover_letter_text:
                    # Post-process the cover letter to ensure correct signature
                    if "[Your Name]" in cover_letter_text:
                        cover_letter_text = cover_letter_text.replace("[Your Name]", self.config['user']['name'])
                        logger.info("Fixed signature in cover letter")
                    
                    # Save cover letter to file
                    cover_letter_path = self._save_cover_letter(cover_letter_text, job)
                    if cover_letter_path:
                        # Store the result
                        results[job['id']] = cover_letter_path
                else:
                    logger.error(f"Failed to generate cover letter for {job_title} at {company}")
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error in worker thread: {str(e)}")
    
    def _use_base_cover_letter(self, job):
        """Use the base cover letter without customization."""
        if not os.path.exists(self.base_cover_letter_path):
            logger.error(f"Base cover letter not found at {self.base_cover_letter_path}")
            return None
        
        try:
            # Extract text from PDF
            base_cover_letter_text = self._extract_text_from_pdf(self.base_cover_letter_path)
            if not base_cover_letter_text:
                logger.error("Failed to extract text from base cover letter PDF")
                return None
            
            # Create a copy of the base cover letter
            company = job.get('company', 'Unknown').replace(' ', '_')
            title = job.get('title', 'Position').replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            filename = f"{self.output_directory}/{company}_{title}_{timestamp}.txt"
            
            # Save the extracted text
            with open(filename, 'w') as f:
                f.write(base_cover_letter_text)
            
            logger.info(f"Used base cover letter for {title} at {company}")
            return filename
            
        except Exception as e:
            logger.error(f"Error using base cover letter: {str(e)}")
            return None 