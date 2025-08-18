# Phase 2: Enhanced Native Browser Engine
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import uuid
import httpx
from bs4 import BeautifulSoup
import base64
from urllib.parse import urljoin, urlparse
import re

logger = logging.getLogger(__name__)

class BrowserAction:
    """Represents a browser action for automation"""
    
    def __init__(self, action_type: str, target: str = "", value: str = "", options: Dict = None):
        self.action_type = action_type
        self.target = target
        self.value = value
        self.options = options or {}
        self.timestamp = datetime.utcnow()

class EnhancedNativeBrowserEngine:
    """
    Phase 2: Enhanced Native Browser Engine with WebView Integration
    Provides advanced browser automation capabilities within current iframe structure
    """
    
    def __init__(self):
        self.active_sessions = {}
        self.browser_cache = {}
        self.automation_scripts = {}
        self.page_screenshots = {}
        
    async def navigate_with_automation(self, url: str, actions: List[Dict[str, Any]] = None, wait_conditions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Navigate to URL with optional automation actions"""
        
        try:
            session_id = str(uuid.uuid4())
            
            # Create browser session
            session = {
                "session_id": session_id,
                "current_url": url,
                "started_at": datetime.utcnow(),
                "actions_performed": [],
                "screenshots": [],
                "page_data": None,
                "automation_state": "running"
            }
            
            self.active_sessions[session_id] = session
            
            # Fetch page content
            page_result = await self._fetch_enhanced_page_content(url)
            session["page_data"] = page_result
            
            # Perform automation actions if provided
            if actions:
                automation_result = await self._execute_automation_actions(session_id, actions)
                session["automation_result"] = automation_result
            
            # Check wait conditions
            if wait_conditions:
                wait_result = await self._check_wait_conditions(session_id, wait_conditions)
                session["wait_result"] = wait_result
            
            session["automation_state"] = "completed"
            session["completed_at"] = datetime.utcnow()
            
            return {
                "success": True,
                "session_id": session_id,
                "url": url,
                "page_data": page_result,
                "automation_completed": bool(actions),
                "actions_count": len(actions) if actions else 0,
                "execution_time": (session["completed_at"] - session["started_at"]).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Enhanced navigation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    async def _fetch_enhanced_page_content(self, url: str) -> Dict[str, Any]:
        """Fetch page content with enhanced parsing"""
        
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': 'AETHER Enhanced Browser Engine/3.0 (+http://aether.browser)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Parse content with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Enhanced content extraction
                page_data = {
                    "url": url,
                    "title": self._extract_title(soup),
                    "meta_data": self._extract_meta_data(soup),
                    "content": self._extract_main_content(soup),
                    "interactive_elements": self._extract_interactive_elements(soup),
                    "navigation_structure": self._extract_navigation_structure(soup),
                    "forms": self._extract_forms(soup),
                    "media_elements": self._extract_media_elements(soup),
                    "links": self._extract_links(soup, url),
                    "scripts": self._extract_scripts(soup),
                    "styles": self._extract_styles(soup),
                    "page_structure": self._analyze_page_structure(soup),
                    "automation_targets": self._identify_automation_targets(soup),
                    "extracted_at": datetime.utcnow().isoformat(),
                    "content_hash": self._calculate_content_hash(response.text)
                }
                
                return page_data
                
        except Exception as e:
            logger.error(f"Enhanced page fetch failed for {url}: {e}")
            return {
                "url": url,
                "error": str(e),
                "extracted_at": datetime.utcnow().isoformat()
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title with fallbacks"""
        
        # Try title tag first
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        
        # Try og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        # Try h1 as fallback
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.get_text():
            return h1_tag.get_text().strip()
        
        return "Untitled Page"
    
    def _extract_meta_data(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract comprehensive meta data"""
        
        meta_data = {}
        
        # Standard meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            
            if name and content:
                meta_data[name] = content
        
        # Additional structured data
        meta_data.update({
            'charset': self._get_charset(soup),
            'viewport': self._get_viewport(soup),
            'canonical_url': self._get_canonical_url(soup),
            'language': self._get_language(soup)
        })
        
        return meta_data
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content with better filtering"""
        
        # Remove non-content elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            element.decompose()
        
        # Try to find main content area
        main_selectors = [
            'main', 'article', '[role="main"]', '.content', '#content',
            '.post-content', '.entry-content', '.article-content'
        ]
        
        main_content = None
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if main_content:
            text = main_content.get_text()
        else:
            # Fall back to body content
            text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = ' '.join(chunk for chunk in chunks if chunk)
        
        return clean_text[:10000]  # Limit to 10k characters
    
    def _extract_interactive_elements(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract interactive elements for automation"""
        
        elements = []
        
        # Buttons
        for button in soup.find_all(['button', 'input']):
            if button.name == 'input' and button.get('type') not in ['button', 'submit', 'reset']:
                continue
            
            element = {
                'type': 'button',
                'text': button.get_text().strip() or button.get('value', ''),
                'id': button.get('id'),
                'class': button.get('class'),
                'name': button.get('name'),
                'onclick': button.get('onclick'),
                'disabled': button.has_attr('disabled'),
                'form': button.get('form')
            }
            elements.append(element)
        
        # Links
        for link in soup.find_all('a', href=True):
            element = {
                'type': 'link',
                'text': link.get_text().strip(),
                'href': link.get('href'),
                'id': link.get('id'),
                'class': link.get('class'),
                'target': link.get('target'),
                'title': link.get('title')
            }
            elements.append(element)
        
        # Input fields
        for input_elem in soup.find_all('input'):
            if input_elem.get('type') in ['button', 'submit', 'reset']:
                continue
                
            element = {
                'type': 'input',
                'input_type': input_elem.get('type', 'text'),
                'name': input_elem.get('name'),
                'id': input_elem.get('id'),
                'placeholder': input_elem.get('placeholder'),
                'required': input_elem.has_attr('required'),
                'disabled': input_elem.has_attr('disabled'),
                'value': input_elem.get('value'),
                'form': input_elem.get('form')
            }
            elements.append(element)
        
        # Select elements
        for select in soup.find_all('select'):
            options = [{'value': opt.get('value'), 'text': opt.get_text().strip()} 
                      for opt in select.find_all('option')]
            
            element = {
                'type': 'select',
                'name': select.get('name'),
                'id': select.get('id'),
                'multiple': select.has_attr('multiple'),
                'required': select.has_attr('required'),
                'options': options,
                'form': select.get('form')
            }
            elements.append(element)
        
        # Textarea elements
        for textarea in soup.find_all('textarea'):
            element = {
                'type': 'textarea',
                'name': textarea.get('name'),
                'id': textarea.get('id'),
                'placeholder': textarea.get('placeholder'),
                'required': textarea.has_attr('required'),
                'disabled': textarea.has_attr('disabled'),
                'rows': textarea.get('rows'),
                'cols': textarea.get('cols'),
                'form': textarea.get('form')
            }
            elements.append(element)
        
        return elements
    
    def _extract_navigation_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract navigation structure"""
        
        navigation = {
            'primary_nav': [],
            'breadcrumbs': [],
            'footer_nav': [],
            'sidebar_nav': []
        }
        
        # Primary navigation
        nav_selectors = ['nav', '.navigation', '.navbar', '.menu', '#menu']
        for selector in nav_selectors:
            nav_elem = soup.select_one(selector)
            if nav_elem:
                links = nav_elem.find_all('a', href=True)
                navigation['primary_nav'] = [
                    {'text': link.get_text().strip(), 'href': link.get('href')}
                    for link in links
                ]
                break
        
        # Breadcrumbs
        breadcrumb_selectors = ['.breadcrumb', '.breadcrumbs', '[aria-label="breadcrumb"]']
        for selector in breadcrumb_selectors:
            breadcrumb_elem = soup.select_one(selector)
            if breadcrumb_elem:
                links = breadcrumb_elem.find_all('a', href=True)
                navigation['breadcrumbs'] = [
                    {'text': link.get_text().strip(), 'href': link.get('href')}
                    for link in links
                ]
                break
        
        return navigation
    
    def _extract_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract form information"""
        
        forms = []
        
        for form in soup.find_all('form'):
            form_data = {
                'id': form.get('id'),
                'name': form.get('name'),
                'action': form.get('action'),
                'method': form.get('method', 'GET').upper(),
                'enctype': form.get('enctype'),
                'fields': []
            }
            
            # Extract form fields
            for field in form.find_all(['input', 'select', 'textarea']):
                field_data = {
                    'tag': field.name,
                    'type': field.get('type', 'text'),
                    'name': field.get('name'),
                    'id': field.get('id'),
                    'required': field.has_attr('required'),
                    'placeholder': field.get('placeholder')
                }
                
                if field.name == 'select':
                    field_data['options'] = [
                        {'value': opt.get('value'), 'text': opt.get_text().strip()}
                        for opt in field.find_all('option')
                    ]
                
                form_data['fields'].append(field_data)
            
            forms.append(form_data)
        
        return forms
    
    def _extract_media_elements(self, soup: BeautifulSoup) -> Dict[str, List[Dict[str, str]]]:
        """Extract media elements"""
        
        media = {
            'images': [],
            'videos': [],
            'audio': []
        }
        
        # Images
        for img in soup.find_all('img', src=True):
            media['images'].append({
                'src': img.get('src'),
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width'),
                'height': img.get('height')
            })
        
        # Videos
        for video in soup.find_all('video'):
            src = video.get('src')
            if not src:
                source = video.find('source')
                src = source.get('src') if source else ''
            
            media['videos'].append({
                'src': src,
                'poster': video.get('poster', ''),
                'controls': video.has_attr('controls'),
                'autoplay': video.has_attr('autoplay')
            })
        
        # Audio
        for audio in soup.find_all('audio'):
            src = audio.get('src')
            if not src:
                source = audio.find('source')
                src = source.get('src') if source else ''
            
            media['audio'].append({
                'src': src,
                'controls': audio.has_attr('controls'),
                'autoplay': audio.has_attr('autoplay')
            })
        
        return media
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract and categorize links"""
        
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            absolute_url = urljoin(base_url, href)
            
            link_data = {
                'text': link.get_text().strip(),
                'href': href,
                'absolute_url': absolute_url,
                'title': link.get('title', ''),
                'target': link.get('target', ''),
                'rel': link.get('rel'),
                'type': self._classify_link_type(href, absolute_url)
            }
            
            links.append(link_data)
        
        return links
    
    def _extract_scripts(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract script information"""
        
        scripts = []
        
        for script in soup.find_all('script'):
            script_data = {
                'src': script.get('src'),
                'type': script.get('type', 'text/javascript'),
                'async': script.has_attr('async'),
                'defer': script.has_attr('defer'),
                'inline': bool(script.string),
                'size': len(script.string) if script.string else 0
            }
            
            scripts.append(script_data)
        
        return scripts
    
    def _extract_styles(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract style information"""
        
        styles = []
        
        # External stylesheets
        for link in soup.find_all('link', rel='stylesheet'):
            styles.append({
                'type': 'external',
                'href': link.get('href'),
                'media': link.get('media', 'all')
            })
        
        # Inline styles
        for style in soup.find_all('style'):
            styles.append({
                'type': 'inline',
                'content_length': len(style.string) if style.string else 0
            })
        
        return styles
    
    def _analyze_page_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze overall page structure"""
        
        structure = {
            'has_header': bool(soup.find('header')),
            'has_nav': bool(soup.find('nav')),
            'has_main': bool(soup.find('main')),
            'has_aside': bool(soup.find('aside')),
            'has_footer': bool(soup.find('footer')),
            'heading_structure': self._analyze_heading_structure(soup),
            'semantic_elements': self._count_semantic_elements(soup),
            'accessibility_features': self._check_accessibility_features(soup)
        }
        
        return structure
    
    def _identify_automation_targets(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Identify elements suitable for automation"""
        
        targets = []
        
        # Common automation targets
        automation_selectors = {
            'login_form': ['form[action*="login"]', 'form#login', '.login-form'],
            'search_box': ['input[type="search"]', 'input[name*="search"]', '#search'],
            'submit_button': ['input[type="submit"]', 'button[type="submit"]', '.submit'],
            'contact_form': ['form[action*="contact"]', 'form#contact', '.contact-form'],
            'newsletter_signup': ['form[action*="newsletter"]', '.newsletter', '.signup'],
            'shopping_cart': ['.cart', '#cart', '[data-cart]'],
            'social_buttons': ['.social', '.share', '[data-social]']
        }
        
        for target_type, selectors in automation_selectors.items():
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    target = {
                        'type': target_type,
                        'tag': element.name,
                        'id': element.get('id'),
                        'class': element.get('class'),
                        'selector': selector,
                        'text': element.get_text().strip()[:100],
                        'automatable': True
                    }
                    targets.append(target)
        
        return targets
    
    async def _execute_automation_actions(self, session_id: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute automation actions on the page"""
        
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            results = []
            
            for action_data in actions:
                action_result = await self._execute_single_action(session, action_data)
                results.append(action_result)
                session["actions_performed"].append(action_result)
            
            successful_actions = len([r for r in results if r.get("success", False)])
            
            return {
                "success": True,
                "total_actions": len(actions),
                "successful_actions": successful_actions,
                "success_rate": successful_actions / len(actions) if actions else 1.0,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Automation execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_single_action(self, session: Dict[str, Any], action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single automation action"""
        
        action_type = action_data.get("type", "")
        
        try:
            if action_type == "click":
                return await self._simulate_click_action(session, action_data)
            elif action_type == "fill":
                return await self._simulate_fill_action(session, action_data)
            elif action_type == "select":
                return await self._simulate_select_action(session, action_data)
            elif action_type == "wait":
                return await self._simulate_wait_action(session, action_data)
            elif action_type == "screenshot":
                return await self._take_page_screenshot(session, action_data)
            elif action_type == "extract":
                return await self._extract_page_data(session, action_data)
            else:
                return {
                    "action_type": action_type,
                    "success": False,
                    "error": f"Unknown action type: {action_type}"
                }
        
        except Exception as e:
            return {
                "action_type": action_type,
                "success": False,
                "error": str(e)
            }
    
    async def _simulate_click_action(self, session: Dict[str, Any], action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate click action"""
        
        target = action_data.get("target", "")
        
        # In a real implementation, this would interact with the browser
        # For now, we simulate the action
        
        return {
            "action_type": "click",
            "target": target,
            "success": True,
            "result": f"Simulated click on {target}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _simulate_fill_action(self, session: Dict[str, Any], action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate fill action"""
        
        target = action_data.get("target", "")
        value = action_data.get("value", "")
        
        return {
            "action_type": "fill",
            "target": target,
            "value": value,
            "success": True,
            "result": f"Simulated filling {target} with {value}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _simulate_select_action(self, session: Dict[str, Any], action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate select action"""
        
        target = action_data.get("target", "")
        option = action_data.get("option", "")
        
        return {
            "action_type": "select",
            "target": target,
            "option": option,
            "success": True,
            "result": f"Simulated selecting {option} in {target}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _simulate_wait_action(self, session: Dict[str, Any], action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate wait action"""
        
        duration = action_data.get("duration", 1)
        
        await asyncio.sleep(duration)
        
        return {
            "action_type": "wait",
            "duration": duration,
            "success": True,
            "result": f"Waited for {duration} seconds",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _take_page_screenshot(self, session: Dict[str, Any], action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Take page screenshot (simulated)"""
        
        # In real implementation, this would capture actual screenshot
        screenshot_id = str(uuid.uuid4())
        
        return {
            "action_type": "screenshot",
            "screenshot_id": screenshot_id,
            "success": True,
            "result": f"Screenshot captured: {screenshot_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _extract_page_data(self, session: Dict[str, Any], action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific data from page"""
        
        target = action_data.get("target", "")
        data_type = action_data.get("data_type", "text")
        
        # Extract data based on current page data
        page_data = session.get("page_data", {})
        
        extracted_data = {}
        
        if data_type == "text":
            extracted_data["content"] = page_data.get("content", "")
        elif data_type == "links":
            extracted_data["links"] = page_data.get("links", [])
        elif data_type == "forms":
            extracted_data["forms"] = page_data.get("forms", [])
        elif data_type == "interactive":
            extracted_data["interactive_elements"] = page_data.get("interactive_elements", [])
        
        return {
            "action_type": "extract",
            "target": target,
            "data_type": data_type,
            "success": True,
            "result": extracted_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _check_wait_conditions(self, session_id: str, wait_conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check wait conditions"""
        
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            results = []
            
            for condition in wait_conditions:
                condition_result = await self._check_single_condition(session, condition)
                results.append(condition_result)
            
            all_met = all(r.get("met", False) for r in results)
            
            return {
                "success": True,
                "all_conditions_met": all_met,
                "conditions_checked": len(wait_conditions),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Wait condition check failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _check_single_condition(self, session: Dict[str, Any], condition: Dict[str, Any]) -> Dict[str, Any]:
        """Check a single wait condition"""
        
        condition_type = condition.get("type", "")
        
        try:
            if condition_type == "element_present":
                return self._check_element_present_condition(session, condition)
            elif condition_type == "text_present":
                return self._check_text_present_condition(session, condition)
            elif condition_type == "page_loaded":
                return self._check_page_loaded_condition(session, condition)
            elif condition_type == "timeout":
                return await self._check_timeout_condition(session, condition)
            else:
                return {
                    "condition_type": condition_type,
                    "met": False,
                    "error": f"Unknown condition type: {condition_type}"
                }
        
        except Exception as e:
            return {
                "condition_type": condition_type,
                "met": False,
                "error": str(e)
            }
    
    def _check_element_present_condition(self, session: Dict[str, Any], condition: Dict[str, Any]) -> Dict[str, Any]:
        """Check if element is present"""
        
        selector = condition.get("selector", "")
        page_data = session.get("page_data", {})
        
        # Check in interactive elements
        interactive_elements = page_data.get("interactive_elements", [])
        
        # Simple check - in real implementation would use proper CSS selector matching
        element_found = any(
            selector in str(element.get("id", "")) or 
            selector in str(element.get("class", "")) or
            selector in str(element.get("name", ""))
            for element in interactive_elements
        )
        
        return {
            "condition_type": "element_present",
            "selector": selector,
            "met": element_found,
            "result": "Element found" if element_found else "Element not found"
        }
    
    def _check_text_present_condition(self, session: Dict[str, Any], condition: Dict[str, Any]) -> Dict[str, Any]:
        """Check if text is present"""
        
        text = condition.get("text", "")
        page_data = session.get("page_data", {})
        
        content = page_data.get("content", "")
        text_found = text.lower() in content.lower()
        
        return {
            "condition_type": "text_present",
            "text": text,
            "met": text_found,
            "result": "Text found" if text_found else "Text not found"
        }
    
    def _check_page_loaded_condition(self, session: Dict[str, Any], condition: Dict[str, Any]) -> Dict[str, Any]:
        """Check if page is fully loaded"""
        
        page_data = session.get("page_data", {})
        
        # Simple check - page is loaded if we have content
        page_loaded = bool(page_data.get("content")) and not page_data.get("error")
        
        return {
            "condition_type": "page_loaded",
            "met": page_loaded,
            "result": "Page loaded" if page_loaded else "Page not loaded"
        }
    
    async def _check_timeout_condition(self, session: Dict[str, Any], condition: Dict[str, Any]) -> Dict[str, Any]:
        """Check timeout condition"""
        
        timeout = condition.get("timeout", 5)
        
        await asyncio.sleep(timeout)
        
        return {
            "condition_type": "timeout",
            "timeout": timeout,
            "met": True,
            "result": f"Timeout of {timeout} seconds completed"
        }
    
    # Helper methods for content extraction
    def _get_charset(self, soup: BeautifulSoup) -> str:
        """Get page charset"""
        charset_tag = soup.find('meta', charset=True)
        if charset_tag:
            return charset_tag.get('charset')
        
        content_type_tag = soup.find('meta', {'http-equiv': 'Content-Type'})
        if content_type_tag and content_type_tag.get('content'):
            content = content_type_tag['content']
            if 'charset=' in content:
                return content.split('charset=')[1].split(';')[0].strip()
        
        return 'utf-8'
    
    def _get_viewport(self, soup: BeautifulSoup) -> str:
        """Get viewport configuration"""
        viewport_tag = soup.find('meta', attrs={'name': 'viewport'})
        return viewport_tag.get('content', '') if viewport_tag else ''
    
    def _get_canonical_url(self, soup: BeautifulSoup) -> str:
        """Get canonical URL"""
        canonical_tag = soup.find('link', rel='canonical')
        return canonical_tag.get('href', '') if canonical_tag else ''
    
    def _get_language(self, soup: BeautifulSoup) -> str:
        """Get page language"""
        html_tag = soup.find('html')
        return html_tag.get('lang', '') if html_tag else ''
    
    def _classify_link_type(self, href: str, absolute_url: str) -> str:
        """Classify link type"""
        if href.startswith('#'):
            return 'anchor'
        elif href.startswith('mailto:'):
            return 'email'
        elif href.startswith('tel:'):
            return 'phone'
        elif href.startswith(('http://', 'https://')):
            return 'external'
        else:
            return 'internal'
    
    def _analyze_heading_structure(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Analyze heading structure"""
        headings = {'h1': 0, 'h2': 0, 'h3': 0, 'h4': 0, 'h5': 0, 'h6': 0}
        
        for level in headings.keys():
            headings[level] = len(soup.find_all(level))
        
        return headings
    
    def _count_semantic_elements(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Count semantic HTML5 elements"""
        semantic_elements = [
            'header', 'nav', 'main', 'section', 'article', 
            'aside', 'footer', 'figure', 'figcaption'
        ]
        
        counts = {}
        for element in semantic_elements:
            counts[element] = len(soup.find_all(element))
        
        return counts
    
    def _check_accessibility_features(self, soup: BeautifulSoup) -> Dict[str, bool]:
        """Check accessibility features"""
        return {
            'has_alt_text': bool(soup.find('img', alt=True)),
            'has_aria_labels': bool(soup.find(attrs={'aria-label': True})),
            'has_skip_links': bool(soup.find('a', href='#main')) or bool(soup.find('a', href='#content')),
            'has_headings': bool(soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
            'has_form_labels': bool(soup.find('label'))
        }
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate content hash for change detection"""
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get browser session status"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        return {
            "success": True,
            "session": {
                "session_id": session_id,
                "current_url": session.get("current_url"),
                "automation_state": session.get("automation_state"),
                "actions_performed": len(session.get("actions_performed", [])),
                "screenshots_taken": len(session.get("screenshots", [])),
                "started_at": session.get("started_at").isoformat() if session.get("started_at") else None,
                "completed_at": session.get("completed_at").isoformat() if session.get("completed_at") else None
            }
        }
    
    async def close_session(self, session_id: str) -> bool:
        """Close browser session and cleanup"""
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        
        return False

# Global instance
enhanced_browser_engine = EnhancedNativeBrowserEngine()