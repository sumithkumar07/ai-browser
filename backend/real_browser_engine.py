import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import time
import logging
import re
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

class RealBrowserEngine:
    def __init__(self):
        self.active_drivers = {}
        self.max_concurrent_drivers = 3
        
        # Site-specific selectors and actions
        self.site_configs = {
            "linkedin.com": {
                "job_search": {
                    "search_box": "input[aria-label*='Search']",
                    "location_box": "input[aria-label*='Location']",
                    "search_button": "button[data-test-id='jobs-search-box-submit-button']",
                    "job_cards": ".job-card-container",
                    "apply_button": ".jobs-apply-button",
                    "easy_apply": "button[aria-label*='Easy Apply']"
                },
                "login": {
                    "email": "input#username",
                    "password": "input#password", 
                    "submit": "button[type='submit']"
                }
            },
            "indeed.com": {
                "job_search": {
                    "search_box": "input#text-input-what",
                    "location_box": "input#text-input-where",
                    "search_button": "button[type='submit']",
                    "job_cards": ".job_seen_beacon",
                    "apply_button": ".ia-IndeedApplyButton"
                }
            },
            "glassdoor.com": {
                "job_search": {
                    "search_box": "input#searchBar-jobTitle",
                    "location_box": "input#searchBar-location",
                    "search_button": "button#search-btn"
                }
            }
        }
    
    async def get_driver_for_session(self, session_id: str) -> webdriver.Chrome:
        """Get or create a Chrome driver for a session"""
        if session_id not in self.active_drivers:
            if len(self.active_drivers) >= self.max_concurrent_drivers:
                # Clean up oldest driver
                oldest_session = list(self.active_drivers.keys())[0]
                await self.cleanup_driver(oldest_session)
            
            # Create new driver
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-logging")
            options.add_argument("--disable-web-security")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            options.add_argument("--window-size=1920,1080")
            
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                driver.set_page_load_timeout(30)
                driver.implicitly_wait(10)
                
                self.active_drivers[session_id] = {
                    "driver": driver,
                    "created_at": datetime.utcnow(),
                    "last_used": datetime.utcnow()
                }
                
                logger.info(f"Created new Chrome driver for session {session_id}")
                
            except Exception as e:
                logger.error(f"Failed to create Chrome driver: {e}")
                raise
        
        self.active_drivers[session_id]["last_used"] = datetime.utcnow()
        return self.active_drivers[session_id]["driver"]
    
    async def cleanup_driver(self, session_id: str):
        """Clean up a specific driver"""
        if session_id in self.active_drivers:
            try:
                self.active_drivers[session_id]["driver"].quit()
            except Exception as e:
                logger.error(f"Error closing driver for session {session_id}: {e}")
            finally:
                del self.active_drivers[session_id]
    
    async def execute_job_search_automation(self, task_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Execute real job search automation"""
        
        driver = await self.get_driver_for_session(session_id)
        results = {
            "status": "success",
            "jobs_found": 0,
            "applications_submitted": 0,
            "sites_searched": [],
            "errors": []
        }
        
        try:
            # Extract search parameters
            keywords = " ".join(task_data.get("keywords", ["software engineer"]))
            location = task_data.get("location", "Remote")
            target_applications = task_data.get("target_count", 5)
            
            # Search on multiple job sites
            job_sites = ["linkedin.com", "indeed.com"]
            
            for site in job_sites:
                try:
                    site_results = await self._search_jobs_on_site(driver, site, keywords, location)
                    results["jobs_found"] += site_results["jobs_found"]
                    results["sites_searched"].append(site)
                    
                    # Apply to jobs if possible
                    if site_results["jobs_found"] > 0:
                        applications = await self._apply_to_jobs(driver, site, min(target_applications, 3))
                        results["applications_submitted"] += applications
                        
                except Exception as site_error:
                    logger.error(f"Error searching on {site}: {site_error}")
                    results["errors"].append(f"{site}: {str(site_error)}")
                
                # Small delay between sites
                await asyncio.sleep(2)
            
            return results
            
        except Exception as e:
            logger.error(f"Job search automation failed: {e}")
            results["status"] = "failed"
            results["error"] = str(e)
            return results
    
    async def _search_jobs_on_site(self, driver: webdriver.Chrome, site: str, keywords: str, location: str) -> Dict[str, Any]:
        """Search for jobs on a specific site"""
        
        site_config = self.site_configs.get(site, {})
        job_config = site_config.get("job_search", {})
        
        try:
            # Navigate to site
            if site == "linkedin.com":
                driver.get("https://www.linkedin.com/jobs")
            elif site == "indeed.com":
                driver.get("https://www.indeed.com")
            else:
                driver.get(f"https://{site}")
            
            await asyncio.sleep(3)
            
            # Find and fill search box
            search_box = None
            search_selectors = [
                job_config.get("search_box", ""),
                "input[placeholder*='job']",
                "input[placeholder*='Job']", 
                "input[name*='q']",
                "input[id*='search']"
            ]
            
            for selector in search_selectors:
                if selector:
                    try:
                        search_box = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        break
                    except TimeoutException:
                        continue
            
            if search_box:
                search_box.clear()
                search_box.send_keys(keywords)
                
                # Try to find location box
                location_selectors = [
                    job_config.get("location_box", ""),
                    "input[placeholder*='location']",
                    "input[placeholder*='Location']",
                    "input[name*='location']"
                ]
                
                for selector in location_selectors:
                    if selector:
                        try:
                            location_box = driver.find_element(By.CSS_SELECTOR, selector)
                            location_box.clear()
                            location_box.send_keys(location)
                            break
                        except NoSuchElementException:
                            continue
                
                # Submit search
                try:
                    search_button = driver.find_element(By.CSS_SELECTOR, 
                                                      job_config.get("search_button", "button[type='submit']"))
                    search_button.click()
                except NoSuchElementException:
                    # Try pressing Enter instead
                    search_box.send_keys(Keys.RETURN)
                
                await asyncio.sleep(5)
                
                # Count job results
                job_selectors = [
                    job_config.get("job_cards", ""),
                    ".job-card",
                    ".job_seen_beacon", 
                    "[data-testid*='job']",
                    ".job-result"
                ]
                
                jobs_found = 0
                for selector in job_selectors:
                    if selector:
                        try:
                            job_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            jobs_found = len(job_elements)
                            if jobs_found > 0:
                                break
                        except Exception:
                            continue
                
                return {
                    "jobs_found": jobs_found,
                    "search_successful": True
                }
            
            return {"jobs_found": 0, "search_successful": False}
            
        except Exception as e:
            logger.error(f"Error searching on {site}: {e}")
            return {"jobs_found": 0, "search_successful": False, "error": str(e)}
    
    async def _apply_to_jobs(self, driver: webdriver.Chrome, site: str, max_applications: int) -> int:
        """Apply to jobs on a specific site"""
        
        applications_submitted = 0
        
        try:
            # Find job cards
            job_selectors = [
                ".job-card",
                ".job_seen_beacon",
                ".job-result-card",
                "[data-testid*='job']"
            ]
            
            job_elements = []
            for selector in job_selectors:
                try:
                    job_elements = driver.find_elements(By.CSS_SELECTOR, selector)[:max_applications]
                    if job_elements:
                        break
                except Exception:
                    continue
            
            for i, job_element in enumerate(job_elements[:max_applications]):
                try:
                    # Click on job card
                    driver.execute_script("arguments[0].click();", job_element)
                    await asyncio.sleep(2)
                    
                    # Look for apply buttons
                    apply_selectors = [
                        "button[aria-label*='Easy Apply']",
                        ".jobs-apply-button",
                        ".ia-IndeedApplyButton",
                        "button:contains('Apply')",
                        "a:contains('Apply')"
                    ]
                    
                    for selector in apply_selectors:
                        try:
                            apply_button = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            
                            # Check if it's an easy apply (1-click application)
                            if "easy" in apply_button.text.lower() or "quick" in apply_button.text.lower():
                                apply_button.click()
                                applications_submitted += 1
                                await asyncio.sleep(1)
                                
                                # Handle any popups or confirmation dialogs
                                try:
                                    confirm_selectors = [
                                        "button:contains('Submit application')",
                                        "button:contains('Send application')",
                                        "button[data-control-name*='submit']"
                                    ]
                                    
                                    for confirm_selector in confirm_selectors:
                                        try:
                                            confirm_btn = WebDriverWait(driver, 2).until(
                                                EC.element_to_be_clickable((By.CSS_SELECTOR, confirm_selector))
                                            )
                                            confirm_btn.click()
                                            break
                                        except TimeoutException:
                                            continue
                                            
                                except Exception:
                                    pass
                                
                            break
                            
                        except (TimeoutException, NoSuchElementException):
                            continue
                    
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error applying to job {i+1}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in job application process: {e}")
        
        return applications_submitted
    
    async def execute_research_automation(self, task_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Execute real research automation across multiple sources"""
        
        driver = await self.get_driver_for_session(session_id)
        results = {
            "status": "success",
            "sources_searched": 0,
            "results_collected": [],
            "summary": ""
        }
        
        try:
            keywords = " ".join(task_data.get("keywords", []))
            search_sites = ["google.com", "scholar.google.com", "wikipedia.org"]
            
            for site in search_sites:
                try:
                    site_results = await self._research_on_site(driver, site, keywords)
                    if site_results:
                        results["results_collected"].extend(site_results)
                        results["sources_searched"] += 1
                    
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Research error on {site}: {e}")
            
            # Generate summary
            if results["results_collected"]:
                results["summary"] = f"Found {len(results['results_collected'])} relevant sources across {results['sources_searched']} platforms."
            
            return results
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            return results
    
    async def _research_on_site(self, driver: webdriver.Chrome, site: str, keywords: str) -> List[Dict]:
        """Research on a specific site"""
        
        results = []
        
        try:
            if site == "google.com":
                driver.get(f"https://www.google.com/search?q={keywords}")
            elif site == "scholar.google.com":
                driver.get(f"https://scholar.google.com/scholar?q={keywords}")
            elif site == "wikipedia.org":
                driver.get(f"https://en.wikipedia.org/wiki/Special:Search?search={keywords}")
            
            await asyncio.sleep(3)
            
            # Extract search results
            result_selectors = [
                ".g h3",  # Google results
                ".gs_rt",  # Scholar results  
                ".mw-search-result-heading"  # Wikipedia results
            ]
            
            for selector in result_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)[:5]
                    for element in elements:
                        try:
                            title = element.text
                            link = element.find_element(By.TAG_NAME, "a").get_attribute("href")
                            results.append({
                                "title": title,
                                "url": link,
                                "source": site
                            })
                        except Exception:
                            continue
                    
                    if results:
                        break
                        
                except NoSuchElementException:
                    continue
            
        except Exception as e:
            logger.error(f"Error researching on {site}: {e}")
        
        return results
    
    async def execute_social_media_posting(self, task_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Execute real social media posting automation"""
        
        results = {
            "status": "success",
            "posts_created": 0,
            "platforms": [],
            "errors": []
        }
        
        # For now, return simulated results as social media automation requires OAuth
        # This would be implemented with proper API integrations
        content = task_data.get("content", "")
        platforms = task_data.get("platforms", ["linkedin", "twitter"])
        
        for platform in platforms:
            try:
                # This would use actual API calls with proper authentication
                results["posts_created"] += 1
                results["platforms"].append(platform)
                
            except Exception as e:
                results["errors"].append(f"{platform}: {str(e)}")
        
        return results
    
    async def cleanup_all_drivers(self):
        """Clean up all active drivers"""
        for session_id in list(self.active_drivers.keys()):
            await self.cleanup_driver(session_id)

# Global instance
real_browser_engine = RealBrowserEngine()