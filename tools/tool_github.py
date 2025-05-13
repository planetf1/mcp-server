import os
import base64
import httpx
from typing import Optional, Dict, List, Any, Union
from mcp_instance import mcp
from datetime import datetime, timedelta, UTC


class GitHubToolError(Exception):
    """Exception raised for GitHub tool errors."""

    pass


@mcp.tool()
async def github_get_file(repo: str, path: str, ref: str = "main") -> Dict[str, str]:
    """
    Retrieve a file from a GitHub repository.

    Args:
        repo: Repository name in format 'owner/repo'
        path: Path to the file within the repository
        ref: Branch, tag, or commit SHA (defaults to 'main')

    Returns:
        Dictionary containing the file content and metadata
    """
    api_key = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not api_key:
        raise GitHubToolError("GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set")

    url = f"https://api.github.com/repos/{repo}/contents/{path}"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params={"ref": ref},
            headers={
                "Authorization": f"token {api_key}",
                "Accept": "application/vnd.github.v3+json",
            },
        )

        if response.status_code == 404:
            return {"error": f"File not found: {path} in {repo} at {ref}"}
        elif response.status_code != 200:
            raise GitHubToolError(f"GitHub API error: {response.status_code} - {response.text}")

        data = await response.json()

        if data.get("type") != "file":
            return {"error": f"Path does not point to a file: {path}"}

        content = base64.b64decode(data["content"]).decode("utf-8")
        return {
            "content": content,
            "name": data["name"],
            "path": data["path"],
            "sha": data["sha"],
            "size": data["size"],
            "url": data["html_url"],
        }


@mcp.tool()
async def github_list_issues(
    repo: str, state: str = "open", labels: str = ""
) -> List[Dict[str, Any]]:
    """
    List issues in a GitHub repository.

    Args:
        repo: Repository name in format 'owner/repo'
        state: Issue state ('open', 'closed', 'all')
        labels: Comma-separated list of label names

    Returns:
        List of issues
    """
    api_key = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not api_key:
        raise GitHubToolError("GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set")

    url = f"https://api.github.com/repos/{repo}/issues"

    params = {"state": state}
    if labels:
        params["labels"] = labels

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            headers={
                "Authorization": f"token {api_key}",
                "Accept": "application/vnd.github.v3+json",
            },
        )

        if response.status_code != 200:
            raise GitHubToolError(f"GitHub API error: {response.status_code} - {response.text}")

        issues = await response.json()

        # Filter out pull requests (GitHub API returns PRs as issues)
        return [
            {
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "html_url": issue["html_url"],
                "user": issue["user"]["login"],
                "labels": [label["name"] for label in issue["labels"]],
                "body": issue.get("body", ""),
            }
            for issue in issues
            if "pull_request" not in issue
        ]


@mcp.tool()
async def github_create_issue(
    repo: str, title: str, body: str, labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a new issue in a GitHub repository.

    Args:
        repo: Repository name in format 'owner/repo'
        title: Issue title
        body: Issue body text
        labels: List of label names to apply

    Returns:
        Created issue information
    """
    api_key = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not api_key:
        raise GitHubToolError("GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set")

    url = f"https://api.github.com/repos/{repo}/issues"

    data = {"title": title, "body": body}

    if labels:
        data["labels"] = labels

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=data,
            headers={
                "Authorization": f"token {api_key}",
                "Accept": "application/vnd.github.v3+json",
            },
        )

        if response.status_code != 201:
            raise GitHubToolError(f"GitHub API error: {response.status_code} - {response.text}")

        issue = await response.json()
        return {
            "number": issue["number"],
            "title": issue["title"],
            "html_url": issue["html_url"],
            "state": issue["state"],
            "created_at": issue["created_at"],
        }


@mcp.tool()
async def github_list_pull_requests(repo: str, state: str = "open") -> List[Dict[str, Any]]:
    """
    List pull requests in a GitHub repository.

    Args:
        repo: Repository name in format 'owner/repo'
        state: PR state ('open', 'closed', 'all')

    Returns:
        List of pull requests
    """
    api_key = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not api_key:
        raise GitHubToolError("GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set")

    url = f"https://api.github.com/repos/{repo}/pulls"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params={"state": state},
            headers={
                "Authorization": f"token {api_key}",
                "Accept": "application/vnd.github.v3+json",
            },
        )

        if response.status_code != 200:
            raise GitHubToolError(f"GitHub API error: {response.status_code} - {response.text}")

        prs = await response.json()
        return [
            {
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
                "html_url": pr["html_url"],
                "user": pr["user"]["login"],
                "head": pr["head"]["ref"],
                "base": pr["base"]["ref"],
            }
            for pr in prs
        ]


@mcp.tool()
async def github_search_code(query: str, repo: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for code on GitHub.

    Args:
        query: Search query
        repo: Optional repository name in format 'owner/repo' to limit search

    Returns:
        Search results
    """
    api_key = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not api_key:
        raise GitHubToolError("GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set")

    if repo:
        query = f"{query} repo:{repo}"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/search/code",
            params={"q": query},
            headers={
                "Authorization": f"token {api_key}",
                "Accept": "application/vnd.github.v3+json",
            },
        )

        if response.status_code != 200:
            raise GitHubToolError(f"GitHub API error: {response.status_code} - {response.text}")

        # Need to await the JSON response
        results = await response.json()
        return {
            "total_count": results["total_count"],
            "items": [
                {
                    "repository": item["repository"]["full_name"],
                    "path": item["path"],
                    "name": item["name"],
                    "url": item["html_url"],
                }
                for item in results.get("items", [])[:10]  # Limit to 10 results
            ],
        }


