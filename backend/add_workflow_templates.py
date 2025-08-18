#!/usr/bin/env python3
"""
Add missing workflow templates to the database
"""

from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/aether_browser")
client = MongoClient(MONGO_URL)
db = client.aether_browser

# Basic web scraping workflow template
basic_web_scraping_template = {
    "template_id": "basic_web_scraping",
    "name": "Basic Web Scraping",
    "description": "Extract data from web pages using simple scraping techniques",
    "category": "data_extraction",
    "difficulty": "beginner",
    "estimated_time": 300,  # 5 minutes
    "parameters": {
        "target_url": {"type": "url", "required": True, "description": "URL to scrape data from"},
        "data_selectors": {"type": "array", "required": True, "description": "CSS selectors for data extraction"},
        "output_format": {"type": "string", "default": "json", "description": "Output format (json, csv, xml)"}
    },
    "steps": [
        {
            "id": "fetch_page",
            "type": "http_request",
            "name": "Fetch Web Page",
            "config": {
                "method": "GET",
                "url": "${target_url}",
                "headers": {"User-Agent": "AETHER Browser Automation"},
                "timeout": 30
            },
            "on_success": "parse_content",
            "on_failure": "fail"
        },
        {
            "id": "parse_content",
            "type": "data_transformation",
            "name": "Parse Page Content",
            "config": {
                "transformation": "html_parse",
                "selectors": "${data_selectors}",
                "input_data": "${fetch_page.response_body}"
            },
            "on_success": "format_output",
            "on_failure": "fail"
        },
        {
            "id": "format_output",
            "type": "data_transformation", 
            "name": "Format Output",
            "config": {
                "transformation": "format",
                "format": "${output_format}",
                "input_data": "${parse_content.parsed_data}"
            },
            "on_success": "complete",
            "on_failure": "fail"
        }
    ],
    "created_at": datetime.utcnow(),
    "created_by": "system",
    "version": "1.0",
    "tags": ["web_scraping", "data_extraction", "basic", "automation"]
}

# Email automation template
email_automation_template = {
    "template_id": "email_automation",
    "name": "Email Automation",
    "description": "Send automated emails with dynamic content",
    "category": "communication",
    "difficulty": "beginner",
    "estimated_time": 120,  # 2 minutes
    "parameters": {
        "recipient": {"type": "email", "required": True, "description": "Email recipient"},
        "subject": {"type": "string", "required": True, "description": "Email subject"},
        "message": {"type": "text", "required": True, "description": "Email message content"}
    },
    "steps": [
        {
            "id": "prepare_email",
            "type": "data_transformation",
            "name": "Prepare Email Content",
            "config": {
                "transformation": "format",
                "template": "To: ${recipient}\nSubject: ${subject}\nMessage: ${message}",
                "input_data": {}
            },
            "on_success": "send_email",
            "on_failure": "fail"
        },
        {
            "id": "send_email",
            "type": "integration_action",
            "name": "Send Email",
            "config": {
                "integration": "email",
                "action": "send",
                "parameters": {
                    "to": "${recipient}",
                    "subject": "${subject}",
                    "body": "${message}"
                }
            },
            "on_success": "complete",
            "on_failure": "fail"
        }
    ],
    "created_at": datetime.utcnow(),
    "created_by": "system",
    "version": "1.0",
    "tags": ["email", "communication", "automation", "basic"]
}

# Social media posting template
social_media_template = {
    "template_id": "social_media_post",
    "name": "Social Media Posting",
    "description": "Post content to multiple social media platforms",
    "category": "social_media",
    "difficulty": "intermediate",
    "estimated_time": 180,  # 3 minutes
    "parameters": {
        "content": {"type": "text", "required": True, "description": "Post content"},
        "platforms": {"type": "array", "required": True, "description": "Target platforms (twitter, facebook, linkedin)"},
        "schedule_time": {"type": "datetime", "required": False, "description": "Schedule for later posting"}
    },
    "steps": [
        {
            "id": "prepare_content",
            "type": "ai_processing",
            "name": "Optimize Content",
            "config": {
                "prompt": "Optimize this social media post for engagement: ${content}",
                "model_type": "content_optimization"
            },
            "on_success": "post_to_platforms",
            "on_failure": "post_original"
        },
        {
            "id": "post_to_platforms",
            "type": "parallel_group",
            "name": "Post to All Platforms",
            "config": {
                "parallel_steps": [
                    {
                        "id": "post_twitter",
                        "type": "integration_action",
                        "condition": "twitter in ${platforms}",
                        "config": {
                            "integration": "twitter",
                            "action": "post",
                            "parameters": {"content": "${prepare_content.ai_response}"}
                        }
                    },
                    {
                        "id": "post_facebook", 
                        "type": "integration_action",
                        "condition": "facebook in ${platforms}",
                        "config": {
                            "integration": "facebook",
                            "action": "post", 
                            "parameters": {"content": "${prepare_content.ai_response}"}
                        }
                    },
                    {
                        "id": "post_linkedin",
                        "type": "integration_action",
                        "condition": "linkedin in ${platforms}",
                        "config": {
                            "integration": "linkedin",
                            "action": "post",
                            "parameters": {"content": "${prepare_content.ai_response}"}
                        }
                    }
                ]
            },
            "on_success": "complete",
            "on_failure": "fail"
        }
    ],
    "created_at": datetime.utcnow(),
    "created_by": "system",
    "version": "1.0",
    "tags": ["social_media", "posting", "automation", "multi_platform"]
}

def add_templates():
    """Add all missing workflow templates"""
    templates = [
        basic_web_scraping_template,
        email_automation_template,
        social_media_template
    ]
    
    for template in templates:
        # Check if template already exists
        existing = db.workflow_templates.find_one({"template_id": template["template_id"]})
        
        if existing:
            print(f"✅ Template {template['template_id']} already exists, updating...")
            db.workflow_templates.replace_one(
                {"template_id": template["template_id"]}, 
                template
            )
        else:
            print(f"➕ Adding new template {template['template_id']}...")
            db.workflow_templates.insert_one(template)
    
    print(f"\n🎯 Added {len(templates)} workflow templates to database")
    
    # Verify templates were added
    total_templates = db.workflow_templates.count_documents({})
    print(f"📊 Total workflow templates in database: {total_templates}")

if __name__ == "__main__":
    add_templates()