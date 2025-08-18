import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

class AdvancedReportGenerator:
    """
    Phase 2 & 4: Advanced Report Generation System
    AI-powered report generation with multiple formats and intelligent insights
    """
    
    def __init__(self):
        self.report_templates = self._load_report_templates()
        self.generated_reports = {}
    
    async def generate_intelligent_report(self, data_sources: List[Dict], report_type: str = "summary", output_format: str = "html") -> Dict[str, Any]:
        """Generate intelligent report with AI analysis"""
        try:
            report_id = str(uuid.uuid4())
            
            # Collect and process data from sources
            processed_data = await self._process_data_sources(data_sources)
            
            # Generate AI-powered insights
            insights = await self._generate_ai_insights(processed_data, report_type)
            
            # Create report structure
            report_structure = await self._create_report_structure(processed_data, insights, report_type)
            
            # Format report according to output format
            formatted_report = await self._format_report(report_structure, output_format)
            
            # Store report
            report_metadata = {
                "report_id": report_id,
                "report_type": report_type,
                "output_format": output_format,
                "data_sources": data_sources,
                "generated_at": datetime.utcnow(),
                "insights": insights,
                "structure": report_structure,
                "formatted_content": formatted_report
            }
            
            self.generated_reports[report_id] = report_metadata
            
            return {
                "success": True,
                "report_id": report_id,
                "report_content": formatted_report,
                "insights": insights,
                "metadata": {
                    "data_sources_count": len(data_sources),
                    "insights_count": len(insights.get("key_insights", [])),
                    "report_length": len(formatted_report) if isinstance(formatted_report, str) else 0,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "report_id": None
            }
    
    async def _process_data_sources(self, data_sources: List[Dict]) -> Dict[str, Any]:
        """Process and consolidate data from multiple sources"""
        processed_data = {
            "web_content": [],
            "structured_data": [],
            "social_data": [],
            "file_data": [],
            "api_data": [],
            "metadata": {
                "total_sources": len(data_sources),
                "successful_extractions": 0,
                "failed_extractions": 0
            }
        }
        
        for source in data_sources:
            try:
                source_type = source.get("type", "web")
                source_url = source.get("url", "")
                source_data = source.get("data", {})
                
                if source_type == "web":
                    web_data = await self._process_web_source(source_url, source_data)
                    processed_data["web_content"].append(web_data)
                elif source_type == "social":
                    social_data = await self._process_social_source(source_url, source_data)
                    processed_data["social_data"].append(social_data)
                elif source_type == "api":
                    api_data = await self._process_api_source(source_url, source_data)
                    processed_data["api_data"].append(api_data)
                elif source_type == "file":
                    file_data = await self._process_file_source(source_data)
                    processed_data["file_data"].append(file_data)
                
                processed_data["metadata"]["successful_extractions"] += 1
                
            except Exception as e:
                logger.error(f"Data source processing failed: {e}")
                processed_data["metadata"]["failed_extractions"] += 1
        
        return processed_data
    
    async def _process_web_source(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process web source data"""
        # This would integrate with the enhanced browser engine
        from native_browser_engine import enhanced_browser_engine
        
        if url:
            # Fetch fresh data from URL
            result = await enhanced_browser_engine.navigate_with_automation(url)
            return {
                "source_url": url,
                "page_data": result.get("page_data", {}),
                "type": "web_fresh",
                "processed_at": datetime.utcnow().isoformat()
            }
        else:
            # Use provided data
            return {
                "source_url": "provided_data",
                "page_data": data,
                "type": "web_provided",
                "processed_at": datetime.utcnow().isoformat()
            }
    
    async def _process_social_source(self, platform: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process social media source data"""
        return {
            "platform": platform,
            "social_data": data,
            "type": "social",
            "processed_at": datetime.utcnow().isoformat(),
            "engagement_metrics": self._calculate_social_metrics(data)
        }
    
    async def _process_api_source(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process API source data"""
        return {
            "api_endpoint": endpoint,
            "api_data": data,
            "type": "api",
            "processed_at": datetime.utcnow().isoformat()
        }
    
    async def _process_file_source(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process file source data"""
        return {
            "file_type": data.get("file_type", "unknown"),
            "file_data": data,
            "type": "file",
            "processed_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_social_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate social media engagement metrics"""
        return {
            "total_posts": data.get("posts_count", 0),
            "total_engagement": data.get("likes", 0) + data.get("comments", 0) + data.get("shares", 0),
            "engagement_rate": data.get("engagement_rate", 0.0),
            "top_performing_post": data.get("top_post", {})
        }
    
    async def _generate_ai_insights(self, processed_data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Generate AI-powered insights from processed data"""
        try:
            # This would integrate with the enhanced AI manager
            from enhanced_ai_manager import enhanced_ai_manager
            
            # Prepare data for AI analysis
            analysis_prompt = self._create_analysis_prompt(processed_data, report_type)
            
            # Get AI insights
            ai_response = await enhanced_ai_manager.get_enhanced_ai_response(
                message=analysis_prompt,
                context=None,
                session_history=[],
                query_type="data_analysis"
            )
            
            # Parse AI response into structured insights
            insights = self._parse_ai_insights(ai_response.get("response", ""))
            
            # Add automated analysis
            automated_insights = await self._generate_automated_insights(processed_data)
            
            # Combine AI and automated insights
            combined_insights = {
                "ai_insights": insights,
                "automated_insights": automated_insights,
                "key_insights": self._extract_key_insights(insights, automated_insights),
                "recommendations": self._generate_recommendations(processed_data, insights),
                "confidence_score": self._calculate_confidence_score(processed_data, insights)
            }
            
            return combined_insights
            
        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return await self._generate_automated_insights(processed_data)
    
    def _create_analysis_prompt(self, processed_data: Dict[str, Any], report_type: str) -> str:
        """Create analysis prompt for AI"""
        data_summary = {
            "web_sources": len(processed_data.get("web_content", [])),
            "social_sources": len(processed_data.get("social_data", [])),
            "api_sources": len(processed_data.get("api_data", [])),
            "total_sources": processed_data.get("metadata", {}).get("total_sources", 0)
        }
        
        # Extract key content for analysis
        key_content = []
        
        # Add web content
        for web_item in processed_data.get("web_content", []):
            page_data = web_item.get("page_data", {})
            if page_data.get("content"):
                key_content.append(page_data["content"][:1000])
        
        # Add social data
        for social_item in processed_data.get("social_data", []):
            social_data = social_item.get("social_data", {})
            if social_data.get("content"):
                key_content.append(social_data["content"][:500])
        
        prompt = f"""
        Analyze the following data and provide insights for a {report_type} report:
        
        Data Summary: {json.dumps(data_summary)}
        
        Key Content:
        {chr(10).join(key_content[:5])}  # Limit content for token efficiency
        
        Please provide:
        1. Key themes and patterns
        2. Important findings
        3. Trends and insights
        4. Actionable recommendations
        5. Data quality assessment
        
        Format as structured JSON with sections for each insight type.
        """
        
        return prompt
    
    def _parse_ai_insights(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response into structured insights"""
        try:
            # Try to extract JSON from AI response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback to text parsing
                return {
                    "summary": ai_response[:500],
                    "key_points": self._extract_key_points_from_text(ai_response),
                    "recommendations": self._extract_recommendations_from_text(ai_response)
                }
        except Exception as e:
            logger.error(f"AI insights parsing failed: {e}")
            return {
                "summary": "AI analysis completed with basic insights",
                "key_points": ["Data processed successfully"],
                "recommendations": ["Continue monitoring data trends"]
            }
    
    def _extract_key_points_from_text(self, text: str) -> List[str]:
        """Extract key points from unstructured text"""
        # Simple extraction based on patterns
        lines = text.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if any(indicator in line.lower() for indicator in ['key', 'important', 'significant', 'finding', 'trend']):
                if len(line) > 20 and len(line) < 200:
                    key_points.append(line)
        
        return key_points[:5]
    
    def _extract_recommendations_from_text(self, text: str) -> List[str]:
        """Extract recommendations from unstructured text"""
        lines = text.split('\n')
        recommendations = []
        
        for line in lines:
            line = line.strip()
            if any(indicator in line.lower() for indicator in ['recommend', 'suggest', 'should', 'could', 'action']):
                if len(line) > 20 and len(line) < 200:
                    recommendations.append(line)
        
        return recommendations[:5]
    
    async def _generate_automated_insights(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate automated insights without AI"""
        insights = {
            "data_summary": {
                "total_web_sources": len(processed_data.get("web_content", [])),
                "total_social_sources": len(processed_data.get("social_data", [])),
                "total_api_sources": len(processed_data.get("api_data", [])),
                "processing_success_rate": self._calculate_success_rate(processed_data)
            },
            "content_analysis": {
                "total_content_length": self._calculate_total_content_length(processed_data),
                "dominant_themes": await self._extract_dominant_themes(processed_data),
                "content_quality_score": self._assess_content_quality(processed_data)
            },
            "temporal_analysis": {
                "data_freshness": self._assess_data_freshness(processed_data),
                "update_frequency": "daily"  # Could be calculated from timestamps
            }
        }
        
        return insights
    
    def _calculate_success_rate(self, processed_data: Dict[str, Any]) -> float:
        """Calculate processing success rate"""
        metadata = processed_data.get("metadata", {})
        total = metadata.get("total_sources", 0)
        successful = metadata.get("successful_extractions", 0)
        
        return (successful / total * 100) if total > 0 else 0.0
    
    def _calculate_total_content_length(self, processed_data: Dict[str, Any]) -> int:
        """Calculate total content length across all sources"""
        total_length = 0
        
        for web_item in processed_data.get("web_content", []):
            content = web_item.get("page_data", {}).get("content", "")
            total_length += len(content)
        
        for social_item in processed_data.get("social_data", []):
            content = social_item.get("social_data", {}).get("content", "")
            total_length += len(content)
        
        return total_length
    
    async def _extract_dominant_themes(self, processed_data: Dict[str, Any]) -> List[str]:
        """Extract dominant themes from content"""
        all_content = []
        
        # Collect all text content
        for web_item in processed_data.get("web_content", []):
            content = web_item.get("page_data", {}).get("content", "")
            all_content.append(content)
        
        # Simple keyword extraction
        combined_content = " ".join(all_content).lower()
        words = combined_content.split()
        
        # Count word frequency (excluding common words)
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        word_freq = {}
        
        for word in words:
            word = word.strip('.,!?";')
            if len(word) > 3 and word not in common_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top themes
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10]]
    
    def _assess_content_quality(self, processed_data: Dict[str, Any]) -> float:
        """Assess overall content quality"""
        quality_factors = []
        
        # Check content length diversity
        content_lengths = []
        for web_item in processed_data.get("web_content", []):
            content = web_item.get("page_data", {}).get("content", "")
            content_lengths.append(len(content))
        
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            quality_factors.append(min(avg_length / 1000, 1.0))  # Normalize to 0-1
        
        # Check source diversity
        source_types = len([k for k, v in processed_data.items() if k != "metadata" and v])
        quality_factors.append(min(source_types / 4, 1.0))  # Normalize to 0-1
        
        # Check success rate
        success_rate = self._calculate_success_rate(processed_data) / 100
        quality_factors.append(success_rate)
        
        return sum(quality_factors) / len(quality_factors) * 100 if quality_factors else 50.0
    
    def _assess_data_freshness(self, processed_data: Dict[str, Any]) -> str:
        """Assess how fresh/recent the data is"""
        current_time = datetime.utcnow()
        timestamps = []
        
        for web_item in processed_data.get("web_content", []):
            timestamp_str = web_item.get("processed_at", "")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    timestamps.append(timestamp)
                except:
                    continue
        
        if timestamps:
            most_recent = max(timestamps)
            time_diff = current_time - most_recent
            
            if time_diff.total_seconds() < 3600:  # < 1 hour
                return "very_fresh"
            elif time_diff.total_seconds() < 86400:  # < 1 day
                return "fresh"
            elif time_diff.total_seconds() < 604800:  # < 1 week
                return "recent"
            else:
                return "stale"
        
        return "unknown"
    
    def _extract_key_insights(self, ai_insights: Dict[str, Any], automated_insights: Dict[str, Any]) -> List[str]:
        """Extract and combine key insights"""
        key_insights = []
        
        # From AI insights
        if "key_points" in ai_insights:
            key_insights.extend(ai_insights["key_points"][:3])
        
        # From automated insights
        data_summary = automated_insights.get("data_summary", {})
        content_analysis = automated_insights.get("content_analysis", {})
        
        if data_summary.get("processing_success_rate", 0) > 90:
            key_insights.append("High data processing success rate indicates reliable data sources")
        
        if content_analysis.get("content_quality_score", 0) > 75:
            key_insights.append("Content quality is high across analyzed sources")
        
        themes = content_analysis.get("dominant_themes", [])
        if themes:
            key_insights.append(f"Key themes identified: {', '.join(themes[:3])}")
        
        return key_insights[:5]
    
    def _generate_recommendations(self, processed_data: Dict[str, Any], insights: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Data quality recommendations
        success_rate = self._calculate_success_rate(processed_data)
        if success_rate < 80:
            recommendations.append("Consider reviewing data source reliability and improving error handling")
        
        # Content recommendations
        total_sources = processed_data.get("metadata", {}).get("total_sources", 0)
        if total_sources < 3:
            recommendations.append("Expand data source diversity for more comprehensive analysis")
        
        # AI recommendations
        if "recommendations" in insights.get("ai_insights", {}):
            ai_recs = insights["ai_insights"]["recommendations"]
            recommendations.extend(ai_recs[:2])
        
        # General recommendations
        recommendations.append("Schedule regular data updates to maintain report accuracy")
        
        return recommendations[:5]
    
    def _calculate_confidence_score(self, processed_data: Dict[str, Any], insights: Dict[str, Any]) -> float:
        """Calculate confidence score for the analysis"""
        factors = []
        
        # Data completeness factor
        success_rate = self._calculate_success_rate(processed_data) / 100
        factors.append(success_rate)
        
        # Source diversity factor
        source_count = processed_data.get("metadata", {}).get("total_sources", 0)
        source_factor = min(source_count / 5, 1.0)  # Normalize to 0-1
        factors.append(source_factor)
        
        # Content quality factor
        content_quality = insights.get("automated_insights", {}).get("content_analysis", {}).get("content_quality_score", 50) / 100
        factors.append(content_quality)
        
        return sum(factors) / len(factors) * 100 if factors else 70.0
    
    async def _create_report_structure(self, processed_data: Dict[str, Any], insights: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Create structured report layout"""
        
        # Get report template
        template = self.report_templates.get(report_type, self.report_templates["summary"])
        
        # Build report structure
        structure = {
            "title": template["title"],
            "sections": []
        }
        
        # Executive Summary
        if "executive_summary" in template["sections"]:
            exec_summary = {
                "title": "Executive Summary",
                "content": self._create_executive_summary(insights),
                "type": "summary"
            }
            structure["sections"].append(exec_summary)
        
        # Data Overview
        if "data_overview" in template["sections"]:
            data_overview = {
                "title": "Data Overview",
                "content": self._create_data_overview(processed_data),
                "type": "overview"
            }
            structure["sections"].append(data_overview)
        
        # Key Insights
        if "key_insights" in template["sections"]:
            key_insights_section = {
                "title": "Key Insights",
                "content": insights.get("key_insights", []),
                "type": "insights"
            }
            structure["sections"].append(key_insights_section)
        
        # Detailed Analysis
        if "detailed_analysis" in template["sections"]:
            detailed_analysis = {
                "title": "Detailed Analysis",
                "content": self._create_detailed_analysis(processed_data, insights),
                "type": "analysis"
            }
            structure["sections"].append(detailed_analysis)
        
        # Recommendations
        if "recommendations" in template["sections"]:
            recommendations_section = {
                "title": "Recommendations",
                "content": insights.get("recommendations", []),
                "type": "recommendations"
            }
            structure["sections"].append(recommendations_section)
        
        # Appendix
        if "appendix" in template["sections"]:
            appendix = {
                "title": "Appendix",
                "content": self._create_appendix(processed_data, insights),
                "type": "appendix"
            }
            structure["sections"].append(appendix)
        
        return structure
    
    def _create_executive_summary(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive summary section"""
        return {
            "overview": "Comprehensive analysis of collected data sources reveals key insights and trends.",
            "key_findings": insights.get("key_insights", [])[:3],
            "confidence_score": insights.get("confidence_score", 70),
            "recommendation_priority": "high" if insights.get("confidence_score", 70) > 80 else "medium"
        }
    
    def _create_data_overview(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create data overview section"""
        metadata = processed_data.get("metadata", {})
        
        return {
            "total_sources": metadata.get("total_sources", 0),
            "successful_extractions": metadata.get("successful_extractions", 0),
            "failed_extractions": metadata.get("failed_extractions", 0),
            "source_breakdown": {
                "web_sources": len(processed_data.get("web_content", [])),
                "social_sources": len(processed_data.get("social_data", [])),
                "api_sources": len(processed_data.get("api_data", [])),
                "file_sources": len(processed_data.get("file_data", []))
            },
            "data_quality": "high" if metadata.get("successful_extractions", 0) > metadata.get("failed_extractions", 0) else "medium"
        }
    
    def _create_detailed_analysis(self, processed_data: Dict[str, Any], insights: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed analysis section"""
        return {
            "content_analysis": insights.get("automated_insights", {}).get("content_analysis", {}),
            "temporal_analysis": insights.get("automated_insights", {}).get("temporal_analysis", {}),
            "source_analysis": self._analyze_sources(processed_data),
            "pattern_detection": self._detect_patterns(processed_data)
        }
    
    def _analyze_sources(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze source characteristics"""
        analysis = {
            "most_productive_source": "web",
            "content_distribution": {},
            "reliability_scores": {}
        }
        
        # Calculate content distribution
        total_content = 0
        for source_type in ["web_content", "social_data", "api_data", "file_data"]:
            source_content = len(processed_data.get(source_type, []))
            analysis["content_distribution"][source_type] = source_content
            total_content += source_content
        
        # Normalize to percentages
        if total_content > 0:
            for source_type in analysis["content_distribution"]:
                analysis["content_distribution"][source_type] = (
                    analysis["content_distribution"][source_type] / total_content * 100
                )
        
        return analysis
    
    def _detect_patterns(self, processed_data: Dict[str, Any]) -> List[str]:
        """Detect patterns in the data"""
        patterns = []
        
        # Check for time-based patterns
        timestamps = []
        for web_item in processed_data.get("web_content", []):
            timestamp_str = web_item.get("processed_at", "")
            if timestamp_str:
                timestamps.append(timestamp_str)
        
        if len(timestamps) > 1:
            patterns.append(f"Data collection spans {len(timestamps)} time periods")
        
        # Check for content patterns
        total_sources = processed_data.get("metadata", {}).get("total_sources", 0)
        if total_sources > 5:
            patterns.append("High source diversity indicates comprehensive data collection")
        
        return patterns
    
    def _create_appendix(self, processed_data: Dict[str, Any], insights: Dict[str, Any]) -> Dict[str, Any]:
        """Create appendix section"""
        return {
            "methodology": "Data collected using AI-powered extraction and analysis",
            "data_sources": [
                f"{source_type}: {len(data)} items" 
                for source_type, data in processed_data.items() 
                if isinstance(data, list)
            ],
            "confidence_metrics": {
                "overall_confidence": insights.get("confidence_score", 70),
                "data_completeness": self._calculate_success_rate(processed_data),
                "analysis_depth": "comprehensive"
            },
            "limitations": [
                "Analysis based on available data sources",
                "AI insights subject to model capabilities",
                "Temporal analysis limited to collection timeframe"
            ]
        }
    
    async def _format_report(self, report_structure: Dict[str, Any], output_format: str) -> str:
        """Format report according to output format"""
        if output_format == "html":
            return self._format_as_html(report_structure)
        elif output_format == "markdown":
            return self._format_as_markdown(report_structure)
        elif output_format == "json":
            return json.dumps(report_structure, indent=2, default=str)
        elif output_format == "pdf":
            return await self._format_as_pdf(report_structure)
        else:
            return self._format_as_html(report_structure)  # Default to HTML
    
    def _format_as_html(self, structure: Dict[str, Any]) -> str:
        """Format report as HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{structure['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }}
                h2 {{ color: #374151; margin-top: 30px; }}
                .section {{ margin-bottom: 30px; }}
                .insights {{ background-color: #f3f4f6; padding: 20px; border-radius: 8px; }}
                .recommendations {{ background-color: #ecfdf5; padding: 20px; border-radius: 8px; }}
                .data-overview {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
                .metric {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                ul {{ padding-left: 20px; }}
                li {{ margin-bottom: 5px; }}
            </style>
        </head>
        <body>
            <h1>{structure['title']}</h1>
        """
        
        for section in structure['sections']:
            html += f'<div class="section">'
            html += f'<h2>{section["title"]}</h2>'
            
            if section['type'] == 'summary':
                content = section['content']
                html += f"<p><strong>Overview:</strong> {content.get('overview', '')}</p>"
                html += f"<p><strong>Confidence Score:</strong> {content.get('confidence_score', 0):.1f}%</p>"
                if content.get('key_findings'):
                    html += "<h3>Key Findings:</h3><ul>"
                    for finding in content['key_findings']:
                        html += f"<li>{finding}</li>"
                    html += "</ul>"
            
            elif section['type'] == 'overview':
                content = section['content']
                html += '<div class="data-overview">'
                html += f'<div class="metric"><h4>Total Sources</h4><p>{content.get("total_sources", 0)}</p></div>'
                html += f'<div class="metric"><h4>Success Rate</h4><p>{(content.get("successful_extractions", 0) / max(content.get("total_sources", 1), 1) * 100):.1f}%</p></div>'
                html += f'<div class="metric"><h4>Data Quality</h4><p>{content.get("data_quality", "unknown").title()}</p></div>'
                html += '</div>'
            
            elif section['type'] == 'insights':
                html += '<div class="insights">'
                html += "<ul>"
                for insight in section['content']:
                    html += f"<li>{insight}</li>"
                html += "</ul>"
                html += '</div>'
            
            elif section['type'] == 'recommendations':
                html += '<div class="recommendations">'
                html += "<ul>"
                for recommendation in section['content']:
                    html += f"<li>{recommendation}</li>"
                html += "</ul>"
                html += '</div>'
            
            elif section['type'] == 'analysis':
                content = section['content']
                html += f"<pre>{json.dumps(content, indent=2)}</pre>"
            
            elif section['type'] == 'appendix':
                content = section['content']
                html += f"<p><strong>Methodology:</strong> {content.get('methodology', '')}</p>"
                if content.get('limitations'):
                    html += "<h4>Limitations:</h4><ul>"
                    for limitation in content['limitations']:
                        html += f"<li>{limitation}</li>"
                    html += "</ul>"
            
            html += '</div>'
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _format_as_markdown(self, structure: Dict[str, Any]) -> str:
        """Format report as Markdown"""
        markdown = f"# {structure['title']}\n\n"
        
        for section in structure['sections']:
            markdown += f"## {section['title']}\n\n"
            
            if section['type'] == 'summary':
                content = section['content']
                markdown += f"**Overview:** {content.get('overview', '')}\n\n"
                markdown += f"**Confidence Score:** {content.get('confidence_score', 0):.1f}%\n\n"
                if content.get('key_findings'):
                    markdown += "### Key Findings:\n\n"
                    for finding in content['key_findings']:
                        markdown += f"- {finding}\n"
                    markdown += "\n"
            
            elif section['type'] == 'insights':
                for insight in section['content']:
                    markdown += f"- {insight}\n"
                markdown += "\n"
            
            elif section['type'] == 'recommendations':
                for recommendation in section['content']:
                    markdown += f"- {recommendation}\n"
                markdown += "\n"
            
            else:
                content = section.get('content', {})
                if isinstance(content, dict):
                    markdown += f"```json\n{json.dumps(content, indent=2)}\n```\n\n"
                elif isinstance(content, list):
                    for item in content:
                        markdown += f"- {item}\n"
                    markdown += "\n"
                else:
                    markdown += f"{content}\n\n"
        
        return markdown
    
    async def _format_as_pdf(self, structure: Dict[str, Any]) -> str:
        """Format report as PDF (returns base64 encoded)"""
        # For now, return HTML that could be converted to PDF
        html_content = self._format_as_html(structure)
        
        # In a real implementation, this would use a PDF generation library
        # For now, we'll return a base64-encoded placeholder
        pdf_placeholder = f"PDF Report: {structure['title']} - Generated at {datetime.utcnow().isoformat()}"
        encoded_pdf = base64.b64encode(pdf_placeholder.encode()).decode()
        
        return encoded_pdf
    
    def _load_report_templates(self) -> Dict[str, Dict]:
        """Load report templates"""
        return {
            "summary": {
                "title": "Executive Summary Report",
                "sections": ["executive_summary", "key_insights", "recommendations"]
            },
            "comprehensive": {
                "title": "Comprehensive Analysis Report", 
                "sections": ["executive_summary", "data_overview", "key_insights", "detailed_analysis", "recommendations", "appendix"]
            },
            "technical": {
                "title": "Technical Analysis Report",
                "sections": ["data_overview", "detailed_analysis", "appendix"]
            },
            "business": {
                "title": "Business Intelligence Report",
                "sections": ["executive_summary", "key_insights", "recommendations"]
            }
        }
    
    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get generated report by ID"""
        return self.generated_reports.get(report_id)
    
    async def list_reports(self) -> List[Dict[str, Any]]:
        """List all generated reports"""
        return [
            {
                "report_id": report_id,
                "title": report_data.get("structure", {}).get("title", ""),
                "report_type": report_data.get("report_type", ""),
                "generated_at": report_data.get("generated_at", "").isoformat() if hasattr(report_data.get("generated_at", ""), 'isoformat') else str(report_data.get("generated_at", "")),
                "output_format": report_data.get("output_format", "")
            }
            for report_id, report_data in self.generated_reports.items()
        ]

# Global instance
advanced_report_generator = AdvancedReportGenerator()