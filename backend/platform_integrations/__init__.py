# Platform Integrations for AETHER
# Comprehensive integration hub for 50+ platforms

from .base_connector import BasePlatformConnector
from .social_media.twitter_connector import TwitterConnector
from .social_media.linkedin_connector import LinkedInConnector
from .social_media.facebook_connector import FacebookConnector
from .social_media.instagram_connector import InstagramConnector
from .social_media.youtube_connector import YouTubeConnector
from .social_media.tiktok_connector import TikTokConnector
from .social_media.discord_connector import DiscordConnector
from .social_media.telegram_connector import TelegramConnector
from .social_media.reddit_connector import RedditConnector
from .social_media.pinterest_connector import PinterestConnector

from .productivity.gmail_connector import GmailConnector
from .productivity.outlook_connector import OutlookConnector
from .productivity.notion_connector import NotionConnector
from .productivity.slack_connector import SlackConnector
from .productivity.teams_connector import TeamsConnector
from .productivity.zoom_connector import ZoomConnector
from .productivity.calendar_connector import CalendarConnector
from .productivity.trello_connector import TrelloConnector
from .productivity.asana_connector import AsanaConnector
from .productivity.jira_connector import JiraConnector

from .development.github_connector import GitHubConnector
from .development.gitlab_connector import GitLabConnector
from .development.bitbucket_connector import BitbucketConnector
from .development.stackoverflow_connector import StackOverflowConnector
from .development.codepen_connector import CodePenConnector

from .ecommerce.amazon_connector import AmazonConnector
from .ecommerce.shopify_connector import ShopifyConnector
from .ecommerce.ebay_connector import EBayConnector
from .ecommerce.etsy_connector import EtsyConnector
from .ecommerce.stripe_connector import StripeConnector

from .cloud_storage.dropbox_connector import DropboxConnector
from .cloud_storage.google_drive_connector import GoogleDriveConnector
from .cloud_storage.onedrive_connector import OneDriveConnector
from .cloud_storage.aws_s3_connector import AWSS3Connector

from .ai_services.openai_connector import OpenAIConnector
from .ai_services.anthropic_connector import AnthropicConnector
from .ai_services.google_ai_connector import GoogleAIConnector

from .marketing.mailchimp_connector import MailchimpConnector
from .marketing.hubspot_connector import HubspotConnector
from .marketing.salesforce_connector import SalesforceConnector

# Platform registry for dynamic loading
PLATFORM_CONNECTORS = {
    # Social Media
    'twitter': TwitterConnector,
    'linkedin': LinkedInConnector, 
    'facebook': FacebookConnector,
    'instagram': InstagramConnector,
    'youtube': YouTubeConnector,
    'tiktok': TikTokConnector,
    'discord': DiscordConnector,
    'telegram': TelegramConnector,
    'reddit': RedditConnector,
    'pinterest': PinterestConnector,
    
    # Productivity
    'gmail': GmailConnector,
    'outlook': OutlookConnector,
    'notion': NotionConnector,
    'slack': SlackConnector,
    'teams': TeamsConnector,
    'zoom': ZoomConnector,
    'calendar': CalendarConnector,
    'trello': TrelloConnector,
    'asana': AsanaConnector,
    'jira': JiraConnector,
    
    # Development
    'github': GitHubConnector,
    'gitlab': GitLabConnector,
    'bitbucket': BitbucketConnector,
    'stackoverflow': StackOverflowConnector,
    'codepen': CodePenConnector,
    
    # E-commerce
    'amazon': AmazonConnector,
    'shopify': ShopifyConnector,
    'ebay': EBayConnector,
    'etsy': EtsyConnector,
    'stripe': StripeConnector,
    
    # Cloud Storage
    'dropbox': DropboxConnector,
    'google_drive': GoogleDriveConnector,
    'onedrive': OneDriveConnector,
    'aws_s3': AWSS3Connector,
    
    # AI Services
    'openai': OpenAIConnector,
    'anthropic': AnthropicConnector,
    'google_ai': GoogleAIConnector,
    
    # Marketing
    'mailchimp': MailchimpConnector,
    'hubspot': HubspotConnector,
    'salesforce': SalesforceConnector,
}

def get_connector(platform_name: str):
    """Get connector class for a platform"""
    return PLATFORM_CONNECTORS.get(platform_name.lower())

def list_available_platforms():
    """List all available platform connectors"""
    return list(PLATFORM_CONNECTORS.keys())

def get_platform_categories():
    """Get platforms organized by categories"""
    return {
        'social_media': [
            'twitter', 'linkedin', 'facebook', 'instagram', 'youtube',
            'tiktok', 'discord', 'telegram', 'reddit', 'pinterest'
        ],
        'productivity': [
            'gmail', 'outlook', 'notion', 'slack', 'teams',
            'zoom', 'calendar', 'trello', 'asana', 'jira'
        ],
        'development': [
            'github', 'gitlab', 'bitbucket', 'stackoverflow', 'codepen'
        ],
        'ecommerce': [
            'amazon', 'shopify', 'ebay', 'etsy', 'stripe'
        ],
        'cloud_storage': [
            'dropbox', 'google_drive', 'onedrive', 'aws_s3'
        ],
        'ai_services': [
            'openai', 'anthropic', 'google_ai'
        ],
        'marketing': [
            'mailchimp', 'hubspot', 'salesforce'
        ]
    }