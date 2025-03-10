#!/usr/bin/env python3
import os
import time
import json
import sys
from dotenv import load_dotenv
from loguru import logger

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.cover_letter_generator import CoverLetterGenerator
from src.config_helper import load_config_with_env_vars

# Load environment variables
load_dotenv()

def load_config():
    """Load configuration from YAML file with environment variable support."""
    config = load_config_with_env_vars()
    if not config:
        logger.error("Failed to load configuration")
        exit(1)
    
    return config

def load_sample_jobs():
    """Load sample jobs from found_jobs.json."""
    try:
        with open("misc/benchmarks/processed_jobs.json", "r") as f:
            jobs = json.load(f)
            return jobs
    except Exception as e:
        logger.error(f"Error loading sample jobs: {str(e)}")
        return []

def benchmark_sequential(config, jobs):
    """Benchmark sequential cover letter generation."""
    generator = CoverLetterGenerator(config)
    
    start_time = time.time()
    
    results = {}
    for job in jobs:
        logger.info(f"Generating cover letter for {job['title']} at {job['company']}")
        cover_letter_path = generator.generate_cover_letter(job)
        if cover_letter_path:
            results[job['id']] = cover_letter_path
    
    end_time = time.time()
    duration = end_time - start_time
    
    return results, duration

def benchmark_parallel(config, jobs, max_workers):
    """Benchmark parallel cover letter generation."""
    config['llm']['max_workers'] = max_workers
    generator = CoverLetterGenerator(config, max_workers=max_workers)
    
    start_time = time.time()
    
    results = generator.generate_cover_letters_batch(jobs)
    
    end_time = time.time()
    duration = end_time - start_time
    
    return results, duration

def main():
    """Main benchmark function."""
    # Setup logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=""))
    
    # Load configuration
    config = load_config()
    
    # Load sample jobs
    jobs = load_sample_jobs()
    if not jobs:
        logger.error("No jobs found for benchmarking")
        return
    
    # Limit to 5 jobs for benchmarking
    jobs = jobs[:5]
    logger.info(f"Benchmarking with {len(jobs)} jobs")
    
    # Benchmark sequential
    logger.info("\n\n=== Sequential Processing ===")
    seq_results, seq_duration = benchmark_sequential(config, jobs)
    logger.info(f"Sequential processing took {seq_duration:.2f} seconds")
    logger.info(f"Generated {len(seq_results)} cover letters")
    
    # Benchmark parallel with different worker counts
    for workers in [2, 3, 5]:
        logger.info(f"\n\n=== Parallel Processing ({workers} workers) ===")
        par_results, par_duration = benchmark_parallel(config, jobs, workers)
        logger.info(f"Parallel processing with {workers} workers took {par_duration:.2f} seconds")
        logger.info(f"Generated {len(par_results)} cover letters")
        
        # Calculate speedup
        speedup = seq_duration / par_duration
        logger.info(f"Speedup: {speedup:.2f}x")

if __name__ == "__main__":
    main() 