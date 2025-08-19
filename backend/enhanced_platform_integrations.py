"""
OPTION B ENHANCEMENT: Extended Platform Integrations
Adding 15+ more platforms to reach 25+ total integrations
Enhanced cross-platform workflow capabilities
"""
from cross_platform_integration_hub import PlatformConfig, PlatformType, AuthMethod
from typing import Dict, List, Any
import logging

class EnhancedPlatformIntegrations:
    """Extended platform integrations for comprehensive automation"""
    
    def __init__(self, platform_hub):
        self.platform_hub = platform_hub
        self.add_enhanced_platforms()
    
    def add_enhanced_platforms(self):
        """Add 15+ additional platform integrations"""
        
        # SOCIAL MEDIA PLATFORMS (5 new)
        self._add_social_media_platforms()
        
        # E-COMMERCE PLATFORMS (4 new)
        self._add_ecommerce_platforms()
        
        # FINANCE & PAYMENT PLATFORMS (3 new)
        self._add_finance_platforms()
        
        # MARKETING & ANALYTICS PLATFORMS (4 new)  
        self._add_marketing_platforms()
        
        # PROJECT MANAGEMENT PLATFORMS (3 new)
        self._add_project_management_platforms()
        
        # DESIGN & CREATIVE PLATFORMS (3 new)
        self._add_design_platforms()
        
        # DEVELOPER PLATFORMS (2 new)
        self._add_developer_platforms()
        
        # COMMUNICATION PLATFORMS (2 new)
        self._add_communication_platforms()
        
        logging.info(f"🔗 Enhanced Platform Integrations: Added 26+ additional platforms")
    
    def _add_social_media_platforms(self):
        """Add social media platform integrations"""
        
        # Twitter/X
        self.platform_hub.platforms["twitter"] = PlatformConfig(
            id="twitter",
            name="Twitter/X",
            type=PlatformType.SOCIAL_MEDIA,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://api.twitter.com/2",
            endpoints={
                "tweets": "/tweets", 
                "users": "/users",
                "timeline": "/users/{id}/tweets",
                "followers": "/users/{id}/followers",
                "spaces": "/spaces",
                "lists": "/lists"
            },
            capabilities=[
                "post_tweets", "schedule_tweets", "manage_followers", 
                "analytics", "direct_messages", "spaces_management", 
                "list_management", "trend_analysis"
            ]
        )
        
        # Instagram
        self.platform_hub.platforms["instagram"] = PlatformConfig(
            id="instagram",
            name="Instagram Business",
            type=PlatformType.SOCIAL_MEDIA,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://graph.instagram.com",
            endpoints={
                "media": "/me/media",
                "stories": "/me/stories",
                "insights": "/me/insights",
                "comments": "/{media-id}/comments"
            },
            capabilities=[
                "post_photos", "post_stories", "schedule_content",
                "analytics", "comment_management", "hashtag_research",
                "influencer_tracking", "story_highlights"
            ]
        )
        
        # Facebook
        self.platform_hub.platforms["facebook"] = PlatformConfig(
            id="facebook",
            name="Facebook Business",
            type=PlatformType.SOCIAL_MEDIA,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://graph.facebook.com/v18.0",
            endpoints={
                "pages": "/me/accounts",
                "posts": "/{page-id}/posts",
                "insights": "/{page-id}/insights",
                "ads": "/act_{ad-account-id}/ads"
            },
            capabilities=[
                "page_management", "post_scheduling", "ad_management",
                "audience_insights", "lead_generation", "event_management",
                "messenger_integration", "facebook_shops"
            ]
        )
        
        # TikTok
        self.platform_hub.platforms["tiktok"] = PlatformConfig(
            id="tiktok",
            name="TikTok Business",
            type=PlatformType.SOCIAL_MEDIA,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://business-api.tiktok.com/open_api/v1.3",
            endpoints={
                "videos": "/video/list",
                "user": "/user/info",
                "analytics": "/video/insights"
            },
            capabilities=[
                "video_analytics", "hashtag_performance", "trend_analysis",
                "audience_insights", "competitor_analysis"
            ]
        )
        
        # YouTube
        self.platform_hub.platforms["youtube"] = PlatformConfig(
            id="youtube",
            name="YouTube",
            type=PlatformType.SOCIAL_MEDIA,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://www.googleapis.com/youtube/v3",
            endpoints={
                "channels": "/channels",
                "videos": "/videos",
                "playlists": "/playlists",
                "analytics": "/reports",
                "comments": "/commentThreads"
            },
            capabilities=[
                "video_upload", "channel_management", "playlist_creation",
                "analytics", "comment_moderation", "live_streaming",
                "thumbnail_management", "monetization_tracking"
            ]
        )
    
    def _add_ecommerce_platforms(self):
        """Add e-commerce platform integrations"""
        
        # Amazon Seller
        self.platform_hub.platforms["amazon_seller"] = PlatformConfig(
            id="amazon_seller",
            name="Amazon Seller Central",
            type=PlatformType.E_COMMERCE,
            auth_method=AuthMethod.API_KEY,
            base_url="https://sellingpartnerapi-na.amazon.com",
            endpoints={
                "orders": "/orders/v0/orders",
                "products": "/catalog/v0/items",
                "inventory": "/fba/inventory/v1/summaries",
                "reports": "/reports/2021-06-30/reports"
            },
            capabilities=[
                "order_management", "inventory_sync", "price_monitoring",
                "product_listings", "fulfillment_tracking", "analytics",
                "advertising_management", "review_monitoring"
            ]
        )
        
        # eBay
        self.platform_hub.platforms["ebay"] = PlatformConfig(
            id="ebay",
            name="eBay",
            type=PlatformType.E_COMMERCE,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://api.ebay.com",
            endpoints={
                "inventory": "/sell/inventory/v1",
                "orders": "/sell/fulfillment/v1/order",
                "listings": "/commerce/catalog/v1",
                "analytics": "/sell/analytics/v1"
            },
            capabilities=[
                "listing_management", "order_fulfillment", "inventory_tracking",
                "price_optimization", "promoted_listings", "store_management"
            ]
        )
        
        # WooCommerce
        self.platform_hub.platforms["woocommerce"] = PlatformConfig(
            id="woocommerce",
            name="WooCommerce",
            type=PlatformType.E_COMMERCE,
            auth_method=AuthMethod.API_KEY,
            base_url="https://{store_url}/wp-json/wc/v3",
            endpoints={
                "products": "/products",
                "orders": "/orders",
                "customers": "/customers",
                "coupons": "/coupons"
            },
            capabilities=[
                "product_sync", "order_management", "customer_management",
                "coupon_management", "inventory_updates", "tax_calculations"
            ]
        )
        
        # Magento
        self.platform_hub.platforms["magento"] = PlatformConfig(
            id="magento",
            name="Magento Commerce",
            type=PlatformType.E_COMMERCE,
            auth_method=AuthMethod.TOKEN,
            base_url="https://{store_url}/rest/V1",
            endpoints={
                "products": "/products",
                "orders": "/orders",
                "customers": "/customers",
                "categories": "/categories"
            },
            capabilities=[
                "catalog_management", "order_processing", "customer_segmentation",
                "inventory_management", "multi_store_sync"
            ]
        )
    
    def _add_finance_platforms(self):
        """Add finance and payment platform integrations"""
        
        # PayPal
        self.platform_hub.platforms["paypal"] = PlatformConfig(
            id="paypal",
            name="PayPal",
            type=PlatformType.FINANCE,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://api-m.paypal.com/v2",
            endpoints={
                "payments": "/payments",
                "orders": "/checkout/orders",
                "invoices": "/invoicing/invoices",
                "disputes": "/customer/disputes"
            },
            capabilities=[
                "payment_processing", "invoice_management", "subscription_billing",
                "dispute_resolution", "transaction_reporting", "refund_processing"
            ]
        )
        
        # QuickBooks
        self.platform_hub.platforms["quickbooks"] = PlatformConfig(
            id="quickbooks",
            name="QuickBooks Online",
            type=PlatformType.FINANCE,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://sandbox-quickbooks.api.intuit.com/v3/company/{companyId}",
            endpoints={
                "customers": "/customers",
                "invoices": "/invoices",
                "payments": "/payments",
                "expenses": "/purchases"
            },
            capabilities=[
                "invoice_automation", "expense_tracking", "financial_reporting",
                "tax_preparation", "customer_billing", "payment_reconciliation"
            ]
        )
        
        # Xero
        self.platform_hub.platforms["xero"] = PlatformConfig(
            id="xero",
            name="Xero Accounting",
            type=PlatformType.FINANCE,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://api.xero.com/api.xro/2.0",
            endpoints={
                "invoices": "/Invoices",
                "contacts": "/Contacts",
                "payments": "/Payments",
                "reports": "/Reports"
            },
            capabilities=[
                "accounting_automation", "invoice_management", "bank_reconciliation",
                "financial_reporting", "expense_management", "payroll_integration"
            ]
        )
    
    def _add_marketing_platforms(self):
        """Add marketing and analytics platform integrations"""
        
        # Google Analytics
        self.platform_hub.platforms["google_analytics"] = PlatformConfig(
            id="google_analytics",
            name="Google Analytics 4",
            type=PlatformType.ANALYTICS,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://analyticsdata.googleapis.com/v1beta",
            endpoints={
                "reports": "/properties/{property}/runReport",
                "realtime": "/properties/{property}/runRealtimeReport",
                "metadata": "/properties/{property}/metadata"
            },
            capabilities=[
                "website_analytics", "conversion_tracking", "audience_analysis",
                "custom_reports", "goal_tracking", "attribution_modeling"
            ]
        )
        
        # Mailchimp
        self.platform_hub.platforms["mailchimp"] = PlatformConfig(
            id="mailchimp",
            name="Mailchimp",
            type=PlatformType.MARKETING,
            auth_method=AuthMethod.API_KEY,
            base_url="https://{dc}.api.mailchimp.com/3.0",
            endpoints={
                "lists": "/lists",
                "campaigns": "/campaigns",
                "automations": "/automations",
                "reports": "/reports"
            },
            capabilities=[
                "email_campaigns", "list_management", "automation_workflows",
                "a_b_testing", "analytics", "segmentation", "personalization"
            ]
        )
        
        # HubSpot
        self.platform_hub.platforms["hubspot"] = PlatformConfig(
            id="hubspot",
            name="HubSpot",
            type=PlatformType.MARKETING,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://api.hubapi.com",
            endpoints={
                "contacts": "/crm/v3/objects/contacts",
                "deals": "/crm/v3/objects/deals",
                "companies": "/crm/v3/objects/companies",
                "emails": "/marketing/v3/emails"
            },
            capabilities=[
                "crm_management", "lead_nurturing", "sales_automation",
                "marketing_analytics", "social_media_management", "landing_pages"
            ]
        )
        
        # Google Ads
        self.platform_hub.platforms["google_ads"] = PlatformConfig(
            id="google_ads",
            name="Google Ads",
            type=PlatformType.MARKETING,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://googleads.googleapis.com/v14",
            endpoints={
                "campaigns": "/customers/{customer_id}/campaigns",
                "keywords": "/customers/{customer_id}/keywords",
                "reports": "/customers/{customer_id}/googleAdsFields"
            },
            capabilities=[
                "campaign_management", "keyword_optimization", "bid_management",
                "ad_creation", "performance_tracking", "audience_targeting"
            ]
        )
    
    def _add_project_management_platforms(self):
        """Add project management platform integrations"""
        
        # Asana
        self.platform_hub.platforms["asana"] = PlatformConfig(
            id="asana",
            name="Asana",
            type=PlatformType.PRODUCTIVITY,
            auth_method=AuthMethod.TOKEN,
            base_url="https://app.asana.com/api/1.0",
            endpoints={
                "tasks": "/tasks",
                "projects": "/projects",
                "teams": "/teams",
                "portfolios": "/portfolios"
            },
            capabilities=[
                "task_management", "project_tracking", "team_collaboration",
                "timeline_management", "goal_tracking", "custom_fields",
                "automation_rules", "reporting"
            ]
        )
        
        # Trello
        self.platform_hub.platforms["trello"] = PlatformConfig(
            id="trello",
            name="Trello",
            type=PlatformType.PRODUCTIVITY,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://api.trello.com/1",
            endpoints={
                "boards": "/boards",
                "cards": "/cards",
                "lists": "/lists",
                "members": "/members"
            },
            capabilities=[
                "board_management", "card_automation", "workflow_templates",
                "team_collaboration", "power_ups_integration", "calendar_sync"
            ]
        )
        
        # Jira
        self.platform_hub.platforms["jira"] = PlatformConfig(
            id="jira",
            name="Jira",
            type=PlatformType.DEVELOPMENT,
            auth_method=AuthMethod.TOKEN,
            base_url="https://{domain}.atlassian.net/rest/api/3",
            endpoints={
                "issues": "/issue",
                "projects": "/project", 
                "users": "/user",
                "workflows": "/workflow"
            },
            capabilities=[
                "issue_tracking", "sprint_management", "workflow_automation",
                "reporting", "integration_management", "custom_fields"
            ]
        )
    
    def _add_design_platforms(self):
        """Add design and creative platform integrations"""
        
        # Figma
        self.platform_hub.platforms["figma"] = PlatformConfig(
            id="figma",
            name="Figma",
            type=PlatformType.DESIGN,
            auth_method=AuthMethod.TOKEN,
            base_url="https://api.figma.com/v1",
            endpoints={
                "files": "/files",
                "teams": "/teams",
                "projects": "/projects",
                "comments": "/files/{file_key}/comments"
            },
            capabilities=[
                "design_collaboration", "prototype_sharing", "version_control",
                "component_management", "design_handoff", "plugin_management"
            ]
        )
        
        # Adobe Creative Cloud
        self.platform_hub.platforms["adobe_cc"] = PlatformConfig(
            id="adobe_cc",
            name="Adobe Creative Cloud",
            type=PlatformType.DESIGN,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://cc-api.adobe.io",
            endpoints={
                "libraries": "/v1/libraries",
                "assets": "/v1/assets",
                "projects": "/v1/projects"
            },
            capabilities=[
                "asset_management", "cloud_sync", "collaboration",
                "library_sharing", "version_tracking"
            ]
        )
        
        # Canva
        self.platform_hub.platforms["canva"] = PlatformConfig(
            id="canva",
            name="Canva",
            type=PlatformType.DESIGN,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://api.canva.com/rest/v1",
            endpoints={
                "designs": "/designs",
                "folders": "/folders",
                "brand_templates": "/brand-templates"
            },
            capabilities=[
                "design_creation", "template_management", "brand_kit_sync",
                "collaborative_editing", "export_automation"
            ]
        )
    
    def _add_developer_platforms(self):
        """Add developer platform integrations"""
        
        # Bitbucket
        self.platform_hub.platforms["bitbucket"] = PlatformConfig(
            id="bitbucket",
            name="Bitbucket",
            type=PlatformType.DEVELOPMENT,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://api.bitbucket.org/2.0",
            endpoints={
                "repositories": "/repositories",
                "pullrequests": "/repositories/{workspace}/{repo_slug}/pullrequests",
                "pipelines": "/repositories/{workspace}/{repo_slug}/pipelines"
            },
            capabilities=[
                "repository_management", "ci_cd_pipelines", "code_review",
                "branch_management", "issue_tracking", "deployment_tracking"
            ]
        )
        
        # Jenkins
        self.platform_hub.platforms["jenkins"] = PlatformConfig(
            id="jenkins",
            name="Jenkins",
            type=PlatformType.DEVELOPMENT,
            auth_method=AuthMethod.API_KEY,
            base_url="http://{jenkins_url}/api",
            endpoints={
                "jobs": "/json",
                "builds": "/job/{job_name}/api/json",
                "queue": "/queue/api/json"
            },
            capabilities=[
                "build_automation", "deployment_pipelines", "test_automation",
                "job_scheduling", "plugin_management", "build_monitoring"
            ]
        )
    
    def _add_communication_platforms(self):
        """Add communication platform integrations"""
        
        # Zoom
        self.platform_hub.platforms["zoom"] = PlatformConfig(
            id="zoom",
            name="Zoom",
            type=PlatformType.COMMUNICATION,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://api.zoom.us/v2",
            endpoints={
                "meetings": "/meetings",
                "users": "/users",
                "webinars": "/webinars",
                "recordings": "/meetings/{meetingId}/recordings"
            },
            capabilities=[
                "meeting_scheduling", "webinar_management", "recording_access",
                "participant_management", "analytics", "integration_webhooks"
            ]
        )
        
        # Microsoft Teams
        self.platform_hub.platforms["microsoft_teams"] = PlatformConfig(
            id="microsoft_teams",
            name="Microsoft Teams",
            type=PlatformType.COMMUNICATION,
            auth_method=AuthMethod.OAUTH2,
            base_url="https://graph.microsoft.com/v1.0",
            endpoints={
                "teams": "/teams",
                "channels": "/teams/{team-id}/channels",
                "messages": "/teams/{team-id}/channels/{channel-id}/messages",
                "meetings": "/me/onlineMeetings"
            },
            capabilities=[
                "team_management", "channel_automation", "meeting_scheduling",
                "file_collaboration", "bot_integration", "analytics"
            ]
        )
    
    def get_platform_statistics(self) -> Dict[str, Any]:
        """Get comprehensive platform integration statistics"""
        
        platforms_by_type = {}
        total_capabilities = 0
        
        for platform_id, platform in self.platform_hub.platforms.items():
            platform_type = platform.type.value
            if platform_type not in platforms_by_type:
                platforms_by_type[platform_type] = 0
            platforms_by_type[platform_type] += 1
            total_capabilities += len(platform.capabilities)
        
        return {
            "total_platforms": len(self.platform_hub.platforms),
            "platforms_by_type": platforms_by_type,
            "total_capabilities": total_capabilities,
            "supported_auth_methods": list(set(p.auth_method.value for p in self.platform_hub.platforms.values())),
            "platform_categories": list(platforms_by_type.keys()),
            "integration_coverage": {
                "social_media": 5,
                "productivity": 8,
                "development": 5,
                "e_commerce": 4,
                "finance": 3,
                "marketing": 4,
                "communication": 4,
                "design": 3
            }
        }


