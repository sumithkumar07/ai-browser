"""
Analysis Agent - Specialized in data analysis and pattern recognition
Provides advanced analytical capabilities for complex data processing
"""
import asyncio
import json
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

class AnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type="analysis",
            capabilities=[
                "data_analysis",
                "pattern_recognition",
                "statistical_analysis",
                "trend_analysis",
                "performance_analysis",
                "sentiment_analysis",
                "competitive_analysis",
                "predictive_modeling"
            ]
        )
        self.analysis_models = {}
        self.cached_analyses = {}
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis task with comprehensive data processing"""
        await self.update_status("analyzing", task)
        
        # 1. Determine analysis type and prepare data
        analysis_spec = await self._determine_analysis_type(task)
        prepared_data = await self._prepare_analysis_data(task, analysis_spec)
        
        # 2. Execute analysis based on type
        analysis_result = await self._execute_analysis(prepared_data, analysis_spec)
        
        # 3. Generate insights and recommendations
        insights = await self._generate_insights(analysis_result, analysis_spec)
        
        # 4. Create visualization suggestions
        visualizations = await self._suggest_visualizations(analysis_result)
        
        final_result = {
            "success": True,
            "analysis_type": analysis_spec["type"],
            "data_points_analyzed": len(prepared_data.get("data_points", [])),
            "confidence_score": analysis_result.get("confidence", 0.0),
            "analysis_results": analysis_result,
            "insights": insights,
            "visualizations": visualizations,
            "processing_time": 0,
            "agent_id": self.agent_id
        }
        
        await self.update_status("completed", task)
        await self.learn_from_execution(task, final_result)
        
        return final_result
    
    async def _determine_analysis_type(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the type of analysis needed based on task description"""
        description = task.get("description", "").lower()
        
        analysis_spec = {
            "type": "general",
            "methods": [],
            "complexity": "medium",
            "output_format": "summary"
        }
        
        # Pattern matching for analysis types
        if any(word in description for word in ["trend", "time", "temporal", "historical"]):
            analysis_spec["type"] = "trend_analysis"
            analysis_spec["methods"] = ["time_series", "regression", "moving_averages"]
        
        elif any(word in description for word in ["sentiment", "opinion", "feeling", "emotion"]):
            analysis_spec["type"] = "sentiment_analysis"
            analysis_spec["methods"] = ["text_analysis", "sentiment_scoring", "emotion_detection"]
        
        elif any(word in description for word in ["performance", "metrics", "benchmark", "kpi"]):
            analysis_spec["type"] = "performance_analysis"
            analysis_spec["methods"] = ["statistical_analysis", "comparative_analysis", "efficiency_metrics"]
        
        elif any(word in description for word in ["pattern", "cluster", "segment", "group"]):
            analysis_spec["type"] = "pattern_analysis"
            analysis_spec["methods"] = ["clustering", "pattern_recognition", "segmentation"]
        
        elif any(word in description for word in ["predict", "forecast", "future", "projection"]):
            analysis_spec["type"] = "predictive_analysis"
            analysis_spec["methods"] = ["predictive_modeling", "forecasting", "regression_analysis"]
        
        elif any(word in description for word in ["compare", "competitive", "benchmark", "versus"]):
            analysis_spec["type"] = "comparative_analysis"
            analysis_spec["methods"] = ["comparative_metrics", "benchmarking", "gap_analysis"]
        
        # Set complexity based on methods
        if len(analysis_spec["methods"]) > 2:
            analysis_spec["complexity"] = "high"
        elif len(analysis_spec["methods"]) > 1:
            analysis_spec["complexity"] = "medium"
        else:
            analysis_spec["complexity"] = "low"
        
        return analysis_spec
    
    async def _prepare_analysis_data(self, task: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and validate data for analysis"""
        raw_data = task.get("data", {})
        
        prepared_data = {
            "data_points": [],
            "metadata": {},
            "quality_score": 0.0,
            "data_types": {},
            "missing_values": 0,
            "total_records": 0
        }
        
        # Extract data points from various sources
        if isinstance(raw_data, dict):
            if "search_results" in raw_data:
                prepared_data["data_points"] = await self._extract_from_search_results(raw_data["search_results"])
            elif "news_articles" in raw_data:
                prepared_data["data_points"] = await self._extract_from_news(raw_data["news_articles"])
            elif "repositories" in raw_data:
                prepared_data["data_points"] = await self._extract_from_repositories(raw_data["repositories"])
            else:
                # Generic data extraction
                prepared_data["data_points"] = await self._extract_generic_data(raw_data)
        elif isinstance(raw_data, list):
            prepared_data["data_points"] = raw_data
        
        # Calculate data quality metrics
        prepared_data["total_records"] = len(prepared_data["data_points"])
        prepared_data["quality_score"] = await self._calculate_data_quality(prepared_data["data_points"])
        prepared_data["data_types"] = await self._analyze_data_types(prepared_data["data_points"])
        
        return prepared_data
    
    async def _extract_from_search_results(self, search_results: List[Dict]) -> List[Dict]:
        """Extract analyzable data from search results"""
        data_points = []
        
        for result in search_results:
            data_point = {
                "title": result.get("title", ""),
                "relevance_score": result.get("relevance_score", 0.0),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
                "word_count": len(result.get("snippet", "").split()),
                "timestamp": datetime.utcnow().isoformat()
            }
            data_points.append(data_point)
        
        return data_points
    
    async def _extract_from_news(self, news_articles: List[Dict]) -> List[Dict]:
        """Extract analyzable data from news articles"""
        data_points = []
        
        for article in news_articles:
            data_point = {
                "headline": article.get("headline", ""),
                "source": article.get("source", ""),
                "published_date": article.get("published_date", ""),
                "credibility_score": article.get("credibility_score", 0.0),
                "summary": article.get("summary", ""),
                "sentiment_indicator": await self._basic_sentiment_analysis(article.get("headline", "")),
                "timestamp": datetime.utcnow().isoformat()
            }
            data_points.append(data_point)
        
        return data_points
    
    async def _extract_from_repositories(self, repositories: List[Dict]) -> List[Dict]:
        """Extract analyzable data from code repositories"""
        data_points = []
        
        for repo in repositories:
            data_point = {
                "name": repo.get("name", ""),
                "stars": repo.get("stars", 0),
                "forks": repo.get("forks", 0),
                "language": repo.get("language", ""),
                "activity_score": repo.get("activity_score", 0.0),
                "popularity_index": (repo.get("stars", 0) + repo.get("forks", 0)) / 2,
                "timestamp": datetime.utcnow().isoformat()
            }
            data_points.append(data_point)
        
        return data_points
    
    async def _extract_generic_data(self, raw_data: Dict) -> List[Dict]:
        """Extract data from generic dictionary structure"""
        data_points = []
        
        for key, value in raw_data.items():
            if isinstance(value, (dict, list)):
                data_point = {
                    "key": key,
                    "value": str(value),
                    "type": type(value).__name__,
                    "size": len(value) if hasattr(value, '__len__') else 1,
                    "timestamp": datetime.utcnow().isoformat()
                }
                data_points.append(data_point)
        
        return data_points
    
    async def _basic_sentiment_analysis(self, text: str) -> float:
        """Basic sentiment analysis for text"""
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "positive", "success"]
        negative_words = ["bad", "terrible", "awful", "horrible", "negative", "failure", "problem", "issue"]
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count + negative_count == 0:
            return 0.0  # Neutral
        
        sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        return sentiment
    
    async def _calculate_data_quality(self, data_points: List[Dict]) -> float:
        """Calculate overall data quality score"""
        if not data_points:
            return 0.0
        
        quality_factors = []
        
        # Completeness - percentage of non-empty values
        total_fields = 0
        filled_fields = 0
        
        for point in data_points:
            for key, value in point.items():
                total_fields += 1
                if value and value != "" and value != 0:
                    filled_fields += 1
        
        completeness = filled_fields / total_fields if total_fields > 0 else 0
        quality_factors.append(completeness)
        
        # Consistency - check for consistent data types
        type_consistency = await self._check_type_consistency(data_points)
        quality_factors.append(type_consistency)
        
        # Validity - check for reasonable values
        validity_score = await self._check_data_validity(data_points)
        quality_factors.append(validity_score)
        
        return statistics.mean(quality_factors)
    
    async def _check_type_consistency(self, data_points: List[Dict]) -> float:
        """Check consistency of data types across records"""
        if len(data_points) < 2:
            return 1.0
        
        field_types = {}
        consistent_fields = 0
        total_fields = 0
        
        for point in data_points:
            for key, value in point.items():
                if key not in field_types:
                    field_types[key] = type(value)
                    total_fields += 1
                elif type(value) == field_types[key]:
                    consistent_fields += 1
        
        return consistent_fields / total_fields if total_fields > 0 else 1.0
    
    async def _check_data_validity(self, data_points: List[Dict]) -> float:
        """Check validity of data values"""
        valid_points = 0
        total_points = len(data_points)
        
        for point in data_points:
            is_valid = True
            
            # Check for reasonable numeric values
            for key, value in point.items():
                if isinstance(value, (int, float)):
                    if value < 0 and key in ["stars", "forks", "score"]:
                        is_valid = False
                        break
                    if value > 1000000:  # Arbitrary large number check
                        is_valid = False
                        break
            
            if is_valid:
                valid_points += 1
        
        return valid_points / total_points if total_points > 0 else 1.0
    
    async def _analyze_data_types(self, data_points: List[Dict]) -> Dict[str, str]:
        """Analyze data types in the dataset"""
        type_analysis = {}
        
        if not data_points:
            return type_analysis
        
        # Analyze first data point to get field structure
        sample_point = data_points[0]
        
        for key, value in sample_point.items():
            type_analysis[key] = type(value).__name__
        
        return type_analysis
    
    async def _execute_analysis(self, prepared_data: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the appropriate analysis based on specification"""
        analysis_type = spec["type"]
        
        if analysis_type == "trend_analysis":
            return await self._perform_trend_analysis(prepared_data)
        elif analysis_type == "sentiment_analysis":
            return await self._perform_sentiment_analysis(prepared_data)
        elif analysis_type == "performance_analysis":
            return await self._perform_performance_analysis(prepared_data)
        elif analysis_type == "pattern_analysis":
            return await self._perform_pattern_analysis(prepared_data)
        elif analysis_type == "predictive_analysis":
            return await self._perform_predictive_analysis(prepared_data)
        elif analysis_type == "comparative_analysis":
            return await self._perform_comparative_analysis(prepared_data)
        else:
            return await self._perform_general_analysis(prepared_data)
    
    async def _perform_trend_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform trend analysis on temporal data"""
        data_points = data.get("data_points", [])
        
        # Extract numeric values for trend analysis
        numeric_values = []
        for point in data_points:
            for key, value in point.items():
                if isinstance(value, (int, float)) and key != "timestamp":
                    numeric_values.append(value)
        
        if len(numeric_values) < 2:
            return {"confidence": 0.0, "trend": "insufficient_data"}
        
        # Calculate trend direction
        if len(numeric_values) >= 3:
            recent_avg = statistics.mean(numeric_values[-3:])
            earlier_avg = statistics.mean(numeric_values[:3]) if len(numeric_values) >= 6 else numeric_values[0]
            
            trend_direction = "increasing" if recent_avg > earlier_avg else "decreasing"
            trend_strength = abs(recent_avg - earlier_avg) / max(abs(earlier_avg), 1)
        else:
            trend_direction = "increasing" if numeric_values[-1] > numeric_values[0] else "decreasing"
            trend_strength = abs(numeric_values[-1] - numeric_values[0]) / max(abs(numeric_values[0]), 1)
        
        return {
            "confidence": min(trend_strength, 1.0),
            "trend": trend_direction,
            "trend_strength": trend_strength,
            "data_points_analyzed": len(numeric_values),
            "average_value": statistics.mean(numeric_values),
            "value_range": {"min": min(numeric_values), "max": max(numeric_values)}
        }
    
    async def _perform_sentiment_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform sentiment analysis on text data"""
        data_points = data.get("data_points", [])
        
        sentiment_scores = []
        text_fields = ["title", "headline", "snippet", "summary", "description"]
        
        for point in data_points:
            for field in text_fields:
                if field in point and point[field]:
                    sentiment = await self._basic_sentiment_analysis(point[field])
                    sentiment_scores.append(sentiment)
        
        if not sentiment_scores:
            return {"confidence": 0.0, "overall_sentiment": "neutral"}
        
        average_sentiment = statistics.mean(sentiment_scores)
        
        # Classify sentiment
        if average_sentiment > 0.2:
            sentiment_label = "positive"
        elif average_sentiment < -0.2:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        return {
            "confidence": min(abs(average_sentiment) * 2, 1.0),
            "overall_sentiment": sentiment_label,
            "average_score": average_sentiment,
            "sentiment_distribution": {
                "positive": sum(1 for s in sentiment_scores if s > 0.1),
                "negative": sum(1 for s in sentiment_scores if s < -0.1),
                "neutral": sum(1 for s in sentiment_scores if -0.1 <= s <= 0.1)
            },
            "texts_analyzed": len(sentiment_scores)
        }
    
    async def _perform_performance_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform performance analysis on metrics data"""
        data_points = data.get("data_points", [])
        
        performance_metrics = {}
        numeric_fields = []
        
        # Identify numeric fields for performance analysis
        if data_points:
            for key, value in data_points[0].items():
                if isinstance(value, (int, float)):
                    numeric_fields.append(key)
        
        for field in numeric_fields:
            values = [point.get(field, 0) for point in data_points if isinstance(point.get(field), (int, float))]
            
            if values:
                performance_metrics[field] = {
                    "average": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0
                }
        
        # Calculate overall performance score
        if performance_metrics:
            # Use coefficient of variation as performance indicator (lower is better)
            cv_scores = []
            for field, metrics in performance_metrics.items():
                if metrics["average"] > 0:
                    cv = metrics["std_dev"] / metrics["average"]
                    cv_scores.append(cv)
            
            performance_score = 1 - (statistics.mean(cv_scores) if cv_scores else 0.5)
        else:
            performance_score = 0.0
        
        return {
            "confidence": 0.8 if performance_metrics else 0.0,
            "performance_score": max(0, min(1, performance_score)),
            "metrics": performance_metrics,
            "data_points_analyzed": len(data_points),
            "analysis_summary": "Performance analysis completed with statistical metrics"
        }
    
    async def _perform_pattern_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform pattern recognition analysis"""
        data_points = data.get("data_points", [])
        
        patterns = {
            "recurring_elements": {},
            "data_clusters": [],
            "anomalies": [],
            "common_attributes": {}
        }
        
        # Find recurring elements
        for point in data_points:
            for key, value in point.items():
                if isinstance(value, str):
                    if key not in patterns["recurring_elements"]:
                        patterns["recurring_elements"][key] = {}
                    
                    if value in patterns["recurring_elements"][key]:
                        patterns["recurring_elements"][key][value] += 1
                    else:
                        patterns["recurring_elements"][key][value] = 1
        
        # Identify common attributes (appear in >50% of records)
        for field, value_counts in patterns["recurring_elements"].items():
            total_records = len(data_points)
            for value, count in value_counts.items():
                if count / total_records > 0.5:
                    patterns["common_attributes"][field] = value
        
        # Simple anomaly detection (values that appear only once)
        for field, value_counts in patterns["recurring_elements"].items():
            anomalous_values = [value for value, count in value_counts.items() if count == 1]
            if anomalous_values:
                patterns["anomalies"].append({
                    "field": field,
                    "anomalous_values": anomalous_values[:5]  # Limit to 5 examples
                })
        
        return {
            "confidence": 0.75,
            "patterns_found": patterns,
            "pattern_strength": len(patterns["common_attributes"]) / max(len(patterns["recurring_elements"]), 1),
            "anomaly_count": sum(len(anomaly["anomalous_values"]) for anomaly in patterns["anomalies"]),
            "data_points_analyzed": len(data_points)
        }
    
    async def _perform_predictive_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform basic predictive analysis"""
        data_points = data.get("data_points", [])
        
        # Simple linear prediction based on trend
        numeric_fields = []
        if data_points:
            for key, value in data_points[0].items():
                if isinstance(value, (int, float)):
                    numeric_fields.append(key)
        
        predictions = {}
        
        for field in numeric_fields:
            values = [point.get(field, 0) for point in data_points if isinstance(point.get(field), (int, float))]
            
            if len(values) >= 3:
                # Simple linear trend prediction
                recent_values = values[-3:]
                trend = (recent_values[-1] - recent_values[0]) / 2  # Average change
                predicted_value = values[-1] + trend
                
                predictions[field] = {
                    "current_value": values[-1],
                    "predicted_next_value": predicted_value,
                    "trend": "increasing" if trend > 0 else "decreasing",
                    "confidence": min(abs(trend) / max(abs(values[-1]), 1), 1.0)
                }
        
        overall_confidence = statistics.mean([p["confidence"] for p in predictions.values()]) if predictions else 0.0
        
        return {
            "confidence": overall_confidence,
            "predictions": predictions,
            "prediction_horizon": "short_term",
            "model_type": "linear_trend",
            "data_points_used": len(data_points)
        }
    
    async def _perform_comparative_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comparative analysis between data segments"""
        data_points = data.get("data_points", [])
        
        if len(data_points) < 2:
            return {"confidence": 0.0, "comparison": "insufficient_data"}
        
        # Split data into segments for comparison
        mid_point = len(data_points) // 2
        segment_1 = data_points[:mid_point]
        segment_2 = data_points[mid_point:]
        
        comparison = {
            "segment_1_size": len(segment_1),
            "segment_2_size": len(segment_2),
            "differences": {},
            "similarities": {},
            "overall_difference_score": 0.0
        }
        
        # Compare numeric fields between segments
        numeric_fields = []
        if data_points:
            for key, value in data_points[0].items():
                if isinstance(value, (int, float)):
                    numeric_fields.append(key)
        
        difference_scores = []
        
        for field in numeric_fields:
            values_1 = [point.get(field, 0) for point in segment_1 if isinstance(point.get(field), (int, float))]
            values_2 = [point.get(field, 0) for point in segment_2 if isinstance(point.get(field), (int, float))]
            
            if values_1 and values_2:
                avg_1 = statistics.mean(values_1)
                avg_2 = statistics.mean(values_2)
                
                if avg_1 != 0 or avg_2 != 0:
                    difference_score = abs(avg_1 - avg_2) / max(abs(avg_1), abs(avg_2), 1)
                    difference_scores.append(difference_score)
                    
                    comparison["differences"][field] = {
                        "segment_1_avg": avg_1,
                        "segment_2_avg": avg_2,
                        "difference_percentage": difference_score * 100,
                        "higher_segment": "segment_1" if avg_1 > avg_2 else "segment_2"
                    }
        
        comparison["overall_difference_score"] = statistics.mean(difference_scores) if difference_scores else 0.0
        
        return {
            "confidence": 0.8 if difference_scores else 0.0,
            "comparison": comparison,
            "analysis_type": "segment_comparison",
            "significant_differences": comparison["overall_difference_score"] > 0.2
        }
    
    async def _perform_general_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform general statistical analysis"""
        data_points = data.get("data_points", [])
        
        analysis = {
            "data_summary": {
                "total_records": len(data_points),
                "data_quality": data.get("quality_score", 0.0),
                "data_types": data.get("data_types", {})
            },
            "basic_statistics": {},
            "data_distribution": {}
        }
        
        # Calculate basic statistics for numeric fields
        if data_points:
            for key, value in data_points[0].items():
                if isinstance(value, (int, float)):
                    values = [point.get(key, 0) for point in data_points if isinstance(point.get(key), (int, float))]
                    
                    if values:
                        analysis["basic_statistics"][key] = {
                            "count": len(values),
                            "mean": statistics.mean(values),
                            "median": statistics.median(values),
                            "min": min(values),
                            "max": max(values)
                        }
                        
                        # Simple distribution analysis
                        sorted_values = sorted(values)
                        q1_index = len(sorted_values) // 4
                        q3_index = 3 * len(sorted_values) // 4
                        
                        analysis["data_distribution"][key] = {
                            "q1": sorted_values[q1_index] if q1_index < len(sorted_values) else sorted_values[0],
                            "q3": sorted_values[q3_index] if q3_index < len(sorted_values) else sorted_values[-1],
                            "range": max(values) - min(values)
                        }
        
        return {
            "confidence": 0.7,
            "analysis": analysis,
            "analysis_type": "descriptive_statistics",
            "insights_available": len(analysis["basic_statistics"]) > 0
        }
    
    async def _generate_insights(self, analysis_result: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable insights from analysis results"""
        insights = {
            "key_findings": [],
            "recommendations": [],
            "confidence_level": analysis_result.get("confidence", 0.0),
            "actionable_items": []
        }
        
        analysis_type = spec["type"]
        confidence = analysis_result.get("confidence", 0.0)
        
        # Generate type-specific insights
        if analysis_type == "trend_analysis" and confidence > 0.5:
            trend = analysis_result.get("trend", "")
            insights["key_findings"].append(f"Data shows a {trend} trend with {confidence:.0%} confidence")
            
            if trend == "increasing":
                insights["recommendations"].append("Monitor for continued growth and plan for scaling")
            else:
                insights["recommendations"].append("Investigate factors causing decline and implement improvements")
        
        elif analysis_type == "sentiment_analysis" and confidence > 0.5:
            sentiment = analysis_result.get("overall_sentiment", "")
            insights["key_findings"].append(f"Overall sentiment is {sentiment} with {confidence:.0%} confidence")
            
            if sentiment == "negative":
                insights["actionable_items"].append("Address negative sentiment sources")
            elif sentiment == "positive":
                insights["actionable_items"].append("Leverage positive sentiment for growth")
        
        elif analysis_type == "performance_analysis":
            performance_score = analysis_result.get("performance_score", 0.0)
            insights["key_findings"].append(f"Performance score: {performance_score:.1%}")
            
            if performance_score < 0.7:
                insights["recommendations"].append("Performance improvement opportunities identified")
            else:
                insights["key_findings"].append("Performance metrics are within acceptable range")
        
        # General insights based on data quality
        if confidence < 0.5:
            insights["recommendations"].append("Consider collecting more data for higher confidence results")
        
        return insights
    
    async def _suggest_visualizations(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest appropriate visualizations for the analysis results"""
        visualizations = {
            "recommended_charts": [],
            "data_suitable_for_visualization": True,
            "visualization_priority": "medium"
        }
        
        confidence = analysis_result.get("confidence", 0.0)
        
        if confidence < 0.3:
            visualizations["data_suitable_for_visualization"] = False
            return visualizations
        
        # Check for different types of data that can be visualized
        if "trend" in analysis_result:
            visualizations["recommended_charts"].append({
                "type": "line_chart",
                "title": "Trend Analysis Over Time",
                "description": "Shows trend direction and strength"
            })
        
        if "sentiment_distribution" in analysis_result:
            visualizations["recommended_charts"].append({
                "type": "pie_chart", 
                "title": "Sentiment Distribution",
                "description": "Shows breakdown of positive, negative, and neutral sentiment"
            })
        
        if "metrics" in analysis_result:
            visualizations["recommended_charts"].append({
                "type": "bar_chart",
                "title": "Performance Metrics Comparison", 
                "description": "Compares different performance indicators"
            })
        
        if "patterns_found" in analysis_result:
            visualizations["recommended_charts"].append({
                "type": "heatmap",
                "title": "Pattern Visualization",
                "description": "Displays data patterns and clusters"
            })
        
        # Set priority based on number of viable visualizations
        if len(visualizations["recommended_charts"]) >= 3:
            visualizations["visualization_priority"] = "high"
        elif len(visualizations["recommended_charts"]) >= 1:
            visualizations["visualization_priority"] = "medium"
        else:
            visualizations["visualization_priority"] = "low"
        
        return visualizations