import asyncio
import logging
from typing import Dict, List, Any, Optional
import httpx
from bs4 import BeautifulSoup
import json
import base64
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class EnhancedBrowserEngine:
    """
    Phase 1 & 4: Enhanced Browser Engine with Native Capabilities
    Builds upon existing iframe system while adding browser automation
    """
    
    def __init__(self):
        self.session_storage = {}
        self.automation_sessions = {}
        self.virtual_workspaces = {}
        
    async def navigate_with_automation(self, url: str, actions: List[Dict] = None, wait_conditions: List[Dict] = None) -> Dict[str, Any]:
        """Enhanced navigation with automation capabilities"""
        try:
            session_id = str(uuid.uuid4())
            
            # Enhanced web page fetching with automation support
            page_data = await self._fetch_with_automation(url, actions or [])
            
            # Store session with enhanced metadata
            self.session_storage[session_id] = {
                "url": url,
                "page_data": page_data,
                "actions_performed": actions or [],
                "timestamp": datetime.utcnow(),
                "automation_context": {
                    "dom_elements": page_data.get("dom_elements", []),
                    "interactive_elements": page_data.get("interactive_elements", []),
                    "forms": page_data.get("forms", [])
                }
            }
            
            return {
                "session_id": session_id,
                "success": True,
                "page_data": page_data,
                "automation_ready": True
            }
            
        except Exception as e:
            logger.error(f"Enhanced navigation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _fetch_with_automation(self, url: str, actions: List[Dict]) -> Dict[str, Any]:
        """Fetch page with automation capabilities"""
        try:
            # Enhanced HTTP client with browser-like behavior
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 AETHER/3.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                },
                follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Enhanced HTML parsing with automation metadata
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove non-content elements for better processing
                for element in soup(["script", "style", "nav", "header", "footer", "aside", "advertisement"]):
                    element.decompose()
                
                # Extract enhanced metadata
                page_data = {
                    "url": url,
                    "title": soup.title.string if soup.title else url,
                    "content": self._extract_main_content(soup),
                    "meta_description": self._extract_meta_description(soup),
                    "meta_keywords": self._extract_meta_keywords(soup),
                    "dom_elements": self._extract_dom_elements(soup),
                    "interactive_elements": self._extract_interactive_elements(soup),
                    "forms": self._extract_forms(soup),
                    "links": self._extract_links(soup),
                    "images": self._extract_images(soup),
                    "automation_hints": self._generate_automation_hints(soup),
                    "accessibility_info": self._extract_accessibility_info(soup),
                    "performance_metrics": {
                        "load_time": response.elapsed.total_seconds(),
                        "content_size": len(response.text),
                        "status_code": response.status_code
                    },
                    "extracted_at": datetime.utcnow().isoformat()
                }
                
                # Execute any specified actions
                if actions:
                    page_data["action_results"] = await self._execute_page_actions(soup, actions, url)
                
                return page_data
                
        except Exception as e:
            logger.error(f"Enhanced fetch failed for {url}: {e}")
            return {
                "url": url,
                "title": url,
                "content": f"Error loading page: {str(e)}",
                "error": True,
                "extracted_at": datetime.utcnow().isoformat()
            }
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content with enhanced algorithm"""
        # Priority order for main content detection
        main_selectors = [
            'main',
            '[role="main"]',
            'article',
            '.main-content',
            '#main-content',
            '.content',
            '#content',
            '.post-content',
            '.entry-content'
        ]
        
        for selector in main_selectors:
            main_element = soup.select_one(selector)
            if main_element:
                text = main_element.get_text(separator=' ', strip=True)
                if len(text) > 100:  # Ensure substantial content
                    return text[:10000]  # Increased content limit
        
        # Fallback to body content with intelligent filtering
        body = soup.find('body')
        if body:
            # Remove common non-content elements
            for element in body.find_all(['nav', 'header', 'footer', 'aside', 'div'], class_=['navigation', 'nav', 'menu', 'sidebar', 'footer']):
                element.decompose()
            
            text = body.get_text(separator=' ', strip=True)
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            return clean_text[:10000]
        
        return soup.get_text()[:5000]
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']
        
        # Fallback to Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content']
        
        return ""
    
    def _extract_meta_keywords(self, soup: BeautifulSoup) -> str:
        """Extract meta keywords"""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            return meta_keywords['content']
        return ""
    
    def _extract_dom_elements(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract important DOM elements for automation"""
        elements = []
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            elements.append({
                "type": "heading",
                "tag": heading.name,
                "text": heading.get_text(strip=True),
                "level": int(heading.name[1])
            })
        
        # Extract paragraphs with substantial content
        for para in soup.find_all('p'):
            text = para.get_text(strip=True)
            if len(text) > 50:
                elements.append({
                    "type": "paragraph",
                    "text": text[:500],
                    "length": len(text)
                })
        
        return elements[:50]  # Limit for performance
    
    def _extract_interactive_elements(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract interactive elements for automation"""
        interactive = []
        
        # Buttons
        for button in soup.find_all(['button', 'input']):
            if button.name == 'input' and button.get('type') not in ['button', 'submit', 'reset']:
                continue
            
            interactive.append({
                "type": "button",
                "text": button.get_text(strip=True) or button.get('value', ''),
                "id": button.get('id', ''),
                "class": button.get('class', []),
                "onclick": button.get('onclick', ''),
                "form_action": button.get('formaction', '')
            })
        
        # Links
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            if text and len(text) < 200:
                interactive.append({
                    "type": "link",
                    "text": text,
                    "href": link['href'],
                    "id": link.get('id', ''),
                    "class": link.get('class', [])
                })
        
        # Input fields
        for input_field in soup.find_all('input'):
            input_type = input_field.get('type', 'text')
            if input_type in ['text', 'email', 'password', 'search', 'tel', 'url']:
                interactive.append({
                    "type": "input",
                    "input_type": input_type,
                    "name": input_field.get('name', ''),
                    "id": input_field.get('id', ''),
                    "placeholder": input_field.get('placeholder', ''),
                    "required": input_field.has_attr('required')
                })
        
        return interactive[:30]  # Limit for performance
    
    def _extract_forms(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract form information for automation"""
        forms = []
        
        for form in soup.find_all('form'):
            form_data = {
                "action": form.get('action', ''),
                "method": form.get('method', 'GET'),
                "id": form.get('id', ''),
                "class": form.get('class', []),
                "fields": []
            }
            
            # Extract form fields
            for field in form.find_all(['input', 'textarea', 'select']):
                field_info = {
                    "tag": field.name,
                    "type": field.get('type', ''),
                    "name": field.get('name', ''),
                    "id": field.get('id', ''),
                    "required": field.has_attr('required'),
                    "placeholder": field.get('placeholder', '')
                }
                
                if field.name == 'select':
                    options = [opt.get_text(strip=True) for opt in field.find_all('option')]
                    field_info["options"] = options
                
                form_data["fields"].append(field_info)
            
            forms.append(form_data)
        
        return forms
    
    def _extract_links(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract links for navigation analysis"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            if text and len(text) < 100:
                links.append({
                    "text": text,
                    "href": href,
                    "is_external": href.startswith(('http://', 'https://')) and not any(domain in href for domain in ['localhost', '127.0.0.1']),
                    "is_download": any(ext in href.lower() for ext in ['.pdf', '.doc', '.zip', '.exe', '.dmg'])
                })
        
        return links[:20]  # Limit for performance
    
    def _extract_images(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract image information"""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            
            if src:
                images.append({
                    "src": src,
                    "alt": alt,
                    "width": img.get('width', ''),
                    "height": img.get('height', ''),
                    "loading": img.get('loading', '')
                })
        
        return images[:10]  # Limit for performance
    
    def _generate_automation_hints(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Generate hints for automation possibilities"""
        hints = {
            "has_search": bool(soup.find(['input'], type='search') or soup.find(['input'], placeholder=lambda x: x and 'search' in x.lower())),
            "has_login": bool(soup.find(['input'], type='password')),
            "has_forms": len(soup.find_all('form')) > 0,
            "has_navigation": bool(soup.find(['nav']) or soup.find_all('a')),
            "interactive_score": len(soup.find_all(['button', 'input', 'select', 'textarea'])),
            "content_type": self._determine_content_type(soup)
        }
        
        return hints
    
    def _determine_content_type(self, soup: BeautifulSoup) -> str:
        """Determine the type of content on the page"""
        # Simple heuristic-based content type detection
        if soup.find(['article']) or soup.find(class_=lambda x: x and any(cls in str(x).lower() for cls in ['post', 'article', 'blog'])):
            return "blog_article"
        elif soup.find(['table']) or soup.find(class_=lambda x: x and 'table' in str(x).lower()):
            return "data_table"
        elif len(soup.find_all('form')) > 0:
            return "form_page"
        elif len(soup.find_all(['nav', 'a'])) > 20:
            return "navigation_heavy"
        else:
            return "general_content"
    
    def _extract_accessibility_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract accessibility information"""
        return {
            "has_alt_texts": len([img for img in soup.find_all('img') if img.get('alt')]),
            "has_labels": len(soup.find_all('label')),
            "has_headings": len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
            "has_landmarks": len(soup.find_all(['main', 'nav', 'aside', 'section', 'article']))
        }
    
    async def _execute_page_actions(self, soup: BeautifulSoup, actions: List[Dict], url: str) -> List[Dict]:
        """Execute specified actions on the page"""
        results = []
        
        for action in actions:
            action_type = action.get("type", "")
            
            try:
                if action_type == "click":
                    result = await self._simulate_click(soup, action, url)
                elif action_type == "extract":
                    result = await self._extract_specific_content(soup, action)
                elif action_type == "form_fill":
                    result = await self._simulate_form_fill(soup, action)
                else:
                    result = {"success": False, "error": f"Unknown action type: {action_type}"}
                
                results.append({
                    "action": action,
                    "result": result
                })
                
            except Exception as e:
                results.append({
                    "action": action,
                    "result": {"success": False, "error": str(e)}
                })
        
        return results
    
    async def _simulate_click(self, soup: BeautifulSoup, action: Dict, url: str) -> Dict[str, Any]:
        """Simulate a click action"""
        selector = action.get("selector", "")
        text = action.get("text", "")
        
        # Find element by selector or text
        element = None
        if selector:
            element = soup.select_one(selector)
        elif text:
            element = soup.find(lambda tag: tag.name in ['a', 'button'] and text.lower() in tag.get_text().lower())
        
        if element:
            # If it's a link, we could potentially follow it
            if element.name == 'a' and element.get('href'):
                href = element['href']
                return {
                    "success": True,
                    "action": "navigation",
                    "target_url": href,
                    "element_text": element.get_text(strip=True)
                }
            else:
                return {
                    "success": True,
                    "action": "click",
                    "element": element.name,
                    "element_text": element.get_text(strip=True)
                }
        
        return {"success": False, "error": "Element not found"}
    
    async def _extract_specific_content(self, soup: BeautifulSoup, action: Dict) -> Dict[str, Any]:
        """Extract specific content based on action parameters"""
        selector = action.get("selector", "")
        content_type = action.get("content_type", "text")
        
        elements = soup.select(selector) if selector else []
        
        extracted = []
        for element in elements[:10]:  # Limit for performance
            if content_type == "text":
                extracted.append(element.get_text(strip=True))
            elif content_type == "html":
                extracted.append(str(element))
            elif content_type == "attributes":
                extracted.append(dict(element.attrs))
        
        return {
            "success": True,
            "extracted_content": extracted,
            "count": len(extracted)
        }
    
    async def _simulate_form_fill(self, soup: BeautifulSoup, action: Dict) -> Dict[str, Any]:
        """Simulate form filling"""
        form_data = action.get("form_data", {})
        
        # Find the form
        form = soup.find('form')
        if not form:
            return {"success": False, "error": "No form found"}
        
        filled_fields = []
        for field_name, field_value in form_data.items():
            field = form.find(['input', 'textarea', 'select'], attrs={'name': field_name})
            if field:
                filled_fields.append({
                    "field": field_name,
                    "value": field_value,
                    "type": field.get('type', field.name)
                })
        
        return {
            "success": True,
            "filled_fields": filled_fields,
            "form_action": form.get('action', ''),
            "form_method": form.get('method', 'GET')
        }
    
    async def create_virtual_workspace(self, workspace_name: str) -> str:
        """Create a virtual workspace for background operations"""
        workspace_id = str(uuid.uuid4())
        
        self.virtual_workspaces[workspace_id] = {
            "name": workspace_name,
            "created_at": datetime.utcnow(),
            "sessions": [],
            "background_tasks": [],
            "status": "active"
        }
        
        return workspace_id
    
    async def execute_in_workspace(self, workspace_id: str, url: str, actions: List[Dict]) -> Dict[str, Any]:
        """Execute actions in a virtual workspace"""
        if workspace_id not in self.virtual_workspaces:
            raise ValueError(f"Workspace {workspace_id} not found")
        
        # Execute navigation in background
        result = await self.navigate_with_automation(url, actions)
        
        # Add to workspace session history
        self.virtual_workspaces[workspace_id]["sessions"].append({
            "url": url,
            "actions": actions,
            "result": result,
            "timestamp": datetime.utcnow()
        })
        
        return result

# Initialize global enhanced browser engine
enhanced_browser_engine = EnhancedBrowserEngine()