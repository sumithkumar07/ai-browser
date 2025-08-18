import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class AIDataExtractor:
    """
    Phase 2: AI-Powered Data Extraction with Computer Vision
    Enhanced data extraction with intelligent parsing
    """
    
    def __init__(self):
        self.extraction_cache = {}
        self.pattern_library = self._initialize_patterns()
    
    async def extract_intelligent_data(self, source: str, extraction_rules: List[Dict], output_format: str = "json") -> Dict[str, Any]:
        """Extract data using AI-powered intelligent parsing"""
        try:
            extraction_id = str(uuid.uuid4())
            
            # Determine source type
            if source.startswith(('http://', 'https://')):
                data = await self._extract_from_url(source, extraction_rules)
            elif source == "current_page":
                data = await self._extract_from_current_page(extraction_rules)
            else:
                data = await self._extract_from_text(source, extraction_rules)
            
            # Apply AI-powered enhancement
            enhanced_data = await self._enhance_with_ai(data, extraction_rules)
            
            # Format output
            formatted_data = self._format_output(enhanced_data, output_format)
            
            return {
                "extraction_id": extraction_id,
                "success": True,
                "data": formatted_data,
                "metadata": {
                    "source": source,
                    "extraction_rules": extraction_rules,
                    "output_format": output_format,
                    "extracted_at": datetime.utcnow().isoformat(),
                    "data_quality_score": self._calculate_quality_score(enhanced_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "extraction_id": None
            }
    
    async def _extract_from_url(self, url: str, extraction_rules: List[Dict]) -> Dict[str, Any]:
        """Extract data from URL with enhanced parsing"""
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Apply extraction rules
                extracted_data = {}
                for rule in extraction_rules:
                    rule_result = await self._apply_extraction_rule(soup, rule, url)
                    extracted_data.update(rule_result)
                
                # Add automatic content detection
                auto_extracted = await self._auto_extract_content(soup, url)
                extracted_data["auto_detected"] = auto_extracted
                
                return extracted_data
                
        except Exception as e:
            logger.error(f"URL extraction failed for {url}: {e}")
            return {"error": f"Failed to extract from URL: {str(e)}"}
    
    async def _extract_from_current_page(self, extraction_rules: List[Dict]) -> Dict[str, Any]:
        """Extract data from current page context"""
        # This would integrate with the current page context
        # For now, return placeholder data
        return {
            "current_page_data": "Data extraction from current page context",
            "rules_applied": len(extraction_rules)
        }
    
    async def _extract_from_text(self, text: str, extraction_rules: List[Dict]) -> Dict[str, Any]:
        """Extract data from raw text using AI parsing"""
        extracted_data = {}
        
        for rule in extraction_rules:
            rule_type = rule.get("type", "")
            pattern = rule.get("pattern", "")
            
            if rule_type == "regex":
                matches = re.findall(pattern, text, re.IGNORECASE)
                extracted_data[rule.get("name", "matches")] = matches
            elif rule_type == "keyword":
                keywords = rule.get("keywords", [])
                found_keywords = [kw for kw in keywords if kw.lower() in text.lower()]
                extracted_data[rule.get("name", "keywords")] = found_keywords
            elif rule_type == "entity":
                entities = await self._extract_entities(text, rule.get("entity_types", []))
                extracted_data[rule.get("name", "entities")] = entities
        
        return extracted_data
    
    async def _apply_extraction_rule(self, soup: BeautifulSoup, rule: Dict, url: str) -> Dict[str, Any]:
        """Apply a single extraction rule to parsed HTML"""
        rule_name = rule.get("name", "extracted_data")
        rule_type = rule.get("type", "text")
        selector = rule.get("selector", "")
        
        result = {}
        
        try:
            if rule_type == "text":
                elements = soup.select(selector) if selector else [soup]
                texts = [elem.get_text(strip=True) for elem in elements]
                result[rule_name] = texts if len(texts) > 1 else (texts[0] if texts else "")
            
            elif rule_type == "links":
                elements = soup.select(selector) if selector else soup.find_all('a')
                links = []
                for elem in elements:
                    if elem.get('href'):
                        links.append({
                            "text": elem.get_text(strip=True),
                            "href": elem['href'],
                            "title": elem.get('title', '')
                        })
                result[rule_name] = links
            
            elif rule_type == "images":
                elements = soup.select(selector) if selector else soup.find_all('img')
                images = []
                for elem in elements:
                    if elem.get('src'):
                        images.append({
                            "src": elem['src'],
                            "alt": elem.get('alt', ''),
                            "title": elem.get('title', '')
                        })
                result[rule_name] = images
            
            elif rule_type == "table":
                table = soup.select_one(selector) if selector else soup.find('table')
                if table:
                    table_data = self._extract_table_data(table)
                    result[rule_name] = table_data
            
            elif rule_type == "form":
                form = soup.select_one(selector) if selector else soup.find('form')
                if form:
                    form_data = self._extract_form_data(form)
                    result[rule_name] = form_data
            
            elif rule_type == "metadata":
                metadata = self._extract_page_metadata(soup)
                result[rule_name] = metadata
            
            elif rule_type == "structured_data":
                structured = self._extract_structured_data(soup)
                result[rule_name] = structured
            
        except Exception as e:
            logger.error(f"Rule application failed for {rule_name}: {e}")
            result[rule_name] = {"error": str(e)}
        
        return result
    
    async def _auto_extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Automatically detect and extract important content"""
        auto_data = {}
        
        # Extract headlines
        headlines = []
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            text = heading.get_text(strip=True)
            if text and len(text) > 5:
                headlines.append({
                    "level": heading.name,
                    "text": text
                })
        auto_data["headlines"] = headlines[:10]
        
        # Extract article content
        article_selectors = [
            'article',
            '[role="main"]',
            '.content',
            '.post-content',
            '.entry-content',
            'main'
        ]
        
        for selector in article_selectors:
            article = soup.select_one(selector)
            if article:
                content = article.get_text(separator=' ', strip=True)
                if len(content) > 200:
                    auto_data["main_content"] = content[:2000]
                    break
        
        # Extract contact information
        contact_info = await self._extract_contact_info(soup)
        auto_data["contact_info"] = contact_info
        
        # Extract social media links
        social_links = self._extract_social_links(soup)
        auto_data["social_links"] = social_links
        
        # Extract prices/monetary values
        prices = self._extract_prices(soup)
        auto_data["prices"] = prices
        
        # Extract dates
        dates = self._extract_dates(soup)
        auto_data["dates"] = dates
        
        return auto_data
    
    def _extract_table_data(self, table) -> Dict[str, Any]:
        """Extract structured data from HTML table"""
        table_data = {
            "headers": [],
            "rows": [],
            "metadata": {}
        }
        
        # Extract headers
        header_row = table.find('tr')
        if header_row:
            headers = header_row.find_all(['th', 'td'])
            table_data["headers"] = [h.get_text(strip=True) for h in headers]
        
        # Extract data rows
        rows = table.find_all('tr')[1:] if table_data["headers"] else table.find_all('tr')
        for row in rows[:50]:  # Limit for performance
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            if any(row_data):  # Only add non-empty rows
                table_data["rows"].append(row_data)
        
        table_data["metadata"] = {
            "total_rows": len(table_data["rows"]),
            "total_columns": len(table_data["headers"]),
            "has_headers": bool(table_data["headers"])
        }
        
        return table_data
    
    def _extract_form_data(self, form) -> Dict[str, Any]:
        """Extract form structure and fields"""
        form_data = {
            "action": form.get('action', ''),
            "method": form.get('method', 'GET'),
            "fields": [],
            "metadata": {}
        }
        
        for field in form.find_all(['input', 'textarea', 'select']):
            field_info = {
                "name": field.get('name', ''),
                "type": field.get('type', field.name),
                "id": field.get('id', ''),
                "placeholder": field.get('placeholder', ''),
                "required": field.has_attr('required'),
                "value": field.get('value', '')
            }
            
            if field.name == 'select':
                options = [opt.get_text(strip=True) for opt in field.find_all('option')]
                field_info["options"] = options
            
            form_data["fields"].append(field_info)
        
        form_data["metadata"] = {
            "total_fields": len(form_data["fields"]),
            "required_fields": len([f for f in form_data["fields"] if f["required"]]),
            "field_types": list(set(f["type"] for f in form_data["fields"]))
        }
        
        return form_data
    
    def _extract_page_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract page metadata"""
        metadata = {}
        
        # Basic meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        # Page title
        title = soup.find('title')
        if title:
            metadata['title'] = title.get_text(strip=True)
        
        # Canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical:
            metadata['canonical_url'] = canonical.get('href')
        
        return metadata
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract JSON-LD and microdata"""
        structured_data = {
            "json_ld": [],
            "microdata": []
        }
        
        # Extract JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                structured_data["json_ld"].append(data)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Extract microdata (simplified)
        for element in soup.find_all(attrs={'itemscope': True}):
            microdata_item = {
                "type": element.get('itemtype', ''),
                "properties": {}
            }
            
            for prop in element.find_all(attrs={'itemprop': True}):
                prop_name = prop.get('itemprop')
                prop_value = prop.get_text(strip=True) or prop.get('content', '')
                microdata_item["properties"][prop_name] = prop_value
            
            if microdata_item["properties"]:
                structured_data["microdata"].append(microdata_item)
        
        return structured_data
    
    async def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract contact information using patterns"""
        contact_info = {
            "emails": [],
            "phones": [],
            "addresses": []
        }
        
        text_content = soup.get_text()
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        contact_info["emails"] = list(set(emails))[:5]
        
        # Phone pattern (various formats)
        phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phones = re.findall(phone_pattern, text_content)
        formatted_phones = [''.join(phone).strip() for phone in phones if any(phone)]
        contact_info["phones"] = list(set(formatted_phones))[:5]
        
        return contact_info
    
    def _extract_social_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract social media links"""
        social_patterns = {
            'twitter': ['twitter.com', 't.co'],
            'facebook': ['facebook.com', 'fb.com'],
            'instagram': ['instagram.com'],
            'linkedin': ['linkedin.com'],
            'youtube': ['youtube.com', 'youtu.be'],
            'github': ['github.com'],
            'tiktok': ['tiktok.com']
        }
        
        social_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            for platform, domains in social_patterns.items():
                if any(domain in href for domain in domains):
                    social_links.append({
                        "platform": platform,
                        "url": link['href'],
                        "text": link.get_text(strip=True)
                    })
                    break
        
        return social_links[:10]
    
    def _extract_prices(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract price information"""
        price_patterns = [
            r'\$[\d,]+\.?\d*',  # $1,234.56
            r'USD\s*[\d,]+\.?\d*',  # USD 1234.56
            r'€[\d,]+\.?\d*',  # €1,234.56
            r'£[\d,]+\.?\d*',  # £1,234.56
        ]
        
        prices = []
        text_content = soup.get_text()
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text_content)
            for match in matches:
                prices.append({
                    "raw_text": match,
                    "currency": self._detect_currency(match)
                })
        
        return prices[:10]
    
    def _detect_currency(self, price_text: str) -> str:
        """Detect currency from price text"""
        if '$' in price_text:
            return 'USD'
        elif '€' in price_text:
            return 'EUR'
        elif '£' in price_text:
            return 'GBP'
        elif 'USD' in price_text:
            return 'USD'
        return 'unknown'
    
    def _extract_dates(self, soup: BeautifulSoup) -> List[str]:
        """Extract date information"""
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',    # YYYY/MM/DD
            r'[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}',  # January 1, 2024
        ]
        
        dates = []
        text_content = soup.get_text()
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_content)
            dates.extend(matches)
        
        return list(set(dates))[:10]
    
    async def _enhance_with_ai(self, data: Dict[str, Any], extraction_rules: List[Dict]) -> Dict[str, Any]:
        """Enhance extracted data with AI processing"""
        try:
            # This would integrate with the AI manager for content enhancement
            enhanced_data = data.copy()
            
            # Add AI-powered insights
            enhanced_data["ai_insights"] = {
                "content_type": self._classify_content_type(data),
                "key_topics": await self._extract_key_topics(data),
                "sentiment": await self._analyze_sentiment(data),
                "data_quality": self._assess_data_quality(data)
            }
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            return data
    
    def _classify_content_type(self, data: Dict[str, Any]) -> str:
        """Classify the type of content extracted"""
        # Simple heuristic-based classification
        if "prices" in data and data["prices"]:
            return "e-commerce"
        elif "contact_info" in data and data["contact_info"].get("emails"):
            return "business_page"
        elif "headlines" in data and len(data.get("headlines", [])) > 3:
            return "news_article"
        elif "social_links" in data and data["social_links"]:
            return "social_profile"
        else:
            return "general_content"
    
    async def _extract_key_topics(self, data: Dict[str, Any]) -> List[str]:
        """Extract key topics from the data"""
        # Simple keyword extraction (would be enhanced with NLP)
        text_content = ""
        
        if "main_content" in data:
            text_content += data["main_content"]
        
        if "headlines" in data:
            headlines_text = " ".join([h.get("text", "") for h in data["headlines"]])
            text_content += " " + headlines_text
        
        # Simple keyword extraction
        words = re.findall(r'\b[A-Za-z]{4,}\b', text_content.lower())
        word_freq = {}
        
        for word in words:
            if word not in ['this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'said', 'each', 'them']:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10]]
    
    async def _analyze_sentiment(self, data: Dict[str, Any]) -> str:
        """Analyze sentiment of the content"""
        # Simplified sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'horrible', 'disappointing', 'worst']
        
        text_content = ""
        if "main_content" in data:
            text_content = data["main_content"].lower()
        
        positive_count = sum(1 for word in positive_words if word in text_content)
        negative_count = sum(1 for word in negative_words if word in text_content)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of extracted data"""
        quality_score = 0
        total_checks = 0
        
        # Check for completeness
        if "main_content" in data and len(data["main_content"]) > 100:
            quality_score += 1
        total_checks += 1
        
        if "headlines" in data and data["headlines"]:
            quality_score += 1
        total_checks += 1
        
        if "contact_info" in data:
            if data["contact_info"].get("emails") or data["contact_info"].get("phones"):
                quality_score += 1
        total_checks += 1
        
        if "auto_detected" in data and len(data["auto_detected"]) > 2:
            quality_score += 1
        total_checks += 1
        
        final_score = (quality_score / total_checks) * 100 if total_checks > 0 else 0
        
        return {
            "score": round(final_score, 1),
            "completeness": quality_score,
            "total_checks": total_checks,
            "quality_level": "high" if final_score >= 75 else "medium" if final_score >= 50 else "low"
        }
    
    async def _extract_entities(self, text: str, entity_types: List[str]) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        entities = {}
        
        # Simple pattern-based entity extraction
        patterns = {
            "person": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            "organization": r'\b[A-Z][a-zA-Z\s&]+(?:Inc|LLC|Corp|Ltd|Co)\b',
            "location": r'\b[A-Z][a-z]+,?\s+[A-Z]{2}\b',  # City, State
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
        
        for entity_type in entity_types:
            if entity_type in patterns:
                matches = re.findall(patterns[entity_type], text)
                entities[entity_type] = list(set(matches))[:10]
        
        return entities
    
    def _format_output(self, data: Dict[str, Any], format_type: str) -> Any:
        """Format the output data according to specified format"""
        if format_type == "json":
            return data
        elif format_type == "csv":
            return self._convert_to_csv(data)
        elif format_type == "xml":
            return self._convert_to_xml(data)
        else:
            return data
    
    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert data to CSV format (simplified)"""
        csv_lines = []
        
        # Handle tabular data
        if "auto_detected" in data and "headlines" in data["auto_detected"]:
            csv_lines.append("Level,Text")
            for headline in data["auto_detected"]["headlines"]:
                level = headline.get("level", "")
                text = headline.get("text", "").replace(",", ";")
                csv_lines.append(f"{level},{text}")
        
        return "\n".join(csv_lines) if csv_lines else "No tabular data available"
    
    def _convert_to_xml(self, data: Dict[str, Any]) -> str:
        """Convert data to XML format (simplified)"""
        xml_lines = ["<?xml version='1.0' encoding='UTF-8'?>", "<extracted_data>"]
        
        def dict_to_xml(d, indent=2):
            lines = []
            for key, value in d.items():
                if isinstance(value, dict):
                    lines.append(" " * indent + f"<{key}>")
                    lines.extend(dict_to_xml(value, indent + 2))
                    lines.append(" " * indent + f"</{key}>")
                elif isinstance(value, list):
                    lines.append(" " * indent + f"<{key}>")
                    for item in value:
                        if isinstance(item, dict):
                            lines.append(" " * (indent + 2) + "<item>")
                            lines.extend(dict_to_xml(item, indent + 4))
                            lines.append(" " * (indent + 2) + "</item>")
                        else:
                            lines.append(" " * (indent + 2) + f"<item>{str(item)}</item>")
                    lines.append(" " * indent + f"</{key}>")
                else:
                    lines.append(" " * indent + f"<{key}>{str(value)}</{key}>")
            return lines
        
        xml_lines.extend(dict_to_xml(data))
        xml_lines.append("</extracted_data>")
        
        return "\n".join(xml_lines)
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate overall data quality score"""
        if "ai_insights" in data and "data_quality" in data["ai_insights"]:
            return data["ai_insights"]["data_quality"]["score"]
        return 75.0  # Default score
    
    def _initialize_patterns(self) -> Dict[str, Any]:
        """Initialize pattern library for data extraction"""
        return {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            "url": r'https?://[^\s<>"{}|\\^`\[\]]+',
            "price": r'\$[\d,]+\.?\d*',
            "date": r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}'
        }

# Global instance
ai_data_extractor = AIDataExtractor()