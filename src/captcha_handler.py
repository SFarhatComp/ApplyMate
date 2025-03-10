import time
import os
from loguru import logger
from twocaptcha import TwoCaptcha
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless

class CaptchaHandler:
    def __init__(self, config):
        self.config = config
        self.service = config['captcha']['service']
        self.api_key = config['captcha']['api_key']
    
    def solve_captcha(self, page):
        """Solve CAPTCHA on the current page."""
        if self.service == "none" or not self.api_key:
            logger.warning("No CAPTCHA service configured. Manual intervention required.")
            # Wait for manual intervention
            logger.info("Waiting 30 seconds for manual CAPTCHA solving...")
            time.sleep(30)
            return
        
        try:
            # Detect CAPTCHA type
            if page.query_selector('.g-recaptcha'):
                logger.info("Detected reCAPTCHA")
                return self._solve_recaptcha(page)
            elif page.query_selector('iframe[src*="hcaptcha"]'):
                logger.info("Detected hCaptcha")
                return self._solve_hcaptcha(page)
            else:
                logger.warning("Unknown CAPTCHA type")
                return False
        except Exception as e:
            logger.error(f"Error solving CAPTCHA: {str(e)}")
            return False
    
    def _solve_recaptcha(self, page):
        """Solve Google reCAPTCHA."""
        try:
            # Get site key
            site_key = page.evaluate('''() => {
                const recaptchaElement = document.querySelector('.g-recaptcha');
                return recaptchaElement ? recaptchaElement.getAttribute('data-sitekey') : null;
            }''')
            
            if not site_key:
                logger.error("Could not find reCAPTCHA site key")
                return False
            
            # Get page URL
            page_url = page.url
            
            # Solve using selected service
            if self.service == "2captcha":
                return self._solve_with_2captcha(page, site_key, page_url)
            elif self.service == "anticaptcha":
                return self._solve_with_anticaptcha(page, site_key, page_url)
            else:
                logger.error(f"Unsupported CAPTCHA service: {self.service}")
                return False
                
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA: {str(e)}")
            return False
    
    def _solve_with_2captcha(self, page, site_key, page_url):
        """Solve CAPTCHA using 2Captcha service."""
        try:
            solver = TwoCaptcha(self.api_key)
            logger.info(f"Sending reCAPTCHA to 2Captcha: {site_key}")
            
            result = solver.recaptcha(
                sitekey=site_key,
                url=page_url
            )
            
            if result and 'code' in result:
                g_response = result['code']
                logger.success("2Captcha solved the reCAPTCHA")
                
                # Insert the solution
                page.evaluate(f'''(response) => {{
                    document.querySelector('#g-recaptcha-response').innerHTML = response;
                    captchaCallback(response);
                }}''', g_response)
                
                return True
            else:
                logger.error("2Captcha failed to solve the reCAPTCHA")
                return False
                
        except Exception as e:
            logger.error(f"Error with 2Captcha: {str(e)}")
            return False
    
    def _solve_with_anticaptcha(self, page, site_key, page_url):
        """Solve CAPTCHA using Anti-Captcha service."""
        try:
            solver = recaptchaV2Proxyless()
            solver.set_verbose(1)
            solver.set_key(self.api_key)
            solver.set_website_url(page_url)
            solver.set_website_key(site_key)
            
            logger.info(f"Sending reCAPTCHA to Anti-Captcha: {site_key}")
            g_response = solver.solve_and_return_solution()
            
            if g_response:
                logger.success("Anti-Captcha solved the reCAPTCHA")
                
                # Insert the solution
                page.evaluate(f'''(response) => {{
                    document.querySelector('#g-recaptcha-response').innerHTML = response;
                    captchaCallback(response);
                }}''', g_response)
                
                return True
            else:
                logger.error("Anti-Captcha failed to solve the reCAPTCHA")
                return False
                
        except Exception as e:
            logger.error(f"Error with Anti-Captcha: {str(e)}")
            return False
    
    def _solve_hcaptcha(self, page):
        """Solve hCaptcha."""
        # Implementation similar to reCAPTCHA but for hCaptcha
        logger.warning("hCaptcha solving not fully implemented")
        return False 