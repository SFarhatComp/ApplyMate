# eApplyMate: AI-Powered Job Application Assistant

<p align="center">
  <img src="docs/images/eapplymate-logo.png" alt="eApplyMate Logo" width="200"/>
</p>

<p align="center">
  <strong>Streamline your job search with AI-powered automation</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#gpu-acceleration">GPU Acceleration</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

## Overview

eApplyMate is an intelligent system that automates the job application process by discovering job listings, customizing resumes, generating personalized cover letters, and submitting applications while avoiding bot detection. It uses AI to tailor your applications to each job, increasing your chances of getting interviews.

## Features

- **🔍 Automated Job Discovery**: Scrapes job boards like LinkedIn and Indeed for relevant positions
- **📄 Resume Customization**: Tailors your resume for each job using AI-extracted keywords
- **✉️ Cover Letter Generation**: Creates personalized cover letters using local LLMs (Mistral, Llama)
- **🤖 Automated Form Submission**: Fills out application forms and uploads documents
- **🧩 CAPTCHA Handling**: Integrates with CAPTCHA solving services
- **👤 Anti-Bot Detection**: Implements human-like behavior to avoid detection
- **⚙️ Configurable Settings**: Customize job search criteria, application limits, and more
- **🚀 GPU Acceleration**: Supports NVIDIA GPU acceleration for faster LLM inference
- **🔒 Privacy-Focused**: Runs entirely on your local machine - no data sent to third parties

## Installation

### Prerequisites

- Docker and Docker Compose
- NVIDIA GPU with CUDA support (optional, for GPU acceleration)
- NVIDIA Container Toolkit (for GPU acceleration)

### Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/eapplymate.git
   cd eapplymate
   ```

2. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file with your credentials:
   ```
   LINKEDIN_USERNAME=your_linkedin_email@example.com
   LINKEDIN_PASSWORD=your_linkedin_password
   CAPTCHA_API_KEY=your_captcha_service_api_key
   ```

3. **Customize your configuration**:
   ```bash
   cp config/config.yaml.example config/config.yaml
   ```
   
   Edit `config/config.yaml` to customize job search parameters, browser settings, etc.

4. **Add your resume and cover letter**:
   - Place your resume in PDF format at `data/resume.pdf`
   - Place your base cover letter in PDF format at `data/base_cover_letter.pdf`

5. **Start the container**:
   ```bash
   docker-compose up -d
   ```

6. **Run the application**:
   ```bash
   docker exec -it job-application-ai python main.py
   ```

### Manual Installation

<details>
<summary>Click to expand manual installation instructions</summary>

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/eapplymate.git
   cd eapplymate
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

5. **Set up Ollama** (for local LLM processing):
   - Install Ollama from [ollama.ai](https://ollama.ai/)
   - Pull the Mistral model: `ollama pull mistral`

6. **Configure the application**:
   - Copy `.env.example` to `.env` and add your credentials
   - Copy `config/config.yaml.example` to `config/config.yaml` and customize

7. **Run the application**:
   ```bash
   python main.py
   ```
</details>

## Usage

### Basic Usage

Run the application with default settings:

```bash
python main.py
```

### Command Line Options

- **Skip cover letter generation**:
  ```bash
  python main.py --no-cover-letters
  ```

- **Force cover letter generation**:
  ```bash
  python main.py --cover-letters
  ```

### Testing Cover Letter Generation

Test the cover letter generation with a sample job:

```bash
python misc/tests/test_mistral_cover_letter.py
```

## Configuration

### Job Search Settings

Edit `config/config.yaml` to customize your job search:

```yaml
job_search:
  keywords: ["Software Engineer", "Python Developer", "Software Developer"]
  locations: ["Remote", "Montreal, QC", "Toronto, ON"]
  exclude_keywords: ["Senior", "10+ years", "Manager", "Lead", "Director"]
  min_salary: 80000  # in USD
  max_commute_distance: 25  # in miles
```

### LLM Settings

Configure the LLM for cover letter generation:

```yaml
llm:
  ollama_model: "mistral:latest"  # Model to use with Ollama
  max_workers: 3  # Maximum number of concurrent threads for cover letter generation
```

## GPU Acceleration

eApplyMate supports NVIDIA GPU acceleration for faster LLM inference.

### Prerequisites for GPU Acceleration

- NVIDIA GPU with CUDA support
- NVIDIA Container Toolkit (nvidia-docker2) installed
- Docker Compose version 1.28.0+

### Enabling GPU Acceleration

GPU acceleration is enabled by default in the Docker Compose configuration. The `deploy` section in `docker-compose.yml` configures GPU access:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### Running Without GPU (CPU-only mode)

If you don't have an NVIDIA GPU or the proper drivers installed, you can still run the application in CPU-only mode:

```bash
docker-compose -f docker-compose.yml -f docker-compose.cpu.yml up -d
```

Note that in CPU-only mode:
- LLM inference will be significantly slower
- Cover letter generation will take longer
- You may want to reduce the number of concurrent workers in config.yaml

### Verifying GPU Usage

You can verify that the GPU is being used by checking the GPU utilization:

```bash
nvidia-smi
```

## Project Structure

```
eApplyMate/
├── config/                 # Configuration files
├── data/                   # Data files (resume, cover letters)
├── logs/                   # Application logs
├── misc/                   # Miscellaneous utilities and tests
│   ├── benchmarks/         # Performance benchmarks
│   ├── tests/              # Test scripts
│   └── utils/              # Utility scripts
├── src/                    # Source code
│   ├── job_discovery.py    # Job discovery module
│   ├── cover_letter_generator.py  # Cover letter generation
│   ├── resume_customizer.py  # Resume customization
│   ├── application_submitter.py  # Application submission
│   ├── captcha_handler.py  # CAPTCHA handling
│   ├── llm_provider.py     # LLM integration
│   ├── utils.py            # Utility functions
│   └── config_helper.py    # Configuration helper
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore file
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker configuration
├── main.py                 # Main application entry point
├── README.md               # Project documentation
└── requirements.txt        # Python dependencies
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Ollama](https://ollama.ai/) for providing local LLM capabilities
- [Mistral AI](https://mistral.ai/) for the Mistral language model
- [Playwright](https://playwright.dev/) for browser automation
- [Docker](https://www.docker.com/) for containerization

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/SFarhatComp">Sami Farhat</a>
</p> 