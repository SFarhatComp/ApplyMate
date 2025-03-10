# Miscellaneous Utilities and Tests

This directory contains various utility scripts, tests, and benchmarks for the Job Application AI system.

## Directory Structure

- `tests/`: Test scripts for various components
- `benchmarks/`: Performance benchmarking tools
- `utils/`: Utility scripts for maintenance and debugging

## Tests

### Ollama Tests

- `tests/test_ollama.py`: Tests basic Ollama functionality
- `tests/check_mistral.py`: Checks if the Mistral model is available in Ollama
- `tests/test_mistral_cover_letter.py`: Tests generating a cover letter with Mistral

### Environment Tests

- `tests/test_env.py`: Tests environment variable configuration

## Benchmarks

- `benchmarks/benchmark_cover_letters.py`: Benchmarks cover letter generation performance with different thread counts

## Usage

Run tests from the project root directory:

```bash
# Test Ollama functionality
python misc/tests/test_ollama.py

# Check if Mistral model is available
python misc/tests/check_mistral.py

# Test cover letter generation with Mistral
python misc/tests/test_mistral_cover_letter.py

# Run benchmarks
python misc/benchmarks/benchmark_cover_letters.py
``` 