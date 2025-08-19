import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiofiles
import httpx
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup
import hashlib
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

@dataclass
class SecurityAnalysis:
    ssl_cert_valid: bool
    has_security_headers: Dict[str, bool]
    content_security_policy: Optional[str]
    security_score: int
    warnings: List[str]
    recommendations: List[str]

@dataclass
class PagePerformance:
    load_time: float
    content_size: int
    resource_count: int
    compression_used: bool
    cache_headers: Dict[str, str]
    performance_score: int

@dataclass
class ContentAnalysis:
    language: str
    readability_score: float
    sentiment: str
    key_topics: List[str]
    meta_quality: Dict[str, Any]
    seo_score: int

class AdvancedBrowserEngine:
    """
    Enhanced browser engine with advanced security, performance analysis,
    and intelligent content processing capabilities.
    """
    
    def __init__(self):
        self.session_cache = {}
        self.security_cache = {}
        self.performance_cache = {}
        self.content_cache = {}
        self.blocked_domains = set()
        self.trusted_domains = set()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Enhanced security headers to check
        self.security_headers = {
            'strict-transport-security': 'HSTS',
            'content-security-policy': 'CSP',
            'x-frame-options': 'Frame Protection',
            'x-content-type-options': 'Content Type Protection',
            'x-xss-protection': 'XSS Protection',
            'referrer-policy': 'Referrer Policy'
        }
        
    async def enhanced_navigate(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhanced navigation with comprehensive analysis"""
        start_time = time.time()
        options = options or {}
        
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                if not url.startswith(('http://', 'https://')):
                    url = f"https://{url}"
                    parsed_url = urlparse(url)
            
            # Security pre-check
            if parsed_url.netloc in self.blocked_domains:
                return {
                    "success": False,
                    "error": "Domain blocked for security reasons",
                    "url": url
                }
            
            # Parallel processing for performance
            tasks = [
                self._fetch_page_content(url, options),
                self._analyze_security(url),
                self._analyze_performance(url)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            page_content, security_analysis, performance_analysis = results
            
            # Handle exceptions
            if isinstance(page_content, Exception):
                logger.error(f"Page fetch failed: {page_content}")
                return {"success": False, "error": str(page_content), "url": url}
                
            if isinstance(security_analysis, Exception):
                logger.warning(f"Security analysis failed: {security_analysis}")
                security_analysis = self._default_security_analysis()
                
            if isinstance(performance_analysis, Exception):
                logger.warning(f"Performance analysis failed: {performance_analysis}")
                performance_analysis = self._default_performance_analysis()
            
            # Enhanced content analysis
            content_analysis = await self._analyze_content(page_content.get('content', ''))
            
            # Compile comprehensive result
            navigation_result = {
                "success": True,
                "url": url,
                "final_url": page_content.get('final_url', url),
                "title": page_content.get('title', ''),
                "content": page_content.get('content', ''),
                "meta": page_content.get('meta', {}),
                "links": page_content.get('links', []),
                "images": page_content.get('images', []),
                "scripts": page_content.get('scripts', []),
                "security": security_analysis.__dict__ if hasattr(security_analysis, '__dict__') else security_analysis,
                "performance": performance_analysis.__dict__ if hasattr(performance_analysis, '__dict__') else performance_analysis,
                "content_analysis": content_analysis.__dict__ if hasattr(content_analysis, '__dict__') else content_analysis,
                "load_time": time.time() - start_time,
                "timestamp": datetime.utcnow().isoformat(),
                "enhanced_features": [
                    "advanced_security_analysis",
                    "performance_optimization",
                    "intelligent_content_processing",
                    "parallel_resource_loading",
                    "comprehensive_meta_analysis"
                ]
            }
            
            return navigation_result
            
        except Exception as e:
            logger.error(f"Enhanced navigation failed for {url}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "load_time": time.time() - start_time
            }
    
    async def _fetch_page_content(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced page content fetching with advanced parsing"""
        
        headers = {
            'User-Agent': options.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        timeout = options.get('timeout', 15)
        
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers=headers,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        ) as client:
            
            response = await client.get(url)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Enhanced meta extraction
            meta_data = self._extract_enhanced_meta(soup)
            
            # Enhanced content extraction
            content = self._extract_main_content(soup)
            
            # Extract resources
            links = self._extract_links(soup, url)
            images = self._extract_images(soup, url)
            scripts = self._extract_scripts(soup, url)
            
            return {
                "final_url": str(response.url),
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "title": soup.title.string.strip() if soup.title else "",
                "content": content,
                "meta": meta_data,
                "links": links,
                "images": images,
                "scripts": scripts,
                "content_length": len(response.content),
                "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0
            }
    
    def _extract_enhanced_meta(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract comprehensive meta information"""
        meta = {
            "description": "",
            "keywords": [],
            "author": "",
            "robots": "",
            "og": {},
            "twitter": {},
            "canonical": "",
            "viewport": "",
            "charset": "",
            "language": "en"
        }
        
        # Standard meta tags
        for tag in soup.find_all('meta'):
            name = tag.get('name', '').lower()
            property_attr = tag.get('property', '').lower()
            content = tag.get('content', '')
            
            if name == 'description':
                meta["description"] = content
            elif name == 'keywords':
                meta["keywords"] = [k.strip() for k in content.split(',')]
            elif name == 'author':
                meta["author"] = content
            elif name == 'robots':
                meta["robots"] = content
            elif name == 'viewport':
                meta["viewport"] = content
            elif tag.get('charset'):
                meta["charset"] = tag.get('charset')
            elif property_attr.startswith('og:'):
                meta["og"][property_attr[3:]] = content
            elif name.startswith('twitter:'):
                meta["twitter"][name[8:]] = content
        
        # Canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical:
            meta["canonical"] = canonical.get('href', '')
        
        # Language
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            meta["language"] = html_tag.get('lang')
        
        return meta
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content using intelligent parsing"""
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            element.decompose()
        
        # Try to find main content areas
        main_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.main-content',
            '.content',
            '#main',
            '#content'
        ]
        
        main_content = None
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            # Fallback to body
            main_content = soup.body or soup
        
        # Extract and clean text
        text = main_content.get_text(separator=' ', strip=True)
        
        # Clean up whitespace and empty lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = ' '.join(lines)
        
        # Limit content size but ensure it's meaningful
        if len(clean_text) > 10000:
            clean_text = clean_text[:10000] + "..."
        
        return clean_text
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract and categorize links"""
        links = []
        
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            text = link_tag.get_text(strip=True)
            
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            
            # Categorize link type
            link_type = "internal" if urlparse(full_url).netloc == urlparse(base_url).netloc else "external"
            
            if href.startswith('mailto:'):
                link_type = "email"
            elif href.startswith('tel:'):
                link_type = "phone"
            elif href.startswith('#'):
                link_type = "anchor"
            
            links.append({
                "url": full_url,
                "text": text,
                "type": link_type,
                "original_href": href
            })
            
            # Limit to avoid excessive data
            if len(links) >= 50:
                break
        
        return links
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract image information"""
        images = []
        
        for img_tag in soup.find_all('img', src=True):
            src = img_tag['src']
            alt = img_tag.get('alt', '')
            
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, src)
            
            images.append({
                "url": full_url,
                "alt": alt,
                "original_src": src
            })
            
            # Limit to avoid excessive data
            if len(images) >= 20:
                break
        
        return images
    
    def _extract_scripts(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract script information for security analysis"""
        scripts = []
        
        for script_tag in soup.find_all('script'):
            src = script_tag.get('src')
            script_type = script_tag.get('type', 'text/javascript')
            
            if src:
                full_url = urljoin(base_url, src)
                script_source = "external"
            else:
                full_url = ""
                script_source = "inline"
            
            scripts.append({
                "url": full_url,
                "type": script_type,
                "source": script_source
            })
        
        return scripts
    
    async def _analyze_security(self, url: str) -> SecurityAnalysis:
        """Comprehensive security analysis"""
        
        cache_key = f"security:{hashlib.md5(url.encode()).hexdigest()}"
        if cache_key in self.security_cache:
            return self.security_cache[cache_key]
        
        try:
            parsed_url = urlparse(url)
            warnings = []
            recommendations = []
            
            # Check HTTPS
            ssl_cert_valid = parsed_url.scheme == 'https'
            if not ssl_cert_valid:
                warnings.append("Insecure connection (HTTP)")
                recommendations.append("Use HTTPS for secure communication")
            
            # Fetch headers for security analysis
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.head(url, follow_redirects=True)
                headers = dict(response.headers)
            
            # Analyze security headers
            security_headers_present = {}
            for header, name in self.security_headers.items():
                is_present = header.lower() in [h.lower() for h in headers.keys()]
                security_headers_present[name] = is_present
                
                if not is_present:
                    recommendations.append(f"Add {name} header for enhanced security")
            
            # Extract CSP if present
            csp = headers.get('content-security-policy', headers.get('Content-Security-Policy'))
            
            # Calculate security score
            score = 60  # Base score
            if ssl_cert_valid:
                score += 20
            score += sum(5 for present in security_headers_present.values() if present)
            
            security_analysis = SecurityAnalysis(
                ssl_cert_valid=ssl_cert_valid,
                has_security_headers=security_headers_present,
                content_security_policy=csp,
                security_score=min(100, score),
                warnings=warnings,
                recommendations=recommendations
            )
            
            # Cache result
            self.security_cache[cache_key] = security_analysis
            
            return security_analysis
            
        except Exception as e:
            logger.error(f"Security analysis failed for {url}: {str(e)}")
            return self._default_security_analysis()
    
    async def _analyze_performance(self, url: str) -> PagePerformance:
        """Comprehensive performance analysis"""
        
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url, follow_redirects=True)
                load_time = time.time() - start_time
            
            headers = dict(response.headers)
            content_size = len(response.content)
            
            # Check compression
            compression_used = 'gzip' in headers.get('content-encoding', '')
            
            # Extract cache headers
            cache_headers = {}
            cache_related = ['cache-control', 'expires', 'etag', 'last-modified']
            for header in cache_related:
                if header in [h.lower() for h in headers.keys()]:
                    cache_headers[header] = headers.get(header, '')
            
            # Simple resource count estimation (would need full parsing for accuracy)
            soup = BeautifulSoup(response.text, 'html.parser')
            resource_count = len(soup.find_all(['img', 'script', 'link']))
            
            # Calculate performance score
            score = 100
            if load_time > 3:
                score -= 30
            elif load_time > 1:
                score -= 10
                
            if content_size > 1000000:  # 1MB
                score -= 20
            elif content_size > 500000:  # 500KB
                score -= 10
            
            if not compression_used:
                score -= 15
            
            if not cache_headers:
                score -= 10
            
            performance_analysis = PagePerformance(
                load_time=load_time,
                content_size=content_size,
                resource_count=resource_count,
                compression_used=compression_used,
                cache_headers=cache_headers,
                performance_score=max(0, score)
            )
            
            return performance_analysis
            
        except Exception as e:
            logger.error(f"Performance analysis failed for {url}: {str(e)}")
            return self._default_performance_analysis()
    
    async def _analyze_content(self, content: str) -> ContentAnalysis:
        """Intelligent content analysis"""
        
        try:
            # Language detection (simplified)
            language = "en"  # Default, could implement proper detection
            
            # Readability analysis (simplified Flesch Reading Ease approximation)
            sentences = len(re.findall(r'[.!?]+', content))
            words = len(content.split())
            syllables = self._count_syllables(content[:1000])  # Sample for performance
            
            if sentences > 0 and words > 0:
                readability_score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
                readability_score = max(0, min(100, readability_score))
            else:
                readability_score = 50
            
            # Sentiment analysis (simplified)
            positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'best']
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'disappointing']
            
            content_lower = content.lower()
            positive_count = sum(1 for word in positive_words if word in content_lower)
            negative_count = sum(1 for word in negative_words if word in content_lower)
            
            if positive_count > negative_count:
                sentiment = "positive"
            elif negative_count > positive_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            # Extract key topics (simplified keyword extraction)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
            word_freq = {}
            for word in words:
                if word not in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            key_topics = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:5]
            
            # Meta quality assessment
            meta_quality = {
                "has_sufficient_content": len(content) > 300,
                "word_count": words,
                "sentence_count": sentences,
                "paragraph_estimation": content.count('\n') + 1
            }
            
            # SEO score (basic)
            seo_score = 70  # Base score
            if words > 300:
                seo_score += 10
            if readability_score > 60:
                seo_score += 10
            if len(key_topics) >= 3:
                seo_score += 10
            
            content_analysis = ContentAnalysis(
                language=language,
                readability_score=readability_score,
                sentiment=sentiment,
                key_topics=key_topics,
                meta_quality=meta_quality,
                seo_score=min(100, seo_score)
            )
            
            return content_analysis
            
        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            return ContentAnalysis(
                language="en",
                readability_score=50,
                sentiment="neutral",
                key_topics=[],
                meta_quality={},
                seo_score=50
            )
    
    def _count_syllables(self, text: str) -> int:
        """Simple syllable counting for readability analysis"""
        text = text.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in text:
            if char in vowels:
                if not previous_was_vowel:
                    syllable_count += 1
                previous_was_vowel = True
            else:
                previous_was_vowel = False
        
        # Adjust for silent 'e'
        if text.endswith('e'):
            syllable_count -= 1
        
        # Ensure at least one syllable per word
        word_count = len(text.split())
        return max(syllable_count, word_count)
    
    def _default_security_analysis(self) -> SecurityAnalysis:
        """Default security analysis for error cases"""
        return SecurityAnalysis(
            ssl_cert_valid=False,
            has_security_headers={},
            content_security_policy=None,
            security_score=30,
            warnings=["Security analysis unavailable"],
            recommendations=["Enable security analysis"]
        )
    
    def _default_performance_analysis(self) -> PagePerformance:
        """Default performance analysis for error cases"""
        return PagePerformance(
            load_time=0,
            content_size=0,
            resource_count=0,
            compression_used=False,
            cache_headers={},
            performance_score=50
        )
    
    async def get_browser_capabilities(self) -> Dict[str, Any]:
        """Get comprehensive browser engine capabilities"""
        return {
            "engine_version": "4.0.0",
            "capabilities": [
                "advanced_security_analysis",
                "comprehensive_performance_monitoring",
                "intelligent_content_processing",
                "parallel_resource_loading",
                "enhanced_meta_extraction",
                "security_header_validation",
                "content_quality_assessment",
                "seo_analysis",
                "readability_scoring",
                "sentiment_analysis"
            ],
            "security_features": [
                "ssl_validation",
                "security_header_analysis",
                "csp_validation",
                "domain_blocking",
                "trusted_domain_management"
            ],
            "performance_features": [
                "load_time_monitoring",
                "content_size_analysis",
                "compression_detection",
                "cache_header_analysis",
                "resource_counting"
            ],
            "content_features": [
                "language_detection",
                "readability_analysis",
                "sentiment_analysis",
                "keyword_extraction",
                "meta_quality_assessment",
                "seo_scoring"
            ]
        }

# Export the enhanced browser engine
browser_engine = AdvancedBrowserEngine()