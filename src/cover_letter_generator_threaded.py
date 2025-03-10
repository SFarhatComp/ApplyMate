import os
import json
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
from datetime import datetime
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from src.llm_provider import LLMProvider

# Load environment variables from .env file
load_dotenv()

class CoverLetterGenerator:
    def __init__(self, config, max_workers=3):
        self.config = config
        self.llm_provider = LLMProvider(config)
        self.base_cover_letter_path = "data/base_cover_letter.pdf"
        self.output_directory = "data/cover_letters"
        self.max_workers = max_workers  # Maximum number of concurrent threads
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_directory, exist_ok=True)
        
        # Check if LLM provider is available
        if not self.llm_provider.is_available():
            logger.warning("LLM provider not available. Cover letter customization will be limited.")
    
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
        
        # Extract base cover letter text once to avoid repeated file I/O
        base_cover_letter = self._extract_text_from_pdf(self.base_cover_letter_path)
        if not base_cover_letter:
            logger.error("Failed to extract text from base cover letter PDF")
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
            thread = threading.Thread(
                target=self._worker_thread, 
                args=(job_queue, results, base_cover_letter)
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        logger.info(f"Generated {len(results)} cover letters using {self.max_workers} threads")
        return results
    
    def _worker_thread(self, job_queue, results, base_cover_letter):
        """Worker thread to process jobs from the queue."""
        while not job_queue.empty():
            try:
                job = job_queue.get(block=False)
                logger.info(f"Generating cover letter for {job['title']} at {job['company']}")
                
                # Generate cover letter
                cover_letter_path = self._generate_single_cover_letter(job, base_cover_letter)
                
                # Store result
                if cover_letter_path:
                    results[job['id']] = cover_letter_path
                
                # Mark task as done
                job_queue.task_done()
                
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error in worker thread: {str(e)}")
                try:
                    job_queue.task_done()
                except:
                    pass
    
    def _generate_single_cover_letter(self, job, base_cover_letter):
        """Generate a cover letter for a single job."""
        try:
            # Extract job details
            job_title = job.get('title', 'Unknown Position')
            company = job.get('company', 'the Company')
            job_description = job.get('description', '')
            
            # Prepare prompts for the LLM
            system_prompt = "You are a professional cover letter writer. Your task is to customize a cover letter for a specific job application."
            user_prompt = self._create_prompt(base_cover_letter, job_title, company, job_description)
            
            # Generate customized cover letter using LLM provider
            customized_cover_letter = self.llm_provider.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1500,
                temperature=0.7
            )
            
            if not customized_cover_letter:
                logger.error(f"Failed to generate customized cover letter for {job_title} at {company}")
                return self._use_base_cover_letter(job)
            
            # Save the cover letter to a file
            filename = self._save_cover_letter(customized_cover_letter, job)
            
            return filename
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            return self._use_base_cover_letter(job)
    
    def generate_cover_letter(self, job):
        """Generate a customized cover letter for a specific job (single job version)."""
        if not self.llm_provider.is_available():
            logger.warning("LLM provider not available. Using base cover letter without customization.")
            return self._use_base_cover_letter(job)
        
        try:
            # Load base cover letter from PDF
            if not os.path.exists(self.base_cover_letter_path):
                logger.error(f"Base cover letter not found at {self.base_cover_letter_path}")
                return None
            base_cover_letter = self._extract_text_from_pdf(self.base_cover_letter_path)
            if not base_cover_letter:
                logger.error("Failed to extract text from base cover letter PDF")
                return None
            
            return self._generate_single_cover_letter(job, base_cover_letter)
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            return self._use_base_cover_letter(job)
    
    def _create_prompt(self, base_cover_letter, job_title, company, job_description):
        """Create a prompt for the LLM to generate a customized cover letter."""
        return f"""
        Please customize this cover letter for a {job_title} position at {company}.
        
        The job description is: {job_description}
        
        Here's my base cover letter:
        
        {base_cover_letter}
        
        Please replace any placeholders like [Position] and [Company] with the actual job title and company name.
        Tailor the content to highlight skills and experiences relevant to this specific job.
        Keep the overall tone professional but personable.
        The final cover letter should be ready to send without any placeholders or instructions.
        """
    
    def _extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return None
    
    def _save_cover_letter(self, cover_letter_text, job):
        """Save the cover letter to a file."""
        try:
            company = job.get('company', 'Unknown').replace(' ', '_')
            title = job.get('title', 'Position').replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            filename = f"{self.output_directory}/{company}_{title}_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(cover_letter_text)
            
            logger.info(f"Saved cover letter to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving cover letter: {str(e)}")
            return None
    
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