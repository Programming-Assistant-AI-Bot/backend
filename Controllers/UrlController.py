import httpx
import re
from models.url import UrlInput

async def validateUrl(data: UrlInput):
    url = str(data.link)  # This is already syntactically valid thanks to HttpUrl

    # ✅ Step 2: Reachability check via HTTP request
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.head(url)
            
            # Some servers don't allow HEAD, fall back to GET
            if response.status_code == 405:
                response = await client.get(url)

        if response.status_code < 400:
            return {
                "message": "✅ The URL is valid and reachable.",
                "status_code": response.status_code,
                "url": url
            }
        else:
            return {
                "message": "❌ URL exists but returned an error.",
                "status_code": response.status_code,
                "url": url
            }

    except httpx.RequestError:
        return {
            "message": "❌ The URL is syntactically valid, but not reachable.",
            "url": url
        }
    
     
        
GITHUB_REPO_REGEX = r"^https:\/\/github\.com\/([\w\-\.]+)\/([\w\-\.]+)(\/)?$"

async def validateGithubUrl(url: str) -> dict:
    # 1. ✅ Syntax check with regex
    match = re.match(GITHUB_REPO_REGEX, url)
    if not match:
        return {"valid": False, "reason": "Invalid GitHub URL format."}

    owner, repo = match.group(1), match.group(2)
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    # 2. ✅ Existence check using GitHub API
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(api_url)
            if response.status_code == 200:
                return {"valid": True, "reason": "Valid public GitHub repository."}
            elif response.status_code == 404:
                return {"valid": False, "reason": "Repository not found or is private."}
            else:
                return {"valid": False, "reason": f"GitHub API returned status {response.status_code}."}
    except httpx.RequestError as e:
        return {"valid": False, "reason": f"Connection error: {str(e)}"}
    
    
        
