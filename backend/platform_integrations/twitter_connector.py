"""
Twitter/X Platform Integration for AETHER
Advanced automation capabilities for Twitter platform
"""

import tweepy
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import logging

class TwitterConnector:
    def __init__(self, api_credentials: Dict[str, str]):
        self.api_key = api_credentials.get('api_key')
        self.api_secret = api_credentials.get('api_secret')
        self.access_token = api_credentials.get('access_token')
        self.access_token_secret = api_credentials.get('access_token_secret')
        self.bearer_token = api_credentials.get('bearer_token')
        
        self.client_v1 = None
        self.client_v2 = None
        self.initialize_clients()
        
    def initialize_clients(self):
        """Initialize Twitter API clients (v1.1 and v2)"""
        try:
            # Twitter API v1.1 (for media uploads and some legacy features)
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            )
            self.client_v1 = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Twitter API v2 (for modern features)
            self.client_v2 = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
            print("✅ Twitter clients initialized successfully")
        except Exception as e:
            print(f"❌ Twitter client initialization failed: {e}")
            raise

    # TWEET OPERATIONS
    async def post_tweet(self, text: str, media_paths: List[str] = None, reply_to: str = None) -> Dict[str, Any]:
        """Post a tweet with optional media and reply functionality"""
        try:
            media_ids = []
            
            # Upload media if provided
            if media_paths:
                for media_path in media_paths:
                    media = self.client_v1.media_upload(media_path)
                    media_ids.append(media.media_id)
            
            # Post tweet
            response = self.client_v2.create_tweet(
                text=text,
                media_ids=media_ids if media_ids else None,
                in_reply_to_tweet_id=reply_to
            )
            
            return {
                "success": True,
                "tweet_id": response.data['id'],
                "text": text,
                "media_count": len(media_ids),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """Delete a specific tweet"""
        try:
            self.client_v2.delete_tweet(tweet_id)
            return {"success": True, "deleted_tweet_id": tweet_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def like_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """Like a specific tweet"""
        try:
            self.client_v2.like(tweet_id)
            return {"success": True, "action": "liked", "tweet_id": tweet_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def retweet(self, tweet_id: str) -> Dict[str, Any]:
        """Retweet a specific tweet"""
        try:
            self.client_v2.retweet(tweet_id)
            return {"success": True, "action": "retweeted", "tweet_id": tweet_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # SEARCH AND DISCOVERY
    async def search_tweets(self, query: str, max_results: int = 10, tweet_fields: List[str] = None) -> Dict[str, Any]:
        """Search for tweets based on query"""
        try:
            default_fields = ['id', 'text', 'created_at', 'author_id', 'public_metrics']
            fields = tweet_fields or default_fields
            
            tweets = self.client_v2.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=fields
            )
            
            results = []
            if tweets.data:
                for tweet in tweets.data:
                    results.append({
                        "id": tweet.id,
                        "text": tweet.text,
                        "created_at": tweet.created_at.isoformat(),
                        "author_id": tweet.author_id,
                        "metrics": tweet.public_metrics
                    })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_trending_topics(self, location_id: int = 1) -> Dict[str, Any]:
        """Get trending topics for a location (1 = worldwide)"""
        try:
            trends = self.client_v1.get_place_trends(location_id)
            
            trending_topics = []
            for trend in trends[0]['trends']:
                trending_topics.append({
                    "name": trend['name'],
                    "url": trend['url'],
                    "tweet_volume": trend.get('tweet_volume'),
                    "promoted": trend.get('promoted_content')
                })
            
            return {
                "success": True,
                "location_id": location_id,
                "trends": trending_topics,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # USER OPERATIONS
    async def follow_user(self, username: str) -> Dict[str, Any]:
        """Follow a user by username"""
        try:
            user = self.client_v2.get_user(username=username)
            if user.data:
                self.client_v2.follow_user(user.data.id)
                return {
                    "success": True,
                    "action": "followed",
                    "username": username,
                    "user_id": user.data.id
                }
            else:
                return {"success": False, "error": "User not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def unfollow_user(self, username: str) -> Dict[str, Any]:
        """Unfollow a user by username"""
        try:
            user = self.client_v2.get_user(username=username)
            if user.data:
                self.client_v2.unfollow_user(user.data.id)
                return {
                    "success": True,
                    "action": "unfollowed",
                    "username": username,
                    "user_id": user.data.id
                }
            else:
                return {"success": False, "error": "User not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get detailed information about a user"""
        try:
            user = self.client_v2.get_user(
                username=username,
                user_fields=['id', 'name', 'username', 'description', 'location', 
                           'public_metrics', 'verified', 'created_at']
            )
            
            if user.data:
                return {
                    "success": True,
                    "user": {
                        "id": user.data.id,
                        "name": user.data.name,
                        "username": user.data.username,
                        "description": user.data.description,
                        "location": user.data.location,
                        "followers": user.data.public_metrics['followers_count'],
                        "following": user.data.public_metrics['following_count'],
                        "tweets": user.data.public_metrics['tweet_count'],
                        "verified": user.data.verified,
                        "created_at": user.data.created_at.isoformat()
                    }
                }
            else:
                return {"success": False, "error": "User not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # AUTOMATION WORKFLOWS
    async def engagement_automation(self, hashtags: List[str], actions_per_hashtag: int = 5) -> Dict[str, Any]:
        """Automated engagement based on hashtags"""
        try:
            total_actions = 0
            results = []
            
            for hashtag in hashtags:
                # Search for recent tweets with hashtag
                search_query = f"#{hashtag} -is:retweet lang:en"
                tweets = await self.search_tweets(search_query, max_results=actions_per_hashtag)
                
                if tweets["success"]:
                    for tweet in tweets["results"]:
                        # Like the tweet
                        like_result = await self.like_tweet(tweet["id"])
                        if like_result["success"]:
                            total_actions += 1
                        
                        results.append({
                            "hashtag": hashtag,
                            "tweet_id": tweet["id"],
                            "action": "like",
                            "success": like_result["success"]
                        })
                        
                        # Add delay to avoid rate limiting
                        await asyncio.sleep(2)
            
            return {
                "success": True,
                "total_actions": total_actions,
                "hashtags_processed": hashtags,
                "detailed_results": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def content_scheduler(self, scheduled_tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Schedule tweets for optimal posting times"""
        try:
            scheduled_count = 0
            
            for tweet_data in scheduled_tweets:
                # For demonstration, we'll post immediately
                # In a real implementation, you'd use a task scheduler
                result = await self.post_tweet(
                    text=tweet_data["text"],
                    media_paths=tweet_data.get("media", [])
                )
                
                if result["success"]:
                    scheduled_count += 1
                
                # Add optimal posting delay
                await asyncio.sleep(3600)  # 1 hour between posts
            
            return {
                "success": True,
                "scheduled_count": scheduled_count,
                "total_tweets": len(scheduled_tweets)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ANALYTICS AND INSIGHTS
    async def get_account_analytics(self) -> Dict[str, Any]:
        """Get analytics for the authenticated account"""
        try:
            # Get user's own information
            me = self.client_v2.get_me(
                user_fields=['public_metrics', 'created_at']
            )
            
            # Get recent tweets for engagement analysis
            my_tweets = self.client_v2.get_users_tweets(
                id=me.data.id,
                max_results=10,
                tweet_fields=['public_metrics', 'created_at']
            )
            
            tweet_analytics = []
            total_engagement = 0
            
            if my_tweets.data:
                for tweet in my_tweets.data:
                    engagement = (
                        tweet.public_metrics['like_count'] + 
                        tweet.public_metrics['retweet_count'] + 
                        tweet.public_metrics['reply_count']
                    )
                    total_engagement += engagement
                    
                    tweet_analytics.append({
                        "tweet_id": tweet.id,
                        "text": tweet.text[:100] + "...",
                        "likes": tweet.public_metrics['like_count'],
                        "retweets": tweet.public_metrics['retweet_count'],
                        "replies": tweet.public_metrics['reply_count'],
                        "engagement": engagement,
                        "created_at": tweet.created_at.isoformat()
                    })
            
            return {
                "success": True,
                "account_metrics": {
                    "followers": me.data.public_metrics['followers_count'],
                    "following": me.data.public_metrics['following_count'],
                    "total_tweets": me.data.public_metrics['tweet_count'],
                    "listed_count": me.data.public_metrics['listed_count']
                },
                "recent_tweets_analytics": tweet_analytics,
                "average_engagement": total_engagement / len(tweet_analytics) if tweet_analytics else 0
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ADVANCED FEATURES
    async def sentiment_based_engagement(self, keywords: List[str], sentiment: str = "positive") -> Dict[str, Any]:
        """Engage with tweets based on sentiment analysis"""
        try:
            engaged_tweets = []
            
            for keyword in keywords:
                # Search for tweets
                query = f"{keyword} lang:en -is:retweet"
                tweets = await self.search_tweets(query, max_results=5)
                
                if tweets["success"]:
                    for tweet in tweets["results"]:
                        # Simple sentiment analysis (in production, use proper NLP)
                        tweet_text = tweet["text"].lower()
                        positive_words = ["good", "great", "awesome", "amazing", "love", "excellent"]
                        negative_words = ["bad", "terrible", "awful", "hate", "horrible"]
                        
                        pos_score = sum(1 for word in positive_words if word in tweet_text)
                        neg_score = sum(1 for word in negative_words if word in tweet_text)
                        
                        if sentiment == "positive" and pos_score > neg_score:
                            result = await self.like_tweet(tweet["id"])
                            engaged_tweets.append({
                                "tweet_id": tweet["id"],
                                "keyword": keyword,
                                "action": "liked",
                                "sentiment_score": pos_score - neg_score
                            })
                        
                        await asyncio.sleep(1)
            
            return {
                "success": True,
                "engaged_tweets": engaged_tweets,
                "sentiment_filter": sentiment,
                "keywords": keywords
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def competitor_analysis(self, competitor_usernames: List[str]) -> Dict[str, Any]:
        """Analyze competitor accounts for insights"""
        try:
            competitor_data = []
            
            for username in competitor_usernames:
                user_info = await self.get_user_info(username)
                
                if user_info["success"]:
                    # Get recent tweets
                    user = self.client_v2.get_user(username=username)
                    tweets = self.client_v2.get_users_tweets(
                        id=user.data.id,
                        max_results=10,
                        tweet_fields=['public_metrics', 'created_at']
                    )
                    
                    avg_engagement = 0
                    if tweets.data:
                        total_engagement = sum(
                            tweet.public_metrics['like_count'] + 
                            tweet.public_metrics['retweet_count'] + 
                            tweet.public_metrics['reply_count']
                            for tweet in tweets.data
                        )
                        avg_engagement = total_engagement / len(tweets.data)
                    
                    competitor_data.append({
                        "username": username,
                        "followers": user_info["user"]["followers"],
                        "following": user_info["user"]["following"],
                        "tweets": user_info["user"]["tweets"],
                        "avg_engagement": avg_engagement,
                        "engagement_rate": avg_engagement / user_info["user"]["followers"] * 100
                    })
                
                await asyncio.sleep(1)
            
            return {
                "success": True,
                "competitor_analysis": competitor_data,
                "analysis_date": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # HEALTH CHECK
    async def test_connection(self) -> Dict[str, Any]:
        """Test the Twitter API connection"""
        try:
            me = self.client_v2.get_me()
            return {
                "success": True,
                "authenticated_user": me.data.username,
                "connection_status": "active"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}