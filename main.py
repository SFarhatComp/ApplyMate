#!/usr/bin/env python3
import os
import json
import time
import random
import sys
import argparse
from loguru import logger
from datetime import datetime
import yaml
from dotenv import load_dotenv

from src.job_discovery import JobDiscovery
from src.resume_customizer import ResumeCustomizer
from src.application_submitter import ApplicationSubmitter
from src.captcha_handler import CaptchaHandler
from src.utils import setup_logging, create_directory_structure, get_resume_path, get_cover_letter_path, check_ollama_available, debug_env_vars, prompt_yes_no
from src.config_helper import load_config_with_env_vars
from src.cover_letter_generator import CoverLetterGenerator

# Load environment variables from .env file
load_dotenv()

def load_config():
    """Load configuration from YAML file with environment variable support."""
    config = load_config_with_env_vars()
    if not config:
        logger.error("Failed to load configuration")
        exit(1)
    
    return config

def main():
    """Main application entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Automated job application system")
    parser.add_argument("--no-cover-letters", action="store_true", help="Skip cover letter generation")
    parser.add_argument("--cover-letters", action="store_true", help="Force cover letter generation")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger.info("Starting automated job application system")
    
    # Debug environment variables
    debug_env_vars()
    
    # Load configuration
    config = load_config()
    logger.info(f"Loaded configuration with {len(config['job_search']['keywords'])} job keywords")
    
    # Check Ollama availability
    ollama_available = check_ollama_available(config)
    if not ollama_available:
        logger.warning("Ollama is not available. Cover letter customization will be limited.")
    
    # Initialize job discovery
    job_discovery = JobDiscovery(config)
    
    # Initialize cover letter generator
    max_workers = config.get('llm', {}).get('max_workers', 3)
    cover_letter_generator = CoverLetterGenerator(config, max_workers=max_workers)
    
    # Discover job listings
    logger.info("Discovering job listings...")
    jobs = job_discovery.find_jobs()
    
    # Filter jobs
    filtered_jobs = jobs
    logger.info(f"Found {len(filtered_jobs)} potential job listings")
    
    # Get resume path
    resume_path = get_resume_path()
    if not resume_path:
        logger.error("No resume found. Please add your resume to data/resume.pdf")
        return
    
    # Check if cover letter generation is enabled in config
    generate_cover_letters = config.get('application', {}).get('generate_cover_letters')
    
    # Command line arguments override config
    if args.no_cover_letters:
        generate_cover_letters = False
        logger.info("Cover letter generation disabled via command line argument")
    elif args.cover_letters:
        generate_cover_letters = True
        logger.info("Cover letter generation enabled via command line argument")
    
    # If not specified in config, ask the user
    if generate_cover_letters is None:
        generate_cover_letters = prompt_yes_no("\nDo you want to generate cover letters for these jobs?")
        
        # Update config for future use
        if 'application' not in config:
            config['application'] = {}
        config['application']['generate_cover_letters'] = generate_cover_letters
        
        # Save updated config
        with open('config/config.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    # Check for base cover letter
    cover_letter_path = None
    if generate_cover_letters:
        cover_letter_path = get_cover_letter_path()
        if not cover_letter_path:
            logger.warning("No base cover letter found. Please add your cover letter to data/base_cover_letter.pdf or data/base_cover_letter.txt")
    
    # Process each job
    processed_jobs = []
    
    if generate_cover_letters:
        # Group jobs for batch processing
        logger.info(f"Processing {len(filtered_jobs)} jobs in parallel...")
        cover_letter_paths = cover_letter_generator.generate_cover_letters_batch(filtered_jobs)
        
        # Add cover letter paths to jobs
        for job in filtered_jobs:
            if job['id'] in cover_letter_paths and cover_letter_paths[job['id']]:
                job['cover_letter_path'] = cover_letter_paths[job['id']]
                processed_jobs.append(job)
                logger.info(f"Generated cover letter for {job['title']} at {job['company']}")
            else:
                logger.error(f"Failed to generate cover letter for {job['title']} at {job['company']}")
                # Still add the job without a cover letter
                processed_jobs.append(job)
    else:
        logger.info("Cover letter generation is disabled. Skipping...")
        processed_jobs = filtered_jobs
    
    # Display results
    if filtered_jobs:
        print("\n=== Job Search Results ===")
        for i, job in enumerate(filtered_jobs, 1):
            # Clean up the URL for display
            display_url = job['url'].split('?')[0] if '?' in job['url'] else job['url']
            
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   URL: {display_url}")
            
            if generate_cover_letters and 'cover_letter_path' in job:
                print(f"   Cover Letter: {os.path.basename(job['cover_letter_path'])}")
    else:
        print("\nNo jobs found matching your criteria.")
    
    # Save processed jobs to file
    if processed_jobs:
        with open("data/processed_jobs.json", "w") as f:
            json.dump(processed_jobs, f, indent=2)
        logger.info(f"Saved {len(processed_jobs)} processed jobs to data/processed_jobs.json")
    
    logger.info(f"Application session complete. Processed {len(processed_jobs)} jobs.")

if __name__ == "__main__":
    main() 