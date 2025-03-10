import requests
from bs4 import BeautifulSoup
import time
import random
from loguru import logger
from playwright.sync_api import sync_playwright
import json
import os

class JobDiscovery:
    def __init__(self, config):
        self.config = config
        self.job_listings = []
        
    def find_jobs(self):
        """Find job listings based on search criteria."""
        logger.info("Searching jobs on linkedin...")
        self._search_linkedin()
        
        # Filter jobs based on criteria
        filtered_jobs = self.filter_jobs()
        logger.info(f"Found {len(filtered_jobs)} jobs after filtering")
        
        return filtered_jobs
        
    def _search_linkedin(self):
        """Search jobs on LinkedIn with direct URL visits."""
        job_count = 0
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.config['browser']['headless']
            )
            context = browser.new_context(
                user_agent=self.config['browser']['user_agent'],
                viewport={'width': self.config['browser']['viewport_width'], 
                          'height': self.config['browser']['viewport_height']}
            )
            page = context.new_page()
            
            try:
                # Log in to LinkedIn
                logger.info("Logging in to LinkedIn...")
                page.goto("https://www.linkedin.com/login")
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                
                # Check if already logged in
                if "feed" in page.url or "checkpoint" in page.url or "dashboard" in page.url:
                    logger.info("Already logged in to LinkedIn")
                else:
                    # Fill login form
                    page.fill("#username", self.config['job_boards']['linkedin']['username'])
                    page.fill("#password", self.config['job_boards']['linkedin']['password'])
                    
                    # Submit login form
                    with page.expect_navigation(timeout=10000):
                        page.click("button[type='submit']")
                    
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                
                # Save screenshot for debugging
                os.makedirs("logs", exist_ok=True)
                page.screenshot(path="logs/linkedin_after_login.png")
                
                # Search for jobs with all keywords at once
                all_keywords = " OR ".join(self.config['job_search']['keywords'])
                
                # Process each location
                for location in self.config['job_search']['locations']:
                    if job_count >= 10:
                        break
                        
                    # Format search URL
                    search_url = f"https://www.linkedin.com/jobs/search/?keywords={all_keywords.replace(' ', '%20')}&location={location.replace(' ', '%20')}&f_TPR=r86400"
                    logger.info(f"Searching jobs in {location}")
                    
                    # Navigate to search URL
                    page.goto(search_url)
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                    
                    # Save screenshot for debugging
                    page.screenshot(path=f"logs/linkedin_search_{location}.png")
                    
                    # Scroll to load more jobs
                    logger.info("Loading more jobs...")
                    for _ in range(3):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(1000)
                    
                    # Extract job URLs only
                    job_urls = page.evaluate("""() => {
                        const links = Array.from(document.querySelectorAll('a[href*="/jobs/view/"]'));
                        return links.slice(0, 5).map(link => link.href);
                    }""")
                    
                    logger.info(f"Found {len(job_urls)} job URLs")
                    
                    # Visit each job URL to get details
                    for url in job_urls:
                        if job_count >= 10:
                            break
                        
                        # Clean the URL to remove tracking parameters
                        base_url = url.split('?')[0]
                        job_id = base_url.split('/view/')[1].replace('/', '')
                        
                        clean_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
                        logger.info(f"Visiting job URL: {clean_url}")
                        
                        # Navigate to job page
                        page.goto(clean_url)
                        page.wait_for_load_state("domcontentloaded", timeout=10000)
                        
                        # Extract job details directly from the job page
                        job_details = page.evaluate("""() => {
                            // Get job title
                            const titleElement = document.querySelector('.job-details-jobs-unified-top-card__job-title');
                            const title = titleElement ? titleElement.textContent.trim() : '';
                            
                            // Get company name
                            const companyElement = document.querySelector('.job-details-jobs-unified-top-card__company-name');
                            const company = companyElement ? companyElement.textContent.trim() : '';
                            
                            // Get location
                            const locationElement = document.querySelector('.job-details-jobs-unified-top-card__bullet');
                            const location = locationElement ? locationElement.textContent.trim() : '';
                            
                            // Get job description with better formatting
                            const descriptionElement = document.querySelector('.jobs-description__content');
                            let description = '';
                            
                            if (descriptionElement) {
                                // Process the description to maintain formatting
                                const processNode = (node, level = 0) => {
                                    let text = '';
                                    
                                    // Process each child node
                                    for (const child of node.childNodes) {
                                        if (child.nodeType === Node.TEXT_NODE) {
                                            // Text node - add its content
                                            const content = child.textContent.trim();
                                            if (content) {
                                                text += content + ' ';
                                            }
                                        } else if (child.nodeType === Node.ELEMENT_NODE) {
                                            // Element node - process based on tag
                                            const tagName = child.tagName.toLowerCase();
                                            
                                            if (tagName === 'br') {
                                                // Line break
                                                text += '\\n';
                                            } else if (tagName === 'p') {
                                                // Paragraph - add with newlines
                                                const paraText = processNode(child, level + 1);
                                                if (paraText.trim()) {
                                                    text += '\\n\\n' + paraText + '\\n';
                                                }
                                            } else if (tagName === 'ul' || tagName === 'ol') {
                                                // List - process each item
                                                text += '\\n';
                                                let i = 1;
                                                for (const li of child.querySelectorAll('li')) {
                                                    const itemText = processNode(li, level + 1).trim();
                                                    if (itemText) {
                                                        text += `\\n${tagName === 'ol' ? i++ + '.' : '•'} ${itemText}`;
                                                    }
                                                }
                                                text += '\\n';
                                            } else if (tagName === 'h1' || tagName === 'h2' || tagName === 'h3' || tagName === 'h4') {
                                                // Heading - add with emphasis
                                                const headingText = processNode(child, level + 1).trim();
                                                if (headingText) {
                                                    text += `\\n\\n${headingText}\\n`;
                                                }
                                            } else if (tagName === 'strong' || tagName === 'b') {
                                                // Bold text
                                                const boldText = processNode(child, level + 1).trim();
                                                if (boldText) {
                                                    text += boldText + ' ';
                                                }
                                            } else {
                                                // Other elements - process recursively
                                                text += processNode(child, level + 1);
                                            }
                                        }
                                    }
                                    
                                    return text;
                                };
                                
                                description = processNode(descriptionElement).trim();
                                
                                // Clean up multiple newlines and spaces
                                description = description.replace(/\\n\\s*\\n\\s*\\n/g, '\\n\\n');
                                description = description.replace(/\\s+/g, ' ').replace(/\\s*\\n\\s*/g, '\\n');
                            }
                            
                            return {
                                title: title || 'Unknown Title',
                                company: company || 'Unknown Company',
                                location: location || '',
                                description: description || ''
                            };
                        }""")
                        
                        # Create job object
                        job = {
                            'title': job_details.get('title', 'Unknown Title'),
                            'company': job_details.get('company', 'Unknown Company'),
                            'location': job_details.get('location', location),
                            'url': clean_url,
                            'source': 'linkedin',
                            'id': job_id,
                            'description': job_details.get('description', '').replace('\\n', '\n')
                        }
                        
                        # Add job to list
                        self.job_listings.append(job)
                        job_count += 1
                        logger.info(f"Added job #{job_count}: {job['title']} at {job['company']}")
                    
                    # Short delay between locations
                    time.sleep(2)
                
                logger.info(f"Found {job_count} jobs on LinkedIn")
                
            except Exception as e:
                logger.error(f"Error in LinkedIn job search: {str(e)}")
                import traceback
                logger.debug(f"Stack trace: {traceback.format_exc()}")
            
            finally:
                browser.close()
    
    def filter_jobs(self):
        """Filter job listings based on criteria."""
        filtered_jobs = []
        
        # Get filter criteria from config
        exclude_keywords = self.config['job_search'].get('exclude_keywords', [])
        
        for job in self.job_listings:
            # Check if job should be excluded based on keywords
            should_exclude = False
            
            for keyword in exclude_keywords:
                if keyword.lower() in job['title'].lower():
                    logger.debug(f"Excluding job {job['title']} due to keyword: {keyword}")
                    should_exclude = True
                    break
            
            if not should_exclude:
                filtered_jobs.append(job)
        
        return filtered_jobs
    
    def export_jobs_to_file(self, file_path="found_jobs.json"):
        """Export the found jobs to a JSON file with proper formatting."""
        try:
            # Create a copy of job listings with cleaned descriptions
            export_listings = []
            for job in self.job_listings:
                job_copy = job.copy()
                
                # Ensure description is properly formatted
                if 'description' in job_copy and job_copy['description']:
                    # Remove excessive newlines and whitespace
                    desc = job_copy['description']
                    desc = '\n'.join(line.strip() for line in desc.split('\n'))
                    desc = desc.replace('\n\n\n', '\n\n')
                    job_copy['description'] = desc
                
                export_listings.append(job_copy)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_listings, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(self.job_listings)} jobs to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting jobs to file: {str(e)}")
            return False    
    def _debug_job_card(self, card, location, index):
        """Save detailed debug information about a job card."""
        try:
            # Create debug directory
            debug_dir = "logs/debug_cards"
            os.makedirs(debug_dir, exist_ok=True)
            
            # Save screenshot of the card
            try:
                card_box = card.bounding_box()
                if card_box:
                    page = card.page
                    page.screenshot(path=f"{debug_dir}/card_{location}_{index}.png", clip=card_box)
            except Exception as e:
                logger.error(f"Error taking screenshot: {str(e)}")
            
            # Save HTML of the card
            try:
                html = card.evaluate("el => el.outerHTML")
                with open(f"{debug_dir}/card_{location}_{index}.html", "w", encoding="utf-8") as f:
                    f.write(html)
            except Exception as e:
                logger.error(f"Error saving HTML: {str(e)}")
            
            # Log all attributes
            try:
                attrs = card.evaluate("""el => {
                    const result = {};
                    for (const attr of el.attributes) {
                        result[attr.name] = attr.value;
                    }
                    return result;
                }""")
                with open(f"{debug_dir}/card_{location}_{index}_attrs.json", "w", encoding="utf-8") as f:
                    json.dump(attrs, f, indent=2)
            except Exception as e:
                logger.error(f"Error logging attributes: {str(e)}")
            
            # Try to extract text content of all elements
            try:
                text_content = card.evaluate("""el => {
                    const result = {};
                    const allElements = el.querySelectorAll('*');
                    for (const elem of allElements) {
                        if (elem.id) {
                            result['#' + elem.id] = elem.textContent.trim();
                        }
                        if (elem.className) {
                            const classes = elem.className.split(' ');
                            for (const cls of classes) {
                                if (cls) {
                                    result['.' + cls] = elem.textContent.trim();
                                }
                            }
                        }
                    }
                    return result;
                }""")
                with open(f"{debug_dir}/card_{location}_{index}_text.json", "w", encoding="utf-8") as f:
                    json.dump(text_content, f, indent=2)
            except Exception as e:
                logger.error(f"Error extracting text content: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error in debug_job_card: {str(e)}")