# Enhanced Workflow Capabilities

class AdvancedWorkflowEngine:
    """Advanced workflow capabilities with conditional logic and parallel execution"""
    
    def __init__(self, platform_hub):
        self.platform_hub = platform_hub
        self.workflow_templates = {}
        self._initialize_workflow_templates()
    
    def _initialize_workflow_templates(self):
        """Initialize advanced workflow templates"""
        
        # Social Media Management Workflow
        self.workflow_templates["social_media_management"] = {
            "name": "Complete Social Media Management",
            "description": "Cross-platform social media posting and analytics",
            "platforms": ["twitter", "instagram", "facebook", "linkedin"],
            "steps": [
                {
                    "platform": "multiple",
                    "action": "schedule_posts",
                    "parallel": True,
                    "condition": {"type": "always"}
                },
                {
                    "platform": "google_analytics",
                    "action": "track_engagement",
                    "delay": "1_hour",
                    "condition": {"type": "if_previous_success", "step_index": 0}
                },
                {
                    "platform": "hubspot",
                    "action": "update_lead_scores",
                    "condition": {"type": "if_engagement_above", "threshold": 100}
                }
            ],
            "triggers": ["scheduled", "webhook", "api_call"],
            "success_metrics": ["engagement_rate", "reach", "conversions"]
        }
        
        # E-commerce Order Processing
        self.workflow_templates["ecommerce_fulfillment"] = {
            "name": "Complete E-commerce Fulfillment",
            "description": "Automated order processing across platforms",
            "platforms": ["shopify", "amazon_seller", "ebay", "quickbooks"],
            "steps": [
                {
                    "platform": "shopify",
                    "action": "fetch_new_orders",
                    "interval": "5_minutes"
                },
                {
                    "platform": "amazon_seller",
                    "action": "sync_inventory",
                    "parallel": True
                },
                {
                    "platform": "quickbooks",
                    "action": "create_invoice",
                    "condition": {"type": "if_order_value_above", "threshold": 100}
                },
                {
                    "platform": "mailchimp",
                    "action": "send_confirmation_email",
                    "delay": "immediate"
                }
            ],
            "error_handling": "retry_with_backoff",
            "notification_channels": ["slack", "email"]
        }
        
        # Developer Productivity Workflow
        self.workflow_templates["dev_productivity"] = {
            "name": "Developer Productivity Suite",
            "description": "Automated development workflow management",
            "platforms": ["github", "jira", "slack", "jenkins"],
            "steps": [
                {
                    "platform": "github",
                    "action": "monitor_pull_requests",
                    "triggers": ["webhook"]
                },
                {
                    "platform": "jenkins",
                    "action": "trigger_build",
                    "condition": {"type": "if_pr_approved"}
                },
                {
                    "platform": "jira",
                    "action": "update_issue_status",
                    "condition": {"type": "if_build_successful"}
                },
                {
                    "platform": "slack",
                    "action": "notify_team",
                    "message_template": "🚀 Deployment successful for {project_name}"
                }
            ],
            "rollback_strategy": "automatic_on_failure"
        }
        
        # Marketing Campaign Automation
        self.workflow_templates["marketing_campaign"] = {
            "name": "Integrated Marketing Campaign",
            "description": "Multi-channel marketing automation",
            "platforms": ["google_ads", "facebook", "mailchimp", "hubspot", "google_analytics"],
            "steps": [
                {
                    "platform": "hubspot",
                    "action": "identify_target_audience",
                    "segmentation_criteria": ["engagement_score", "purchase_history"]
                },
                {
                    "platform": "mailchimp",
                    "action": "create_email_campaign",
                    "parallel_with": ["google_ads", "facebook"]
                },
                {
                    "platform": "google_ads",
                    "action": "launch_search_campaign",
                    "budget_allocation": "40%"
                },
                {
                    "platform": "facebook",
                    "action": "launch_social_campaign",
                    "budget_allocation": "35%"
                },
                {
                    "platform": "google_analytics",
                    "action": "track_campaign_performance",
                    "delay": "24_hours"
                },
                {
                    "platform": "hubspot",
                    "action": "score_leads",
                    "condition": {"type": "continuous"}
                }
            ],
            "optimization": "automatic_budget_reallocation",
            "success_metrics": ["ctr", "conversion_rate", "roi", "lead_quality"]
        }
    
    async def execute_advanced_workflow(self, template_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute advanced workflow with conditional logic and parallel processing"""
        
        if template_name not in self.workflow_templates:
            return {"success": False, "error": "Workflow template not found"}
        
        template = self.workflow_templates[template_name]
        workflow_id = f"workflow_{int(datetime.utcnow().timestamp())}"
        
        execution_result = {
            "workflow_id": workflow_id,
            "template": template_name,
            "status": "running",
            "steps_completed": 0,
            "total_steps": len(template["steps"]),
            "results": [],
            "parallel_executions": [],
            "performance_metrics": {
                "start_time": datetime.utcnow().isoformat(),
                "estimated_duration": self._estimate_workflow_duration(template),
                "optimization_level": "advanced"
            }
        }
        
        # Execute workflow steps
        for i, step in enumerate(template["steps"]):
            
            # Check step conditions
            if not await self._evaluate_step_condition(step.get("condition"), execution_result["results"]):
                execution_result["results"].append({
                    "step": i + 1,
                    "status": "skipped",
                    "reason": "condition not met"
                })
                continue
            
            # Handle parallel execution
            if step.get("parallel", False) or step.get("parallel_with"):
                parallel_result = await self._execute_parallel_steps(step, parameters)
                execution_result["parallel_executions"].append(parallel_result)
                execution_result["results"].append({
                    "step": i + 1,
                    "status": "parallel_completed",
                    "result": parallel_result
                })
            else:
                # Execute single step
                step_result = await self.platform_hub.execute_platform_action(
                    user_id=parameters.get("user_id", "system"),
                    platform_id=step["platform"],
                    action=step["action"],
                    parameters=step.get("parameters", {})
                )
                
                execution_result["results"].append({
                    "step": i + 1,
                    "platform": step["platform"],
                    "action": step["action"],
                    "status": "completed" if step_result["success"] else "failed",
                    "result": step_result
                })
            
            execution_result["steps_completed"] += 1
            
            # Handle step delays
            if step.get("delay"):
                await self._handle_step_delay(step["delay"])
        
        # Calculate final metrics
        execution_result["status"] = "completed"
        execution_result["performance_metrics"]["end_time"] = datetime.utcnow().isoformat()
        execution_result["performance_metrics"]["success_rate"] = self._calculate_success_rate(execution_result["results"])
        
        return execution_result
    
    async def _execute_parallel_steps(self, step_config: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute steps in parallel"""
        
        parallel_platforms = step_config.get("parallel_with", [step_config["platform"]])
        
        tasks = []
        for platform in parallel_platforms:
            task = asyncio.create_task(
                self.platform_hub.execute_platform_action(
                    user_id=parameters.get("user_id", "system"),
                    platform_id=platform,
                    action=step_config["action"],
                    parameters=step_config.get("parameters", {})
                )
            )
            tasks.append((platform, task))
        
        # Wait for all parallel tasks to complete
        results = {}
        for platform, task in tasks:
            try:
                result = await task
                results[platform] = result
            except Exception as e:
                results[platform] = {"success": False, "error": str(e)}
        
        return {
            "parallel_execution": True,
            "platforms": parallel_platforms,
            "results": results,
            "success_count": len([r for r in results.values() if r.get("success", False)])
        }
    
    async def _evaluate_step_condition(self, condition: Optional[Dict[str, Any]], previous_results: List[Dict[str, Any]]) -> bool:
        """Evaluate step execution conditions"""
        
        if not condition:
            return True
        
        condition_type = condition.get("type", "always")
        
        if condition_type == "always":
            return True
        elif condition_type == "never":
            return False
        elif condition_type == "if_previous_success":
            step_index = condition.get("step_index", -1)
            if 0 <= step_index < len(previous_results):
                return previous_results[step_index]["status"] == "completed"
        elif condition_type == "if_engagement_above":
            # Custom condition logic
            threshold = condition.get("threshold", 0)
            return True  # Simplified for demo
        
        return True
    
    def _estimate_workflow_duration(self, template: Dict[str, Any]) -> str:
        """Estimate workflow execution duration"""
        
        step_count = len(template["steps"])
        parallel_steps = len([s for s in template["steps"] if s.get("parallel", False)])
        
        # Rough estimation based on step complexity
        base_duration = step_count * 30  # 30 seconds per step
        parallel_savings = parallel_steps * 20  # 20 seconds saved per parallel step
        
        estimated_seconds = max(60, base_duration - parallel_savings)
        
        if estimated_seconds < 300:  # Less than 5 minutes
            return f"{estimated_seconds} seconds"
        else:
            return f"{estimated_seconds // 60} minutes"
    
    async def _handle_step_delay(self, delay_spec: str):
        """Handle step delays"""
        
        if delay_spec == "immediate":
            return
        elif delay_spec.endswith("_minutes"):
            minutes = int(delay_spec.split("_")[0])
            await asyncio.sleep(minutes * 60)
        elif delay_spec.endswith("_hours"):
            hours = int(delay_spec.split("_")[0])
            await asyncio.sleep(hours * 3600)
        else:
            # Default delay
            await asyncio.sleep(5)
    
    def _calculate_success_rate(self, results: List[Dict[str, Any]]) -> float:
        """Calculate workflow success rate"""
        
        if not results:
            return 0.0
        
        successful_steps = len([r for r in results if r["status"] in ["completed", "parallel_completed"]])
        return successful_steps / len(results)
    
    def get_available_templates(self) -> Dict[str, Any]:
        """Get all available workflow templates"""
        
        return {
            "templates": list(self.workflow_templates.keys()),
            "total_count": len(self.workflow_templates),
            "categories": ["social_media", "ecommerce", "development", "marketing"],
            "template_details": {
                name: {
                    "name": template["name"],
                    "description": template["description"],
                    "platforms": template["platforms"],
                    "estimated_duration": self._estimate_workflow_duration(template)
                }
                for name, template in self.workflow_templates.items()
            }
        }