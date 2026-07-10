"""
GitHub 操作工具
需要 GitHub Personal Access Token
创建：Settings → Developer settings → Personal access tokens → Generate new token
权限：repo (私有仓库需勾选)
"""

import requests
from config import GITHUB_TOKEN

BASE_URL = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _github_request(method: str, endpoint: str, json_data: dict = None) -> dict:
    """统一处理 GitHub API 请求"""
    if not GITHUB_TOKEN:
        return {"error": "GitHub Token 未配置，请在 .env 中设置 GITHUB_TOKEN"}

    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            resp = requests.get(url, headers=HEADERS, timeout=15)
        elif method == "POST":
            resp = requests.post(url, headers=HEADERS, json=json_data, timeout=15)
        else:
            return {"error": f"不支持的 HTTP 方法：{method}"}

        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"GitHub API 错误：{e.response.status_code} - {e.response.text[:200]}"}
    except Exception as e:
        return {"error": f"GitHub 操作失败：{str(e)}"}


def create_issue(owner: str, repo: str, title: str, body: str = "") -> dict:
    """
    在指定仓库创建一个 Issue。

    参数:
        owner: 仓库所有者（用户名或组织名），如 "octocat"
        repo: 仓库名，如 "Hello-World"
        title: Issue 标题
        body: Issue 正文（可选，支持 Markdown）

    返回:
        {"url": "https://github.com/...", "number": 42, "title": "..."}
    """
    result = _github_request(
        "POST",
        f"/repos/{owner}/{repo}/issues",
        json_data={"title": title, "body": body}
    )
    if "error" in result:
        return result
    return {
        "url": result.get("html_url", ""),
        "number": result.get("number", 0),
        "title": result.get("title", ""),
        "state": result.get("state", "open"),
    }


def get_repo_info(owner: str, repo: str) -> dict:
    """
    查询一个仓库的基本信息。

    参数:
        owner: 仓库所有者
        repo: 仓库名

    返回:
        {"name": "Hello-World", "stars": 100, "language": "Python", ...}
    """
    result = _github_request("GET", f"/repos/{owner}/{repo}")
    if "error" in result:
        return result
    return {
        "name": result.get("full_name", ""),
        "description": result.get("description", ""),
        "stars": result.get("stargazers_count", 0),
        "forks": result.get("forks_count", 0),
        "language": result.get("language", ""),
        "open_issues": result.get("open_issues_count", 0),
        "url": result.get("html_url", ""),
    }


def list_user_repos(username: str, max_results: int = 10) -> list[dict]:
    """
    列出用户的公开仓库。

    参数:
        username: GitHub 用户名
        max_results: 最多返回几个仓库（默认 10）

    返回:
        仓库列表，每项包含 name, stars, language, url
    """
    result = _github_request(
        "GET",
        f"/users/{username}/repos?per_page={max_results}&sort=updated"
    )
    if "error" in result:
        return [result]
    if not isinstance(result, list):
        return [{"error": "意外的返回格式"}]

    return [
        {
            "name": r.get("full_name", ""),
            "description": r.get("description", ""),
            "stars": r.get("stargazers_count", 0),
            "language": r.get("language", ""),
            "url": r.get("html_url", ""),
        }
        for r in result[:max_results]
    ]


GITHUB_TOOLS = [
    {
        "name": "create_issue",
        "description": "在 GitHub 仓库中创建一个新的 Issue",
        "func": create_issue,
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "仓库所有者用户名或组织名"},
                "repo": {"type": "string", "description": "仓库名"},
                "title": {"type": "string", "description": "Issue 标题"},
                "body": {"type": "string", "description": "Issue 正文（Markdown，可选）"},
            },
            "required": ["owner", "repo", "title"]
        }
    },
    {
        "name": "get_repo_info",
        "description": "查询一个 GitHub 仓库的基本信息（星标、语言、描述等）",
        "func": get_repo_info,
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "仓库所有者用户名或组织名"},
                "repo": {"type": "string", "description": "仓库名"},
            },
            "required": ["owner", "repo"]
        }
    },
    {
        "name": "list_user_repos",
        "description": "列出某个 GitHub 用户的公开仓库",
        "func": list_user_repos,
        "parameters": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "GitHub 用户名"},
                "max_results": {"type": "integer", "description": "最多返回几个仓库，默认 10"},
            },
            "required": ["username"]
        }
    },
]
