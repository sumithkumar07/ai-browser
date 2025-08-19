"""
GitHub Platform Integration for AETHER
Advanced automation capabilities for GitHub platform
"""

import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import base64
import logging

class GitHubConnector:
    def __init__(self, access_token: str, username: str = None):
        self.access_token = access_token
        self.username = username
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AETHER-GitHub-Integration"
        }
        
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make HTTP request to GitHub API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{endpoint}"
                
                async with session.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data
                ) as response:
                    result = await response.json()
                    
                    if response.status >= 200 and response.status < 300:
                        return {"success": True, "data": result}
                    else:
                        return {"success": False, "error": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # REPOSITORY OPERATIONS
    async def create_repository(self, name: str, description: str = "", private: bool = False) -> Dict[str, Any]:
        """Create a new repository"""
        try:
            data = {
                "name": name,
                "description": description,
                "private": private,
                "auto_init": True,
                "gitignore_template": "Python",
                "license_template": "mit"
            }
            
            result = await self._make_request("POST", "/user/repos", data)
            
            if result["success"]:
                repo_data = result["data"]
                return {
                    "success": True,
                    "repository": {
                        "name": repo_data["name"],
                        "full_name": repo_data["full_name"],
                        "url": repo_data["html_url"],
                        "clone_url": repo_data["clone_url"],
                        "ssh_url": repo_data["ssh_url"],
                        "private": repo_data["private"],
                        "created_at": repo_data["created_at"]
                    }
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information"""
        try:
            result = await self._make_request("GET", f"/repos/{owner}/{repo}")
            
            if result["success"]:
                repo_data = result["data"]
                return {
                    "success": True,
                    "repository": {
                        "name": repo_data["name"],
                        "full_name": repo_data["full_name"],
                        "description": repo_data["description"],
                        "url": repo_data["html_url"],
                        "stars": repo_data["stargazers_count"],
                        "forks": repo_data["forks_count"],
                        "watchers": repo_data["watchers_count"],
                        "language": repo_data["language"],
                        "size": repo_data["size"],
                        "created_at": repo_data["created_at"],
                        "updated_at": repo_data["updated_at"],
                        "private": repo_data["private"],
                        "archived": repo_data["archived"]
                    }
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_repositories(self, user: str = None, type: str = "all", sort: str = "updated") -> Dict[str, Any]:
        """List repositories for a user or authenticated user"""
        try:
            if user:
                endpoint = f"/users/{user}/repos"
            else:
                endpoint = "/user/repos"
            
            endpoint += f"?type={type}&sort={sort}&per_page=50"
            result = await self._make_request("GET", endpoint)
            
            if result["success"]:
                repositories = []
                for repo in result["data"]:
                    repositories.append({
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo["description"],
                        "url": repo["html_url"],
                        "language": repo["language"],
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "updated_at": repo["updated_at"],
                        "private": repo["private"]
                    })
                
                return {
                    "success": True,
                    "repositories": repositories,
                    "count": len(repositories)
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ISSUE OPERATIONS
    async def create_issue(self, owner: str, repo: str, title: str, body: str = "", labels: List[str] = None) -> Dict[str, Any]:
        """Create a new issue"""
        try:
            data = {
                "title": title,
                "body": body,
                "labels": labels or []
            }
            
            result = await self._make_request("POST", f"/repos/{owner}/{repo}/issues", data)
            
            if result["success"]:
                issue_data = result["data"]
                return {
                    "success": True,
                    "issue": {
                        "id": issue_data["id"],
                        "number": issue_data["number"],
                        "title": issue_data["title"],
                        "body": issue_data["body"],
                        "url": issue_data["html_url"],
                        "state": issue_data["state"],
                        "created_at": issue_data["created_at"],
                        "labels": [label["name"] for label in issue_data["labels"]]
                    }
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_issues(self, owner: str, repo: str, state: str = "open", labels: str = "") -> Dict[str, Any]:
        """List issues in a repository"""
        try:
            endpoint = f"/repos/{owner}/{repo}/issues?state={state}&per_page=50"
            if labels:
                endpoint += f"&labels={labels}"
            
            result = await self._make_request("GET", endpoint)
            
            if result["success"]:
                issues = []
                for issue in result["data"]:
                    # Skip pull requests (they appear in issues API)
                    if "pull_request" not in issue:
                        issues.append({
                            "id": issue["id"],
                            "number": issue["number"],
                            "title": issue["title"],
                            "body": issue["body"][:200] + "..." if issue["body"] and len(issue["body"]) > 200 else issue["body"],
                            "url": issue["html_url"],
                            "state": issue["state"],
                            "created_at": issue["created_at"],
                            "updated_at": issue["updated_at"],
                            "labels": [label["name"] for label in issue["labels"]],
                            "assignees": [assignee["login"] for assignee in issue["assignees"]]
                        })
                
                return {
                    "success": True,
                    "issues": issues,
                    "count": len(issues)
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    # PULL REQUEST OPERATIONS
    async def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str, body: str = "") -> Dict[str, Any]:
        """Create a new pull request"""
        try:
            data = {
                "title": title,
                "head": head,
                "base": base,
                "body": body
            }
            
            result = await self._make_request("POST", f"/repos/{owner}/{repo}/pulls", data)
            
            if result["success"]:
                pr_data = result["data"]
                return {
                    "success": True,
                    "pull_request": {
                        "id": pr_data["id"],
                        "number": pr_data["number"],
                        "title": pr_data["title"],
                        "body": pr_data["body"],
                        "url": pr_data["html_url"],
                        "state": pr_data["state"],
                        "head": pr_data["head"]["ref"],
                        "base": pr_data["base"]["ref"],
                        "created_at": pr_data["created_at"]
                    }
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_pull_requests(self, owner: str, repo: str, state: str = "open") -> Dict[str, Any]:
        """List pull requests in a repository"""
        try:
            result = await self._make_request("GET", f"/repos/{owner}/{repo}/pulls?state={state}&per_page=50")
            
            if result["success"]:
                pull_requests = []
                for pr in result["data"]:
                    pull_requests.append({
                        "id": pr["id"],
                        "number": pr["number"],
                        "title": pr["title"],
                        "body": pr["body"][:200] + "..." if pr["body"] and len(pr["body"]) > 200 else pr["body"],
                        "url": pr["html_url"],
                        "state": pr["state"],
                        "head": pr["head"]["ref"],
                        "base": pr["base"]["ref"],
                        "created_at": pr["created_at"],
                        "updated_at": pr["updated_at"],
                        "author": pr["user"]["login"]
                    })
                
                return {
                    "success": True,
                    "pull_requests": pull_requests,
                    "count": len(pull_requests)
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    # FILE OPERATIONS
    async def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> Dict[str, Any]:
        """Get file content from repository"""
        try:
            result = await self._make_request("GET", f"/repos/{owner}/{repo}/contents/{path}?ref={ref}")
            
            if result["success"]:
                file_data = result["data"]
                
                # Decode base64 content
                content = ""
                if file_data.get("content"):
                    content = base64.b64decode(file_data["content"]).decode('utf-8')
                
                return {
                    "success": True,
                    "file": {
                        "name": file_data["name"],
                        "path": file_data["path"],
                        "size": file_data["size"],
                        "sha": file_data["sha"],
                        "content": content,
                        "download_url": file_data["download_url"]
                    }
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_file(self, owner: str, repo: str, path: str, content: str, message: str, branch: str = "main") -> Dict[str, Any]:
        """Create a new file in repository"""
        try:
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            data = {
                "message": message,
                "content": encoded_content,
                "branch": branch
            }
            
            result = await self._make_request("PUT", f"/repos/{owner}/{repo}/contents/{path}", data)
            
            if result["success"]:
                return {
                    "success": True,
                    "file": {
                        "path": path,
                        "sha": result["data"]["content"]["sha"],
                        "commit_sha": result["data"]["commit"]["sha"],
                        "message": message
                    }
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    # AUTOMATION WORKFLOWS
    async def bulk_issue_creator(self, owner: str, repo: str, issues_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple issues in bulk"""
        try:
            created_issues = []
            failed_issues = []
            
            for issue_data in issues_data:
                result = await self.create_issue(
                    owner=owner,
                    repo=repo,
                    title=issue_data["title"],
                    body=issue_data.get("body", ""),
                    labels=issue_data.get("labels", [])
                )
                
                if result["success"]:
                    created_issues.append(result["issue"])
                else:
                    failed_issues.append({
                        "title": issue_data["title"],
                        "error": result["error"]
                    })
                
                # Rate limiting delay
                await asyncio.sleep(1)
            
            return {
                "success": True,
                "created_count": len(created_issues),
                "failed_count": len(failed_issues),
                "created_issues": created_issues,
                "failed_issues": failed_issues
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def repository_analyzer(self, owner: str, repo: str) -> Dict[str, Any]:
        """Comprehensive repository analysis"""
        try:
            # Get repository info
            repo_info = await self.get_repository(owner, repo)
            if not repo_info["success"]:
                return repo_info
            
            # Get issues
            issues = await self.list_issues(owner, repo)
            open_issues = issues.get("data", {}).get("count", 0) if issues["success"] else 0
            
            # Get pull requests
            prs = await self.list_pull_requests(owner, repo)
            open_prs = prs.get("data", {}).get("count", 0) if prs["success"] else 0
            
            # Get contributors
            contributors_result = await self._make_request("GET", f"/repos/{owner}/{repo}/contributors")
            contributors = len(contributors_result.get("data", [])) if contributors_result["success"] else 0
            
            # Get languages
            languages_result = await self._make_request("GET", f"/repos/{owner}/{repo}/languages")
            languages = list(languages_result.get("data", {}).keys()) if languages_result["success"] else []
            
            # Get recent commits
            commits_result = await self._make_request("GET", f"/repos/{owner}/{repo}/commits?per_page=10")
            recent_commits = len(commits_result.get("data", [])) if commits_result["success"] else 0
            
            repository = repo_info["repository"]
            
            analysis = {
                "basic_info": {
                    "name": repository["name"],
                    "description": repository["description"],
                    "stars": repository["stars"],
                    "forks": repository["forks"],
                    "watchers": repository["watchers"],
                    "size": repository["size"],
                    "language": repository["language"],
                    "created_at": repository["created_at"],
                    "updated_at": repository["updated_at"]
                },
                "activity_metrics": {
                    "open_issues": open_issues,
                    "open_pull_requests": open_prs,
                    "contributors": contributors,
                    "recent_commits": recent_commits,
                    "languages": languages
                },
                "health_score": self._calculate_health_score(repository, open_issues, open_prs, contributors),
                "recommendations": self._generate_repo_recommendations(repository, open_issues, open_prs)
            }
            
            return {
                "success": True,
                "analysis": analysis,
                "analyzed_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_health_score(self, repo: Dict, issues: int, prs: int, contributors: int) -> Dict[str, Any]:
        """Calculate repository health score"""
        score = 0
        max_score = 100
        
        # Stars influence (0-20 points)
        stars = repo["stars"]
        if stars > 1000:
            score += 20
        elif stars > 100:
            score += 15
        elif stars > 10:
            score += 10
        elif stars > 0:
            score += 5
        
        # Recent activity (0-20 points)
        updated_at = datetime.fromisoformat(repo["updated_at"].replace('Z', '+00:00'))
        days_since_update = (datetime.now(updated_at.tzinfo) - updated_at).days
        if days_since_update < 7:
            score += 20
        elif days_since_update < 30:
            score += 15
        elif days_since_update < 90:
            score += 10
        elif days_since_update < 365:
            score += 5
        
        # Issue management (0-20 points)
        if issues == 0:
            score += 20
        elif issues < 5:
            score += 15
        elif issues < 20:
            score += 10
        elif issues < 50:
            score += 5
        
        # Contributors (0-20 points)
        if contributors > 50:
            score += 20
        elif contributors > 10:
            score += 15
        elif contributors > 5:
            score += 10
        elif contributors > 1:
            score += 5
        
        # Documentation (0-20 points)
        if repo["description"]:
            score += 10
        # This would need additional API calls to check for README, etc.
        score += 10  # Assuming basic documentation exists
        
        return {
            "score": score,
            "max_score": max_score,
            "percentage": round((score / max_score) * 100, 2),
            "rating": "Excellent" if score > 80 else "Good" if score > 60 else "Fair" if score > 40 else "Poor"
        }

    def _generate_repo_recommendations(self, repo: Dict, issues: int, prs: int) -> List[str]:
        """Generate recommendations for repository improvement"""
        recommendations = []
        
        if issues > 20:
            recommendations.append("Consider addressing open issues to improve project health")
        
        if prs > 10:
            recommendations.append("Review and merge pending pull requests")
        
        if not repo["description"]:
            recommendations.append("Add a detailed description to help users understand the project")
        
        updated_at = datetime.fromisoformat(repo["updated_at"].replace('Z', '+00:00'))
        days_since_update = (datetime.now(updated_at.tzinfo) - updated_at).days
        
        if days_since_update > 90:
            recommendations.append("Project appears inactive - consider regular updates or maintenance")
        
        if repo["stars"] < 10:
            recommendations.append("Improve visibility through better documentation and community engagement")
        
        return recommendations

    # SEARCH AND DISCOVERY
    async def search_repositories(self, query: str, sort: str = "stars", order: str = "desc", per_page: int = 10) -> Dict[str, Any]:
        """Search for repositories"""
        try:
            endpoint = f"/search/repositories?q={query}&sort={sort}&order={order}&per_page={per_page}"
            result = await self._make_request("GET", endpoint)
            
            if result["success"]:
                repositories = []
                for repo in result["data"]["items"]:
                    repositories.append({
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo["description"],
                        "url": repo["html_url"],
                        "language": repo["language"],
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "score": repo["score"],
                        "owner": repo["owner"]["login"]
                    })
                
                return {
                    "success": True,
                    "repositories": repositories,
                    "total_count": result["data"]["total_count"],
                    "query": query
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    # HEALTH CHECK
    async def test_connection(self) -> Dict[str, Any]:
        """Test the GitHub API connection"""
        try:
            result = await self._make_request("GET", "/user")
            
            if result["success"]:
                user_data = result["data"]
                return {
                    "success": True,
                    "authenticated_user": user_data["login"],
                    "user_id": user_data["id"],
                    "connection_status": "active"
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}