@mcp.tool()
async def github_user_activity(username: str, days: int = 7, token: str = None) -> dict:
    """
    Summarize a GitHub user's activity over a specified time period

    Args:
        username: GitHub username to analyze
        days: Number of days to look back (default: 7)
        token: GitHub Personal Access Token (optional but recommended to avoid rate limits)

    Returns:
        Summary of user's GitHub activity including issues, PRs, and comments
    """
    # Calculate the date range
    # Use datetime.now(UTC) instead of utcnow() which is deprecated
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days)
    since = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    async with httpx.AsyncClient() as client:
        # Fetch user info to confirm user exists
        user_response = await client.get(
            f"https://api.github.com/users/{username}", headers=headers
        )

        if user_response.status_code != 200:
            return {
                "error": f"GitHub API error: User not found or API limit reached ({user_response.status_code})"
            }

        # Initialize result containers
        issues_opened = []
        issues_commented = []
        prs_opened = []
        prs_merged = []
        pr_reviews = []

        # Get issues created by the user
        issues_response = await client.get(
            f"https://api.github.com/search/issues",
            headers=headers,
            params={
                "q": f"author:{username} type:issue created:>={since}",
                "sort": "updated",
                "order": "desc",
            },
        )

        if issues_response.status_code == 200:
            # Await the JSON method
            issues_data = await issues_response.json()
            for issue in issues_data.get("items", []):
                issues_opened.append(
                    {
                        "title": issue.get("title"),
                        "url": issue.get("html_url"),
                        "created_at": issue.get("created_at"),
                        "repo": (
                            issue.get("repository_url").split("/repos/")[1]
                            if "repository_url" in issue
                            else "unknown"
                        ),
                    }
                )

        # Get PRs created by the user
        prs_response = await client.get(
            f"https://api.github.com/search/issues",
            headers=headers,
            params={
                "q": f"author:{username} type:pr created:>={since}",
                "sort": "updated",
                "order": "desc",
            },
        )

        if prs_response.status_code == 200:
            # Await the JSON method
            prs_data = await prs_response.json()
            for pr in prs_data.get("items", []):
                pr_info = {
                    "title": pr.get("title"),
                    "url": pr.get("html_url"),
                    "created_at": pr.get("created_at"),
                    "repo": (
                        pr.get("repository_url").split("/repos/")[1]
                        if "repository_url" in pr
                        else "unknown"
                    ),
                    "state": pr.get("state"),
                }
                prs_opened.append(pr_info)

                # Check if PR was merged (requires additional API call)
                if pr.get("pull_request", {}).get("url"):
                    pr_detail_response = await client.get(
                        pr.get("pull_request").get("url"), headers=headers
                    )
                    if pr_detail_response.status_code == 200:
                        pr_detail = await pr_detail_response.json()
                        if pr_detail.get("merged"):
                            prs_merged.append(pr_info)

        # Get issues/PRs commented on by the user
        comments_response = await client.get(
            f"https://api.github.com/search/issues",
            headers=headers,
            params={
                "q": f"commenter:{username} updated:>={since}",
                "sort": "updated",
                "order": "desc",
            },
        )

        if comments_response.status_code == 200:
            # Await the JSON method
            comments_data = await comments_response.json()
            for item in comments_data.get("items", []):
                comment_info = {
                    "title": item.get("title"),
                    "url": item.get("html_url"),
                    "updated_at": item.get("updated_at"),
                    "repo": (
                        item.get("repository_url").split("/repos/")[1]
                        if "repository_url" in item
                        else "unknown"
                    ),
                }
                if "pull_request" in item:
                    # This is a PR the user commented on
                    pass  # We'll count these separately in PR reviews if they're formal reviews
                else:
                    # This is an issue the user commented on
                    issues_commented.append(comment_info)

        # Get PR reviews done by the user
        # This is complex as we'd need to query each repo the user has contributed to
        # For demonstration, we'll use a simplified approach that shows the concept
        reviews_response = await client.get(
            f"https://api.github.com/search/issues",
            headers=headers,
            params={
                "q": f"reviewed-by:{username} updated:>={since}",
                "sort": "updated",
                "order": "desc",
            },
        )

        if reviews_response.status_code == 200:
            # Await the JSON method
            reviews_data = await reviews_response.json()
            for review in reviews_data.get("items", []):
                pr_reviews.append(
                    {
                        "title": review.get("title"),
                        "url": review.get("html_url"),
                        "updated_at": review.get("updated_at"),
                        "repo": (
                            review.get("repository_url").split("/repos/")[1]
                            if "repository_url" in review
                            else "unknown"
                        ),
                    }
                )

        # Create summary
        return {
            "username": username,
            "period": f"Last {days} days ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})",
            "summary": {
                "issues_opened_count": len(issues_opened),
                "issues_commented_count": len(issues_commented),
                "prs_opened_count": len(prs_opened),
                "prs_merged_count": len(prs_merged),
                "pr_reviews_count": len(pr_reviews),
            },
            "issues_opened": issues_opened,
            "issues_commented": issues_commented,
            "prs_opened": prs_opened,
            "prs_merged": prs_merged,
            "pr_reviews": pr_reviews,
        }
