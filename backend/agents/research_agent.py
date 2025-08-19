import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from bs4 import BeautifulSoup
from .base_agent import BaseAgent, AgentTask, AgentCapability
import re
import urllib.parse

class ResearchAgent(BaseAgent):
    """Specialized agent for web research and information gathering"""
    
    def __init__(self):
        super().__init__(
            agent_id="research_agent",
            name="Research Agent",
            description="Conducts web research, gathers information, and analyzes content"
        )
        
        # Research configuration
        self.max_search_results = 20
        self.max_content_length = 50000
        self.timeout = 30
        
        # Search engines and APIs
        self.search_engines = {
            "google": "https://www.googleapis.com/customsearch/v1",
            "bing": "https://api.bing.microsoft.com/v7.0/search",
            "duckduckgo": "https://api.duckduckgo.com/"
        }
        
        # Content extraction patterns
        self.content_patterns = {
            "article": [
                "article", "main", ".content", ".article-content",
                ".post-content", ".entry-content"
            ],
            "text": ["p", "div", "span", "section"],
            "headings": ["h1", "h2", "h3", "h4", "h5", "h6"],
            "links": ["a[href]"],
            "images": ["img[src]"]
        }
        
    async def initialize(self) -> bool:
        """Initialize the research agent"""
        try:
            # Test connectivity to search engines
            async with aiohttp.ClientSession() as session:
                test_url = "https://httpbin.org/get"
                async with session.get(test_url, timeout=5) as response:
                    if response.status == 200:
                        self.logger.info("Research agent initialized successfully")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize research agent: {e}")
            return False
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a research task"""
        task_type = task.type
        
        if task_type == "web_search":
            return await self._perform_web_search(task)
        elif task_type == "content_analysis":
            return await self._analyze_content(task)
        elif task_type == "url_scraping":
            return await self._scrape_urls(task)
        elif task_type == "deep_research":
            return await self._deep_research(task)
        elif task_type == "competitor_analysis":
            return await self._competitor_analysis(task)
        else:
            return {"error": f"Unknown research task type: {task_type}"}
    
    async def get_capabilities(self) -> List[AgentCapability]:
        """Return research agent capabilities"""
        return [
            AgentCapability(
                name="Web Search",
                description="Search the web for information on specific topics",
                input_types=["web_search"],
                output_types=["search_results"],
                estimated_time=5.0,
                success_rate=0.95
            ),
            AgentCapability(
                name="Content Analysis",
                description="Analyze web content for insights and patterns",
                input_types=["content_analysis"],
                output_types=["analysis_report"],
                estimated_time=8.0,
                success_rate=0.90
            ),
            AgentCapability(
                name="URL Scraping",
                description="Extract content and data from specific URLs",
                input_types=["url_scraping"],
                output_types=["scraped_data"],
                estimated_time=3.0,
                success_rate=0.85
            ),
            AgentCapability(
                name="Deep Research",
                description="Comprehensive research combining multiple sources",
                input_types=["deep_research"],
                output_types=["research_report"],
                estimated_time=15.0,
                success_rate=0.88
            ),
            AgentCapability(
                name="Competitor Analysis",
                description="Analyze competitors and market landscape",
                input_types=["competitor_analysis"],
                output_types=["competitor_report"],
                estimated_time=20.0,
                success_rate=0.85
            )
        ]
    
    async def _perform_web_search(self, task: AgentTask) -> Dict[str, Any]:
        """Perform web search for given query"""
        try:
            query = task.payload.get("query", "")
            max_results = task.payload.get("max_results", self.max_search_results)
            
            if not query:
                return {"error": "No search query provided"}
            
            # Use DuckDuckGo instant answer API (no key required)
            search_results = await self._search_duckduckgo(query, max_results)
            
            # Fallback to direct web scraping if API fails
            if not search_results:
                search_results = await self._search_fallback(query, max_results)
            
            # Analyze and rank results
            ranked_results = await self._rank_search_results(search_results, query)
            
            return {
                "query": query,
                "total_results": len(ranked_results),
                "results": ranked_results,
                "search_time": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return {"error": str(e), "success": False}
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo instant answer API"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1"
                }
                
                url = "https://api.duckduckgo.com/"
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        results = []
                        
                        # Process related topics
                        for topic in data.get("RelatedTopics", [])[:max_results]:
                            if isinstance(topic, dict) and "FirstURL" in topic:
                                results.append({
                                    "title": topic.get("Text", "").split(" - ")[0],
                                    "url": topic["FirstURL"],
                                    "description": topic.get("Text", ""),
                                    "source": "duckduckgo"
                                })
                        
                        return results
            
            return []
            
        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    async def _search_fallback(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback search by scraping search engine results"""
        try:
            # Use Google search (scraping)
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={max_results}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        results = []
                        
                        # Extract search results
                        for result in soup.find_all('div', class_='g')[:max_results]:
                            title_elem = result.find('h3')
                            link_elem = result.find('a')
                            desc_elem = result.find('span', class_='st') or result.find('div', class_='s')
                            
                            if title_elem and link_elem:
                                results.append({
                                    "title": title_elem.get_text(),
                                    "url": link_elem.get('href', ''),
                                    "description": desc_elem.get_text() if desc_elem else "",
                                    "source": "google_scrape"
                                })
                        
                        return results
            
            return []
            
        except Exception as e:
            self.logger.error(f"Fallback search failed: {e}")
            return []
    
    async def _rank_search_results(self, results: List[Dict[str, Any]], 
                                 query: str) -> List[Dict[str, Any]]:
        """Rank search results by relevance"""
        try:
            query_words = set(query.lower().split())
            
            for result in results:
                score = 0
                title = result.get("title", "").lower()
                description = result.get("description", "").lower()
                
                # Title relevance (higher weight)
                title_matches = len(query_words.intersection(set(title.split())))
                score += title_matches * 3
                
                # Description relevance
                desc_matches = len(query_words.intersection(set(description.split())))
                score += desc_matches * 1
                
                # URL relevance
                url = result.get("url", "").lower()
                url_matches = len(query_words.intersection(set(url.split('/'))))
                score += url_matches * 0.5
                
                result["relevance_score"] = score
            
            # Sort by relevance score
            ranked_results = sorted(results, key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            return ranked_results
            
        except Exception as e:
            self.logger.error(f"Result ranking failed: {e}")
            return results
    
    async def _scrape_urls(self, task: AgentTask) -> Dict[str, Any]:
        """Scrape content from specific URLs"""
        try:
            urls = task.payload.get("urls", [])
            if isinstance(urls, str):
                urls = [urls]
            
            scraped_data = []
            
            async with aiohttp.ClientSession() as session:
                for url in urls:
                    try:
                        data = await self._scrape_single_url(session, url)
                        scraped_data.append(data)
                    except Exception as e:
                        scraped_data.append({
                            "url": url,
                            "error": str(e),
                            "success": False
                        })
            
            return {
                "total_urls": len(urls),
                "successful_scrapes": len([d for d in scraped_data if d.get("success", False)]),
                "scraped_data": scraped_data,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"URL scraping failed: {e}")
            return {"error": str(e), "success": False}
    
    async def _scrape_single_url(self, session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
        """Scrape content from a single URL"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with session.get(url, headers=headers, timeout=self.timeout) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract content
                content = self._extract_content(soup)
                
                return {
                    "url": url,
                    "title": soup.title.string if soup.title else "",
                    "content": content,
                    "meta": self._extract_metadata(soup),
                    "links": self._extract_links(soup),
                    "images": self._extract_images(soup),
                    "success": True,
                    "scraped_at": datetime.now().isoformat()
                }
            else:
                raise Exception(f"HTTP {response.status}: {response.reason}")
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML"""
        # Try to find main content area
        content_selectors = [
            'article', 'main', '.content', '.article-content',
            '.post-content', '.entry-content', '#content', '#main'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        # Fallback to body content
        body = soup.find('body')
        if body:
            # Remove script and style elements
            for script in body(["script", "style"]):
                script.decompose()
            
            return body.get_text(strip=True)[:self.max_content_length]
        
        return ""
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from HTML"""
        metadata = {}
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            
            if name and content:
                metadata[name] = content
        
        # Title
        title = soup.find('title')
        if title:
            metadata['title'] = title.string
        
        return metadata
    
    def _extract_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract links from HTML"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http'):
                links.append(href)
        
        return list(set(links))  # Remove duplicates
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract image URLs from HTML"""
        images = []
        for img in soup.find_all('img', src=True):
            src = img['src']
            if src.startswith('http'):
                images.append(src)
        
        return list(set(images))  # Remove duplicates
    
    async def _deep_research(self, task: AgentTask) -> Dict[str, Any]:
        """Perform comprehensive research on a topic"""
        try:
            topic = task.payload.get("topic", "")
            depth = task.payload.get("depth", "medium")  # shallow, medium, deep
            
            if not topic:
                return {"error": "No research topic provided"}
            
            research_report = {
                "topic": topic,
                "depth": depth,
                "started_at": datetime.now().isoformat(),
                "sources": [],
                "key_findings": [],
                "summary": "",
                "related_topics": []
            }
            
            # Phase 1: Initial search
            search_results = await self._perform_web_search(
                AgentTask(
                    id="search_1",
                    type="web_search",
                    description=f"Search for {topic}",
                    priority=task.priority,
                    payload={"query": topic, "max_results": 10},
                    created_at=datetime.now()
                )
            )
            
            if search_results.get("success"):
                # Phase 2: Scrape top results
                top_urls = [result["url"] for result in search_results["results"][:5]]
                
                scraped_data = await self._scrape_urls(
                    AgentTask(
                        id="scrape_1",
                        type="url_scraping",
                        description="Scrape top search results",
                        priority=task.priority,
                        payload={"urls": top_urls},
                        created_at=datetime.now()
                    )
                )
                
                if scraped_data.get("success"):
                    research_report["sources"] = scraped_data["scraped_data"]
                    
                    # Phase 3: Analyze content for key findings
                    research_report["key_findings"] = await self._extract_key_findings(
                        scraped_data["scraped_data"]
                    )
                    
                    # Phase 4: Generate summary
                    research_report["summary"] = await self._generate_research_summary(
                        research_report["key_findings"]
                    )
            
            research_report["completed_at"] = datetime.now().isoformat()
            
            return {
                "research_report": research_report,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Deep research failed: {e}")
            return {"error": str(e), "success": False}
    
    async def _extract_key_findings(self, scraped_data: List[Dict[str, Any]]) -> List[str]:
        """Extract key findings from scraped content"""
        findings = []
        
        for data in scraped_data:
            if data.get("success") and data.get("content"):
                content = data["content"]
                
                # Simple key finding extraction (can be enhanced with NLP)
                sentences = content.split('.')
                
                # Look for sentences with key indicators
                key_indicators = [
                    "research shows", "study found", "according to",
                    "statistics show", "data indicates", "important",
                    "significant", "key", "main", "primary"
                ]
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 50 and any(indicator in sentence.lower() for indicator in key_indicators):
                        findings.append(sentence)
                
                # Limit findings per source
                if len(findings) >= 20:
                    break
        
        return findings[:10]  # Return top 10 findings
    
    async def _generate_research_summary(self, key_findings: List[str]) -> str:
        """Generate a summary from key findings"""
        if not key_findings:
            return "No significant findings identified."
        
        # Simple summary generation (can be enhanced with AI)
        summary_parts = [
            "Research Summary:",
            f"Based on analysis of multiple sources, {len(key_findings)} key findings were identified:",
        ]
        
        for i, finding in enumerate(key_findings[:5], 1):
            summary_parts.append(f"{i}. {finding}")
        
        return "\n".join(summary_parts)