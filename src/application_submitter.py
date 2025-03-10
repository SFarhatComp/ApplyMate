from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import random
from loguru import logger
import os

class ApplicationSubmitter:
    def __init__(self, config, captcha_handler):
        self.config = config
        self.captcha_handler = captcha_handler
    
    def submit_application(self, job, resume_path, cover_letter_path):
        """Submit job application through the job portal."""
        logger.info(f"Submitting application for {job['title']} at {job['company']}")
        
        if not job.get('url'):
            logger.error("No application URL provided")
            return False
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.config['browser']['headless']
            )
            context = browser.new_context(
                user_agent=self.config['browser']['user_agent'],
                viewport={'width': self.config['browser']['viewport_width'], 
                          'height': self.config['browser']['viewport_height']}
            )
            
            # Add human-like behavior
            self._add_human_behavior(context)
            
            page = context.new_page()
            
            try:
                # Navigate to job application page
                logger.info(f"Navigating to {job['url']}")
                page.goto(job['url'])
                page.wait_for_load_state("networkidle")
                
                # Detect application form type
                if "linkedin.com" in job['url']:
                    success = self._apply_linkedin(page, job, resume_path, cover_letter_path)
                elif "indeed.com" in job['url']:
                    success = self._apply_indeed(page, job, resume_path, cover_letter_path)
                else:
                    success = self._apply_generic(page, job, resume_path, cover_letter_path)
                
                if success:
                    logger.success(f"Successfully submitted application to {job['company']}")
                else:
                    logger.warning(f"Could not complete application for {job['company']}")
                
                return success
                
            except Exception as e:
                logger.error(f"Error submitting application: {str(e)}")
                # Take screenshot of error
                page.screenshot(path=f"logs/error_{job['company'].replace(' ', '_')}_{int(time.time())}.png")
                return False
            finally:
                browser.close()
    
    def _add_human_behavior(self, context):
        """Add human-like behavior to browser context."""
        # Add random mouse movements and delays
        context.route("**/*", lambda route: self._human_interaction(route))
    
    def _human_interaction(self, route):
        """Simulate human interaction patterns."""
        # Continue with the request
        route.continue_()
        # Add random delay to simulate human thinking
        if random.random() < 0.3:  # 30% chance of delay
            time.sleep(random.uniform(0.5, 2.0))
    
    def _apply_linkedin(self, page, job, resume_path, cover_letter_path):
        """Apply to job on LinkedIn."""
        try:
            # Check if we need to log in
            if page.query_selector(".artdeco-button__text:has-text('Sign in')"):
                logger.info("LinkedIn login required")
                page.click(".artdeco-button__text:has-text('Sign in')")
                page.wait_for_selector("#username")
                
                # Login
                page.fill("#username", self.config['job_boards']['linkedin']['username'])
                page.fill("#password", self.config['job_boards']['linkedin']['password'])
                page.click("button[type='submit']")
                page.wait_for_load_state("networkidle")
            
            # Look for Easy Apply button
            easy_apply_button = page.query_selector("button.jobs-apply-button")
            if easy_apply_button:
                logger.info("Found Easy Apply button")
                easy_apply_button.click()
                page.wait_for_selector(".jobs-easy-apply-content")
                
                # Handle multi-step application
                while True:
                    # Check for next button
                    next_button = page.query_selector("button.artdeco-button--primary:has-text('Next')")
                    submit_button = page.query_selector("button.artdeco-button--primary:has-text('Submit application')")
                    
                    if submit_button:
                        logger.info("Found Submit button - completing application")
                        submit_button.click()
                        page.wait_for_selector(".artdeco-modal__dismiss", timeout=10000)
                        page.click(".artdeco-modal__dismiss")
                        return True
                    
                    if next_button:
                        # Fill in any visible form fields
                        self._fill_linkedin_form(page, job, resume_path, cover_letter_path)
                        
                        # Click Next
                        logger.info("Clicking Next button")
                        next_button.click()
                        page.wait_for_load_state("networkidle")
                        time.sleep(random.uniform(1, 2))
                    else:
                        # No next or submit button found
                        logger.warning("Could not find Next or Submit button")
                        return False
            else:
                logger.warning("No Easy Apply button found")
                return False
                
        except Exception as e:
            logger.error(f"Error in LinkedIn application: {str(e)}")
            return False
    
    def _fill_linkedin_form(self, page, job, resume_path, cover_letter_path):
        """Fill in LinkedIn application form fields."""
        try:
            # Check for resume upload
            resume_upload = page.query_selector('input[type="file"]')
            if resume_upload:
                logger.info("Uploading resume")
                resume_upload.set_input_files(resume_path)
                time.sleep(random.uniform(1, 2))
            
            # Check for common form fields
            self._fill_form_field(page, '#email-address', self.config['user']['email'])
            self._fill_form_field(page, '#phone-number', self.config['user']['phone'])
            
            # Check for cover letter text area
            cover_letter_field = page.query_selector('textarea[name="coverLetter"]')
            if cover_letter_field:
                logger.info("Adding cover letter")
                with open(cover_letter_path, 'r') as f:
                    cover_letter_text = f.read()
                cover_letter_field.fill(cover_letter_text)
                time.sleep(random.uniform(1, 2))
            
            # Handle any CAPTCHA if present
            if page.query_selector('.captcha-container'):
                logger.info("CAPTCHA detected")
                self.captcha_handler.solve_captcha(page)
            
        except Exception as e:
            logger.error(f"Error filling LinkedIn form: {str(e)}")
    
    def _apply_indeed(self, page, job, resume_path, cover_letter_path):
        """Apply to job on Indeed."""
        try:
            # Check for Apply button
            apply_button = page.query_selector('button:has-text("Apply now")')
            if apply_button:
                logger.info("Found Apply button")
                apply_button.click()
                page.wait_for_load_state("networkidle")
                
                # Check if we need to log in
                if page.query_selector('#login-email-input'):
                    logger.info("Indeed login required")
                    page.fill('#login-email-input', self.config['user']['email'])
                    page.fill('#login-password-input', self.config['user']['password'])
                    page.click('button[type="submit"]')
                    page.wait_for_load_state("networkidle")
                
                # Fill application form
                self._fill_indeed_form(page, job, resume_path, cover_letter_path)
                
                # Look for continue/submit buttons
                continue_button = page.query_selector('button:has-text("Continue")')
                submit_button = page.query_selector('button:has-text("Submit")')
                
                if submit_button:
                    logger.info("Submitting application")
                    submit_button.click()
                    page.wait_for_load_state("networkidle")
                    return True
                elif continue_button:
                    logger.info("Continuing application")
                    continue_button.click()
                    page.wait_for_load_state("networkidle")
                    # Recursively handle multi-page applications
                    return self._apply_indeed(page, job, resume_path, cover_letter_path)
                else:
                    logger.warning("Could not find Continue or Submit button")
                    return False
            else:
                logger.warning("No Apply button found")
                return False
                
        except Exception as e:
            logger.error(f"Error in Indeed application: {str(e)}")
            return False
    
    def _fill_indeed_form(self, page, job, resume_path, cover_letter_path):
        """Fill in Indeed application form fields."""
        try:
            # Check for resume upload
            resume_upload = page.query_selector('input[type="file"]')
            if resume_upload:
                logger.info("Uploading resume")
                resume_upload.set_input_files(resume_path)
                time.sleep(random.uniform(1, 2))
            
            # Check for common form fields
            self._fill_form_field(page, 'input[name="name"]', self.config['user']['name'])
            self._fill_form_field(page, 'input[name="email"]', self.config['user']['email'])
            self._fill_form_field(page, 'input[name="phoneNumber"]', self.config['user']['phone'])
            
            # Check for cover letter text area
            cover_letter_field = page.query_selector('textarea[name="coverLetter"]')
            if cover_letter_field:
                logger.info("Adding cover letter")
                with open(cover_letter_path, 'r') as f:
                    cover_letter_text = f.read()
                cover_letter_field.fill(cover_letter_text)
                time.sleep(random.uniform(1, 2))
            
            # Handle any CAPTCHA if present
            if page.query_selector('.g-recaptcha'):
                logger.info("CAPTCHA detected")
                self.captcha_handler.solve_captcha(page)
            
        except Exception as e:
            logger.error(f"Error filling Indeed form: {str(e)}")
    
    def _apply_generic(self, page, job, resume_path, cover_letter_path):
        """Apply to job on a generic job board."""
        try:
            # Look for common application buttons
            apply_buttons = [
                'button:has-text("Apply")',
                'a:has-text("Apply")',
                'button:has-text("Apply Now")',
                'a:has-text("Apply Now")',
                'input[type="submit"][value="Apply"]'
            ]
            
            for button_selector in apply_buttons:
                apply_button = page.query_selector(button_selector)
                if apply_button:
                    logger.info(f"Found Apply button: {button_selector}")
                    apply_button.click()
                    page.wait_for_load_state("networkidle")
                    break
            
            # Look for common form fields
            self._fill_form_field(page, 'input[name="name"], input[name="fullName"], input[id="name"]', self.config['user']['name'])
            self._fill_form_field(page, 'input[name="email"], input[type="email"], input[id="email"]', self.config['user']['email'])
            self._fill_form_field(page, 'input[name="phone"], input[type="tel"], input[id="phone"]', self.config['user']['phone'])
            
            # Check for resume upload
            resume_selectors = [
                'input[type="file"][name="resume"]',
                'input[type="file"][accept=".pdf,.doc,.docx"]',
                'input[type="file"]'
            ]
            
            for selector in resume_selectors:
                resume_upload = page.query_selector(selector)
                if resume_upload:
                    logger.info("Uploading resume")
                    resume_upload.set_input_files(resume_path)
                    time.sleep(random.uniform(1, 2))
                    break
            
            # Check for cover letter upload or text area
            cover_letter_selectors = [
                'textarea[name="coverLetter"]',
                'textarea[placeholder*="cover letter"]',
                'input[type="file"][name="coverLetter"]'
            ]
            
            for selector in cover_letter_selectors:
                cover_letter_field = page.query_selector(selector)
                if cover_letter_field:
                    logger.info("Adding cover letter")
                    if 'input[type="file"]' in selector:
                        cover_letter_field.set_input_files(cover_letter_path)
                    else:
                        with open(cover_letter_path, 'r') as f:
                            cover_letter_text = f.read()
                        cover_letter_field.fill(cover_letter_text)
                    time.sleep(random.uniform(1, 2))
                    break
            
            # Look for submit button
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Submit")',
                'button:has-text("Apply")',
                'a:has-text("Submit Application")'
            ]
            
            for selector in submit_selectors:
                submit_button = page.query_selector(selector)
                if submit_button:
                    logger.info(f"Found Submit button: {selector}")
                    submit_button.click()
                    page.wait_for_load_state("networkidle")
                    return True
            
            logger.warning("Could not find Submit button")
            return False
                
        except Exception as e:
            logger.error(f"Error in generic application: {str(e)}")
            return False
    
    def _fill_form_field(self, page, selector, value):
        """Fill in a form field if it exists and is empty."""
        try:
            field = page.query_selector(selector)
            if field:
                # Check if field is empty
                current_value = field.evaluate('el => el.value')
                if not current_value:
                    logger.info(f"Filling field: {selector}")
                    field.fill(value)
                    time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            logger.error(f"Error filling form field {selector}: {str(e)}")
