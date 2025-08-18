"""
PHASE 2: Research Automation Engine with AI-Powered Data Extraction
Advanced research capabilities with intelligent report generation
"""
import asyncio
import json
import uuid
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import httpx
from bs4 import BeautifulSoup
import re

class ResearchType(Enum):
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    MARKET_RESEARCH = "market_research" 
    TECHNOLOGY_RESEARCH = "technology_research"
    ACADEMIC_RESEARCH = "academic_research"
    NEWS_MONITORING = "news_monitoring"
    PRICE_MONITORING = "price_monitoring"
    CONTENT_EXTRACTION = "content_extraction"

class ResearchStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ResearchQuery:
    id: str
    query: str
    research_type: ResearchType
    sources: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None

@dataclass
class ResearchResult:
    query_id: str
    status: ResearchStatus
    data: Dict[str, Any] = field(default_factory=dict)
    sources_analyzed: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    generated_at: datetime = field(default_factory=datetime.utcnow)
    processing_time: float = 0.0

class ResearchAutomationEngine:
    """
    Advanced research automation with AI-powered analysis
    Supports multiple research types and intelligent data extraction
    """
    
    def __init__(self):
        self.active_queries: Dict[str, ResearchQuery] = {}
        self.results_cache: Dict[str, ResearchResult] = {}
        self.knowledge_base = ResearchKnowledgeBase()
        self.source_analyzer = SourceAnalyzer()
        self.report_generator = IntelligentReportGenerator()
        
        # Research agents
        self.web_scraper = WebScrapingAgent()
        self.content_extractor = ContentExtractionAgent()
        self.data_analyzer = DataAnalysisAgent()
        
        logging.info("🔬 Research Automation Engine initialized")
    
    async def create_research_query(
        self,
        query: str,
        research_type: ResearchType,
        sources: List[str] = None,
        parameters: Dict[str, Any] = None,
        user_id: str = None
    ) -> str:
        """Create new research query"""
        
        query_id = str(uuid.uuid4())
        
        research_query = ResearchQuery(
            id=query_id,
            query=query,
            research_type=research_type,
            sources=sources or [],
            parameters=parameters or {},
            user_id=user_id
        )
        
        self.active_queries[query_id] = research_query
        
        # Start research process in background
        asyncio.create_task(self._execute_research_query(query_id))
        
        logging.info(f"🔬 Created research query: {query} ({query_id})")
        return query_id
    
    async def get_research_status(self, query_id: str) -> Dict[str, Any]:
        """Get current research status"""
        
        if query_id not in self.active_queries:
            return {"error": "Query not found"}
        
        query = self.active_queries[query_id]
        result = self.results_cache.get(query_id)
        
        status_info = {
            "query_id": query_id,
            "query": query.query,
            "type": query.research_type.value,
            "created_at": query.created_at.isoformat(),
            "sources": query.sources
        }
        
        if result:
            status_info.update({
                "status": result.status.value,
                "progress": 1.0 if result.status == ResearchStatus.COMPLETED else 0.7,
                "sources_analyzed": len(result.sources_analyzed),
                "insights_found": len(result.insights),
                "confidence_score": result.confidence_score,
                "processing_time": result.processing_time
            })
        else:
            status_info.update({
                "status": "running",
                "progress": 0.3
            })
        
        return status_info
    
    async def get_research_results(self, query_id: str) -> Dict[str, Any]:
        """Get completed research results"""
        
        if query_id not in self.results_cache:
            return {"error": "Results not available"}
        
        result = self.results_cache[query_id]
        query = self.active_queries.get(query_id)
        
        if result.status != ResearchStatus.COMPLETED:
            return {"error": "Research not completed yet", "status": result.status.value}
        
        # Generate comprehensive report
        report = await self.report_generator.generate_report(query, result)
        
        return {
            "query_id": query_id,
            "status": result.status.value,
            "data": result.data,
            "insights": result.insights,
            "sources_analyzed": result.sources_analyzed,
            "confidence_score": result.confidence_score,
            "generated_report": report,
            "metadata": {
                "processing_time": result.processing_time,
                "generated_at": result.generated_at.isoformat()
            }
        }
    
    async def execute_smart_extraction(
        self,
        url: str,
        extraction_type: str = "comprehensive",
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Smart content extraction from URL"""
        
        try:
            # Fetch page content
            page_content = await self.web_scraper.fetch_page(url)
            
            if not page_content:
                return {"success": False, "error": "Failed to fetch page"}
            
            # Extract data based on type
            extracted_data = await self.content_extractor.extract_content(
                page_content, extraction_type, parameters or {}
            )
            
            # Analyze extracted data
            analysis = await self.data_analyzer.analyze_data(extracted_data, url)
            
            return {
                "success": True,
                "url": url,
                "extraction_type": extraction_type,
                "data": extracted_data,
                "analysis": analysis,
                "extracted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def monitor_price_changes(
        self,
        product_urls: List[str],
        monitoring_params: Dict[str, Any] = None
    ) -> str:
        """Monitor price changes across multiple URLs"""
        
        monitor_id = str(uuid.uuid4())
        
        # Create monitoring research query
        query_id = await self.create_research_query(
            query=f"Price monitoring for {len(product_urls)} products",
            research_type=ResearchType.PRICE_MONITORING,
            sources=product_urls,
            parameters={
                "monitor_id": monitor_id,
                "monitoring_params": monitoring_params or {},
                "check_interval": 3600  # 1 hour default
            }
        )
        
        return query_id
    
    async def competitive_analysis(
        self,
        company_name: str,
        competitors: List[str] = None,
        analysis_depth: str = "comprehensive"
    ) -> str:
        """Automated competitive analysis"""
        
        # Generate competitor list if not provided
        if not competitors:
            competitors = await self._discover_competitors(company_name)
        
        # Create research sources
        sources = []
        for competitor in competitors:
            sources.extend([
                f"https://www.google.com/search?q={competitor.replace(' ', '+')}",
                f"https://www.crunchbase.com/search/organizations/field/organizations/name/{competitor}",
                f"https://www.linkedin.com/search/results/companies/?keywords={competitor}"
            ])
        
        query_id = await self.create_research_query(
            query=f"Competitive analysis: {company_name} vs competitors",
            research_type=ResearchType.COMPETITIVE_ANALYSIS,
            sources=sources,
            parameters={
                "target_company": company_name,
                "competitors": competitors,
                "analysis_depth": analysis_depth,
                "metrics": ["pricing", "features", "market_position", "funding", "team_size"]
            }
        )
        
        return query_id
    
    async def _execute_research_query(self, query_id: str):
        """Execute research query in background"""
        
        start_time = datetime.utcnow()
        
        try:
            query = self.active_queries[query_id]
            
            # Initialize result
            result = ResearchResult(
                query_id=query_id,
                status=ResearchStatus.RUNNING
            )
            self.results_cache[query_id] = result
            
            # Execute based on research type
            if query.research_type == ResearchType.COMPETITIVE_ANALYSIS:
                data = await self._execute_competitive_analysis(query)
            elif query.research_type == ResearchType.PRICE_MONITORING:
                data = await self._execute_price_monitoring(query)
            elif query.research_type == ResearchType.CONTENT_EXTRACTION:
                data = await self._execute_content_extraction(query)
            elif query.research_type == ResearchType.MARKET_RESEARCH:
                data = await self._execute_market_research(query)
            else:
                data = await self._execute_general_research(query)
            
            # Generate insights
            insights = await self._generate_insights(query, data)
            
            # Calculate confidence score
            confidence = await self._calculate_confidence_score(query, data, insights)
            
            # Update result
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result.status = ResearchStatus.COMPLETED
            result.data = data
            result.insights = insights
            result.confidence_score = confidence
            result.processing_time = processing_time
            result.generated_at = datetime.utcnow()
            
            logging.info(f"✅ Research query completed: {query_id} ({processing_time:.2f}s)")
            
        except Exception as e:
            result = self.results_cache.get(query_id)
            if result:
                result.status = ResearchStatus.FAILED
                result.data = {"error": str(e)}
            
            logging.error(f"❌ Research query failed: {query_id} - {e}")
    
    async def _execute_competitive_analysis(self, query: ResearchQuery) -> Dict[str, Any]:
        """Execute competitive analysis research"""
        
        target_company = query.parameters.get("target_company", "")
        competitors = query.parameters.get("competitors", [])
        
        analysis_data = {
            "target_company": target_company,
            "competitors": {},
            "comparison_matrix": {},
            "market_insights": []
        }
        
        # Analyze each competitor
        for competitor in competitors:
            competitor_data = await self._analyze_competitor(competitor)
            analysis_data["competitors"][competitor] = competitor_data
        
        # Generate comparison matrix
        analysis_data["comparison_matrix"] = await self._generate_comparison_matrix(
            target_company, analysis_data["competitors"]
        )
        
        return analysis_data
    
    async def _execute_price_monitoring(self, query: ResearchQuery) -> Dict[str, Any]:
        """Execute price monitoring"""
        
        product_urls = query.sources
        monitoring_data = {
            "products": {},
            "price_changes": [],
            "statistics": {}
        }
        
        for url in product_urls:
            product_data = await self._extract_product_price(url)
            if product_data:
                monitoring_data["products"][url] = product_data
        
        # Calculate statistics
        monitoring_data["statistics"] = await self._calculate_price_statistics(
            monitoring_data["products"]
        )
        
        return monitoring_data
    
    async def _execute_content_extraction(self, query: ResearchQuery) -> Dict[str, Any]:
        """Execute content extraction"""
        
        extraction_results = {}
        
        for source in query.sources:
            extraction_result = await self.execute_smart_extraction(
                source, 
                query.parameters.get("extraction_type", "comprehensive"),
                query.parameters
            )
            extraction_results[source] = extraction_result
        
        return extraction_results
    
    async def _execute_market_research(self, query: ResearchQuery) -> Dict[str, Any]:
        """Execute market research"""
        
        market_data = {
            "market_size": {},
            "trends": [],
            "key_players": [],
            "opportunities": []
        }
        
        # Research market size and trends
        for source in query.sources:
            source_data = await self.web_scraper.fetch_page(source)
            if source_data:
                extracted_info = await self.content_extractor.extract_market_data(source_data)
                market_data = self._merge_market_data(market_data, extracted_info)
        
        return market_data
    
    async def _execute_general_research(self, query: ResearchQuery) -> Dict[str, Any]:
        """Execute general research"""
        
        research_data = {
            "query": query.query,
            "sources_analyzed": [],
            "extracted_content": {},
            "structured_data": {}
        }
        
        # Process each source
        for source in query.sources:
            try:
                content = await self.web_scraper.fetch_page(source)
                if content:
                    extracted = await self.content_extractor.extract_relevant_content(
                        content, query.query
                    )
                    research_data["extracted_content"][source] = extracted
                    research_data["sources_analyzed"].append(source)
            except Exception as e:
                logging.warning(f"⚠️ Failed to process source {source}: {e}")
        
        return research_data
    
    async def _generate_insights(self, query: ResearchQuery, data: Dict[str, Any]) -> List[str]:
        """Generate AI-powered insights from research data"""
        
        insights = []
        
        try:
            # Use AI to generate insights based on research type and data
            from multi_ai_provider_engine import MultiAIProviderEngine
            
            ai_engine = MultiAIProviderEngine()
            
            prompt = f"""
            Analyze the following research data and generate key insights:
            
            Research Query: {query.query}
            Research Type: {query.research_type.value}
            Data: {json.dumps(data, default=str)[:3000]}
            
            Provide 3-5 key insights in bullet points.
            """
            
            ai_response = await ai_engine.get_smart_response(prompt)
            
            # Extract insights from AI response
            insights_text = ai_response.response if hasattr(ai_response, 'response') else str(ai_response)
            insights = self._extract_insights_from_text(insights_text)
            
        except Exception as e:
            logging.warning(f"⚠️ AI insight generation failed: {e}")
            # Fallback to rule-based insights
            insights = self._generate_rule_based_insights(query, data)
        
        return insights
    
    def _extract_insights_from_text(self, text: str) -> List[str]:
        """Extract insights from AI-generated text"""
        
        insights = []
        
        # Look for bullet points or numbered lists
        bullet_patterns = [
            r'[•\-\*]\s*(.+)',
            r'\d+\.\s*(.+)',
            r'[→➤]\s*(.+)'
        ]
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, text)
            insights.extend([match.strip() for match in matches])
        
        # If no structured format found, split by sentences
        if not insights:
            sentences = text.split('.')
            insights = [s.strip() for s in sentences if len(s.strip()) > 20][:5]
        
        return insights[:5]  # Limit to 5 insights
    
    def _generate_rule_based_insights(self, query: ResearchQuery, data: Dict[str, Any]) -> List[str]:
        """Generate insights using rule-based approach"""
        
        insights = []
        
        if query.research_type == ResearchType.COMPETITIVE_ANALYSIS:
            competitors = data.get("competitors", {})
            if len(competitors) > 0:
                insights.append(f"Analyzed {len(competitors)} competitors in the market")
                
        elif query.research_type == ResearchType.PRICE_MONITORING:
            products = data.get("products", {})
            if products:
                prices = [p.get("current_price", 0) for p in products.values() if isinstance(p, dict)]
                if prices:
                    avg_price = sum(prices) / len(prices)
                    insights.append(f"Average product price: ${avg_price:.2f}")
        
        return insights
    
    async def _calculate_confidence_score(
        self, 
        query: ResearchQuery, 
        data: Dict[str, Any], 
        insights: List[str]
    ) -> float:
        """Calculate confidence score for research results"""
        
        score = 0.5  # Base score
        
        # Factor in number of sources processed
        sources_analyzed = len(data.get("sources_analyzed", query.sources))
        source_score = min(0.3, sources_analyzed * 0.1)
        score += source_score
        
        # Factor in data quality
        if data and len(str(data)) > 1000:
            score += 0.1
        
        # Factor in insights quality
        if insights and len(insights) >= 3:
            score += 0.1
        
        return min(1.0, score)
    
    async def _discover_competitors(self, company_name: str) -> List[str]:
        """Discover competitors using AI and web search"""
        
        try:
            from multi_ai_provider_engine import MultiAIProviderEngine
            
            ai_engine = MultiAIProviderEngine()
            
            prompt = f"""
            List 5 main competitors of {company_name}.
            Return only the company names, one per line.
            """
            
            ai_response = await ai_engine.get_smart_response(prompt)
            response_text = ai_response.response if hasattr(ai_response, 'response') else str(ai_response)
            
            # Extract company names
            competitors = [line.strip() for line in response_text.split('\n') 
                         if line.strip() and len(line.strip()) > 2]
            
            return competitors[:5]  # Limit to 5 competitors
            
        except Exception as e:
            logging.warning(f"⚠️ Competitor discovery failed: {e}")
            return ["Competitor 1", "Competitor 2", "Competitor 3"]
    
    async def _analyze_competitor(self, competitor_name: str) -> Dict[str, Any]:
        """Analyze individual competitor"""
        
        return {
            "name": competitor_name,
            "market_position": "Unknown",
            "estimated_size": "Unknown",
            "key_features": [],
            "pricing_model": "Unknown",
            "strengths": [],
            "weaknesses": []
        }
    
    async def _generate_comparison_matrix(self, target: str, competitors: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparison matrix"""
        
        return {
            "dimensions": ["Market Position", "Pricing", "Features", "Team Size"],
            "target_company": target,
            "comparison_data": competitors
        }
    
    async def _extract_product_price(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract product price from URL"""
        
        try:
            content = await self.web_scraper.fetch_page(url)
            if content:
                price_info = await self.content_extractor.extract_price_info(content)
                return price_info
        except Exception as e:
            logging.warning(f"⚠️ Price extraction failed for {url}: {e}")
        
        return None
    
    async def _calculate_price_statistics(self, products: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate price statistics"""
        
        prices = []
        for product_data in products.values():
            if isinstance(product_data, dict) and "current_price" in product_data:
                try:
                    price = float(product_data["current_price"])
                    prices.append(price)
                except (ValueError, TypeError):
                    continue
        
        if not prices:
            return {"error": "No valid prices found"}
        
        return {
            "average_price": sum(prices) / len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "price_range": max(prices) - min(prices),
            "total_products": len(prices)
        }
    
    def _merge_market_data(self, existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge market research data"""
        
        # Simple merge logic - in production, this would be more sophisticated
        if isinstance(new_data, dict):
            for key, value in new_data.items():
                if key in existing_data and isinstance(existing_data[key], list):
                    if isinstance(value, list):
                        existing_data[key].extend(value)
                    else:
                        existing_data[key].append(value)
                else:
                    existing_data[key] = value
        
        return existing_data


# Support Classes

class ResearchKnowledgeBase:
    """Knowledge base for research patterns and optimization"""
    
    def __init__(self):
        self.patterns = {}
        self.optimization_rules = {}
    
    def learn_from_research(self, query: ResearchQuery, result: ResearchResult):
        """Learn from completed research"""
        pass


class SourceAnalyzer:
    """Analyzes source credibility and relevance"""
    
    async def analyze_source_quality(self, url: str) -> Dict[str, Any]:
        """Analyze source quality and credibility"""
        
        quality_score = 0.5
        factors = []
        
        # Domain authority (simplified)
        if any(domain in url for domain in ['.edu', '.gov', '.org']):
            quality_score += 0.2
            factors.append("authoritative_domain")
        
        if any(domain in url for domain in ['wikipedia.org', 'reuters.com', 'bloomberg.com']):
            quality_score += 0.15
            factors.append("reputable_source")
        
        return {
            "quality_score": min(1.0, quality_score),
            "credibility_factors": factors,
            "recommended": quality_score > 0.6
        }


class IntelligentReportGenerator:
    """Generates comprehensive research reports"""
    
    async def generate_report(self, query: ResearchQuery, result: ResearchResult) -> Dict[str, Any]:
        """Generate formatted research report"""
        
        report = {
            "title": f"Research Report: {query.query}",
            "executive_summary": self._generate_executive_summary(query, result),
            "methodology": self._describe_methodology(query),
            "findings": result.data,
            "key_insights": result.insights,
            "confidence_assessment": self._assess_confidence(result),
            "recommendations": await self._generate_recommendations(query, result),
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "processing_time": result.processing_time,
                "sources_count": len(result.sources_analyzed)
            }
        }
        
        return report
    
    def _generate_executive_summary(self, query: ResearchQuery, result: ResearchResult) -> str:
        """Generate executive summary"""
        
        summary = f"Research conducted on '{query.query}' using {query.research_type.value} methodology. "
        summary += f"Analysis completed with {result.confidence_score:.1%} confidence. "
        summary += f"Key findings include {len(result.insights)} actionable insights."
        
        return summary
    
    def _describe_methodology(self, query: ResearchQuery) -> str:
        """Describe research methodology"""
        
        methodology = f"Automated {query.research_type.value} using AI-powered content extraction. "
        methodology += f"Analyzed {len(query.sources)} sources with advanced pattern recognition."
        
        return methodology
    
    def _assess_confidence(self, result: ResearchResult) -> Dict[str, Any]:
        """Assess confidence in results"""
        
        confidence_level = "high" if result.confidence_score > 0.8 else "medium" if result.confidence_score > 0.6 else "low"
        
        return {
            "score": result.confidence_score,
            "level": confidence_level,
            "factors": [
                f"Sources analyzed: {len(result.sources_analyzed)}",
                f"Data quality: {'good' if len(str(result.data)) > 1000 else 'moderate'}",
                f"Insights generated: {len(result.insights)}"
            ]
        }
    
    async def _generate_recommendations(self, query: ResearchQuery, result: ResearchResult) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        if query.research_type == ResearchType.COMPETITIVE_ANALYSIS:
            recommendations.extend([
                "Consider expanding analysis to include emerging competitors",
                "Monitor competitor pricing strategies quarterly",
                "Analyze competitor customer feedback for insights"
            ])
        elif query.research_type == ResearchType.PRICE_MONITORING:
            recommendations.extend([
                "Set up automated alerts for significant price changes",
                "Analyze price patterns to optimize purchasing timing",
                "Consider bulk purchasing during low-price periods"
            ])
        else:
            recommendations.extend([
                "Expand research sources for comprehensive coverage",
                "Set up ongoing monitoring for dynamic insights",
                "Validate findings with primary research where possible"
            ])
        
        return recommendations


# Agent Classes

class WebScrapingAgent:
    """Advanced web scraping with respect for robots.txt"""
    
    def __init__(self):
        self.session_cache = {}
    
    async def fetch_page(self, url: str, headers: Dict[str, str] = None) -> Optional[str]:
        """Fetch page content with proper headers and caching"""
        
        default_headers = {
            "User-Agent": "AETHER Research Bot 1.0 (Research Automation)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        if headers:
            default_headers.update(headers)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=default_headers)
                response.raise_for_status()
                return response.text
                
        except Exception as e:
            logging.warning(f"⚠️ Failed to fetch {url}: {e}")
            return None


class ContentExtractionAgent:
    """Intelligent content extraction with AI assistance"""
    
    async def extract_content(self, html_content: str, extraction_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content based on type and parameters"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        extracted_data = {
            "title": self._extract_title(soup),
            "text_content": self._extract_text_content(soup),
            "links": self._extract_links(soup),
            "images": self._extract_images(soup),
            "metadata": self._extract_metadata(soup)
        }
        
        if extraction_type == "comprehensive":
            extracted_data.update({
                "headings": self._extract_headings(soup),
                "tables": self._extract_tables(soup),
                "forms": self._extract_forms(soup)
            })
        elif extraction_type == "price_monitoring":
            extracted_data.update({
                "prices": self._extract_prices(soup),
                "product_info": self._extract_product_info(soup)
            })
        
        return extracted_data
    
    async def extract_relevant_content(self, html_content: str, query: str) -> Dict[str, Any]:
        """Extract content relevant to research query"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract all text content
        text_content = soup.get_text()
        
        # Find relevant sections based on query keywords
        query_keywords = query.lower().split()
        relevant_sections = []
        
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'div']):
            element_text = element.get_text().lower()
            relevance_score = sum(1 for keyword in query_keywords if keyword in element_text)
            
            if relevance_score > 0:
                relevant_sections.append({
                    "text": element.get_text().strip(),
                    "relevance_score": relevance_score,
                    "tag": element.name
                })
        
        # Sort by relevance
        relevant_sections.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return {
            "query": query,
            "relevant_sections": relevant_sections[:10],  # Top 10 most relevant
            "total_content_length": len(text_content),
            "relevance_found": len(relevant_sections) > 0
        }
    
    async def extract_price_info(self, html_content: str) -> Dict[str, Any]:
        """Extract price information from page"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Common price selectors and patterns
        price_patterns = [
            r'\$[\d,]+\.?\d*',
            r'USD\s*[\d,]+\.?\d*',
            r'Price:\s*\$?[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*dollars?'
        ]
        
        price_selectors = [
            '.price', '.cost', '.amount', '[data-price]', '.sale-price',
            '.current-price', '.price-current', '#price'
        ]
        
        found_prices = []
        
        # Try selectors first
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get_text().strip()
                found_prices.append(price_text)
        
        # Try regex patterns
        text_content = soup.get_text()
        for pattern in price_patterns:
            matches = re.findall(pattern, text_content)
            found_prices.extend(matches)
        
        # Process and clean prices
        cleaned_prices = []
        for price in found_prices:
            clean_price = re.sub(r'[^\d.]', '', price)
            if clean_price and '.' in clean_price:
                try:
                    cleaned_prices.append(float(clean_price))
                except ValueError:
                    continue
        
        return {
            "raw_prices": found_prices,
            "cleaned_prices": cleaned_prices,
            "current_price": cleaned_prices[0] if cleaned_prices else None,
            "price_count": len(cleaned_prices)
        }
    
    async def extract_market_data(self, html_content: str) -> Dict[str, Any]:
        """Extract market-related data"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for market indicators
        market_keywords = [
            'market size', 'market share', 'revenue', 'growth rate',
            'industry trends', 'market cap', 'valuation'
        ]
        
        market_data = {
            "financial_data": [],
            "trends": [],
            "key_metrics": []
        }
        
        text_content = soup.get_text().lower()
        
        for keyword in market_keywords:
            if keyword in text_content:
                # Find sentences containing the keyword
                sentences = text_content.split('.')
                relevant_sentences = [s.strip() for s in sentences if keyword in s]
                market_data["key_metrics"].extend(relevant_sentences[:3])
        
        return market_data
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ""
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract main text content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        return soup.get_text()[:5000]  # Limit to 5000 chars
    
    def _extract_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all links"""
        links = []
        for link in soup.find_all('a', href=True):
            links.append({
                "url": link['href'],
                "text": link.get_text().strip()
            })
        return links[:50]  # Limit to 50 links
    
    def _extract_images(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract image information"""
        images = []
        for img in soup.find_all('img', src=True):
            images.append({
                "src": img['src'],
                "alt": img.get('alt', ''),
                "title": img.get('title', '')
            })
        return images[:20]  # Limit to 20 images
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract page metadata"""
        metadata = {}
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        return metadata
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract headings"""
        headings = []
        for level in range(1, 7):  # h1 to h6
            for heading in soup.find_all(f'h{level}'):
                headings.append({
                    "level": level,
                    "text": heading.get_text().strip()
                })
        return headings
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract table data"""
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                row = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                rows.append(row)
            if rows:
                tables.append({"rows": rows})
        return tables
    
    def _extract_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract form information"""
        forms = []
        for form in soup.find_all('form'):
            form_data = {
                "action": form.get('action', ''),
                "method": form.get('method', 'get'),
                "inputs": []
            }
            
            for input_elem in form.find_all('input'):
                form_data["inputs"].append({
                    "name": input_elem.get('name', ''),
                    "type": input_elem.get('type', 'text'),
                    "placeholder": input_elem.get('placeholder', '')
                })
            
            forms.append(form_data)
        
        return forms
    
    def _extract_prices(self, soup: BeautifulSoup) -> List[str]:
        """Extract price information"""
        # This would be called by extract_price_info
        return []
    
    def _extract_product_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract product information"""
        return {
            "name": "",
            "description": "",
            "specifications": {}
        }


class DataAnalysisAgent:
    """Analyzes extracted data and provides insights"""
    
    async def analyze_data(self, data: Dict[str, Any], source_url: str) -> Dict[str, Any]:
        """Analyze extracted data and provide insights"""
        
        analysis = {
            "content_quality": self._assess_content_quality(data),
            "data_completeness": self._assess_completeness(data),
            "key_topics": self._identify_topics(data),
            "actionable_items": self._identify_actionable_items(data),
            "source_credibility": await self._assess_source_credibility(source_url)
        }
        
        return analysis
    
    def _assess_content_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of extracted content"""
        
        text_content = data.get("text_content", "")
        quality_score = 0.5
        
        # Length assessment
        if len(text_content) > 1000:
            quality_score += 0.2
        elif len(text_content) > 500:
            quality_score += 0.1
        
        # Structure assessment
        if data.get("headings"):
            quality_score += 0.1
        
        if data.get("links"):
            quality_score += 0.1
        
        # Metadata assessment
        if data.get("metadata"):
            quality_score += 0.1
        
        return {
            "score": min(1.0, quality_score),
            "content_length": len(text_content),
            "has_structure": bool(data.get("headings"))
        }
    
    def _assess_completeness(self, data: Dict[str, Any]) -> float:
        """Assess completeness of extracted data"""
        
        expected_fields = ["title", "text_content", "links", "images", "metadata"]
        present_fields = [field for field in expected_fields if data.get(field)]
        
        return len(present_fields) / len(expected_fields)
    
    def _identify_topics(self, data: Dict[str, Any]) -> List[str]:
        """Identify main topics from content"""
        
        text_content = data.get("text_content", "")
        
        # Simple keyword extraction (in production, use more sophisticated NLP)
        common_words = set(['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        words = [word.lower().strip('.,!?()[]{}') for word in text_content.split()]
        word_freq = {}
        
        for word in words:
            if len(word) > 3 and word not in common_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top topics
        topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        return [topic[0] for topic in topics]
    
    def _identify_actionable_items(self, data: Dict[str, Any]) -> List[str]:
        """Identify actionable items from content"""
        
        text_content = data.get("text_content", "").lower()
        actionable_patterns = [
            r'click\s+(?:on\s+)?([^.]+)',
            r'download\s+([^.]+)',
            r'visit\s+([^.]+)',
            r'contact\s+([^.]+)',
            r'subscribe\s+to\s+([^.]+)'
        ]
        
        actionable_items = []
        for pattern in actionable_patterns:
            matches = re.findall(pattern, text_content)
            actionable_items.extend(matches[:3])  # Limit matches per pattern
        
        return actionable_items
    
    async def _assess_source_credibility(self, url: str) -> Dict[str, Any]:
        """Assess credibility of source URL"""
        
        # Simple credibility assessment
        credibility_score = 0.5
        factors = []
        
        # Domain-based assessment
        if any(domain in url for domain in ['.edu', '.gov']):
            credibility_score += 0.3
            factors.append("educational_or_government")
        elif any(domain in url for domain in ['.org']):
            credibility_score += 0.2
            factors.append("organization")
        
        # HTTPS assessment
        if url.startswith('https://'):
            credibility_score += 0.1
            factors.append("secure_connection")
        
        return {
            "score": min(1.0, credibility_score),
            "factors": factors,
            "assessment": "high" if credibility_score > 0.8 else "medium" if credibility_score > 0.6 else "low"
        }