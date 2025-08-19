# Platform Integrations for AETHER
# Comprehensive integration hub for 50+ platforms

from .base_connector import BasePlatformConnector
from .twitter_connector import TwitterConnector
from .github_connector import GitHubConnector

# Platform registry for dynamic loading
PLATFORM_CONNECTORS = {
    # Currently implemented
    'twitter': TwitterConnector,
    'github': GitHubConnector,
    
    # Planned integrations (will be implemented in full enhancement phase)
    'linkedin': None,
    'facebook': None,
    'instagram': None,
    'youtube': None,
    'discord': None,
    'slack': None,
    'notion': None,
    # ... more will be added
}

def get_connector(platform_name: str):
    """Get connector class for a platform"""
    return PLATFORM_CONNECTORS.get(platform_name.lower())

def list_available_platforms():
    """List all available platform connectors"""
    return [k for k, v in PLATFORM_CONNECTORS.items() if v is not None]

def get_platform_categories():
    """Get platforms organized by categories"""
    return {
        'social_media': ['twitter', 'linkedin', 'facebook', 'instagram'],
        'development': ['github', 'gitlab', 'bitbucket'],
        'productivity': ['slack', 'notion', 'trello'],
        # More categories will be added
    }