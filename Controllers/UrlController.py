# import httpx
# import re
# from models.url import UrlInput

# async def validateUrl(data: UrlInput):
#     url = str(data.link)  # This is already syntactically valid thanks to HttpUrl

#     try:
#         async with httpx.AsyncClient(timeout=5.0) as client:
#             response = await client.head(url)
            
#             # Some servers don't allow HEAD, fall back to GET
#             if response.status_code == 405:
#                 response = await client.get(url)

#         if response.status_code < 400:
#             return {
#                 "message": " The URL is valid and reachable.",
#                 "status_code": response.status_code,
#                 "url": url
#             }
#         else:
#             return {
#                 "message": " URL exists but returned an error.",
#                 "status_code": response.status_code,
#                 "url": url
#             }

#     except httpx.RequestError:
#         return {
#             "message": " The URL is syntactically valid, but not reachable.",
#             "url": url
#         }
    
     
        
# GITHUB_REPO_REGEX = r"^https:\/\/github\.com\/([\w\-\.]+)\/([\w\-\.]+)(\/)?$"

# async def validateGithubUrl(url: str) -> dict:
    
#     match = re.match(GITHUB_REPO_REGEX, url)
#     if not match:
#         return {"valid": False, "reason": "Invalid GitHub URL format."}

#     owner, repo = match.group(1), match.group(2)
#     api_url = f"https://api.github.com/repos/{owner}/{repo}"

#     try:
#         async with httpx.AsyncClient(timeout=5.0) as client:
#             response = await client.get(api_url)
#             if response.status_code == 200:
#                 return {"valid": True, "reason": "Valid public GitHub repository."}
#             elif response.status_code == 404:
#                 return {"valid": False, "reason": "Repository not found or is private."}
#             else:
#                 return {"valid": False, "reason": f"GitHub API returned status {response.status_code}."}
#     except httpx.RequestError as e:
#         return {"valid": False, "reason": f"Connection error: {str(e)}"}
    
    
    
import httpx
import re
from models.url import UrlInput

async def validateUrl(data: UrlInput):
    url = str(data.link)  # This is already syntactically valid thanks to HttpUrl
    print(url)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.head(url)
            
            # Some servers don't allow HEAD, fall back to GET
            if response.status_code == 405:
                response = await client.get(url)

        if response.status_code < 400:
            return {
                "valid": True,  # Add this
                "message": "The URL is valid and reachable.",
                "status_code": response.status_code,
                "url": url
            }
        else:
            return {
                "valid": False,  # Add this
                "message": "URL exists but returned an error.",
                "status_code": response.status_code,
                "url": url
            }
    except httpx.RequestError:
        return {
            "valid": False,  # Add this
            "message": "The URL is valid but not reachable.",
            "url": url
        }
        
        
        
        

# Updated regex pattern to handle .git suffix and http/https
GITHUB_REPO_REGEX = r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"

async def validateGithubUrl(url: str, token: str = None) -> dict:
    """
    Validate a GitHub repository URL and check if it's public or private.
    
    Args:
        url (str): The GitHub repository URL (e.g., https://github.com/owner/repo)
        token (str, optional): GitHub Personal Access Token for authenticated requests
    
    Returns:
        dict: Contains 'valid' (bool) and 'reason' (str) describing the result
    """
    # Match the URL against the regex
    match = re.match(GITHUB_REPO_REGEX, url)
    if not match:
        return {"valid": False, "reason": "Invalid GitHub URL format. Expected: https://github.com/owner/repo"}

    owner, repo = match.group(1), match.group(2)
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    # Set headers for GitHub API
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                is_private = data.get("private", False)
                return {
                    "valid": True,
                    "reason": f"Repository is {'private' if is_private else 'public'}."
                }
            elif response.status_code == 404:
                return {"valid": False, "reason": "Repository not found or inaccessible (private or does not exist)."}
            elif response.status_code == 403:
                return {"valid": False, "reason": "API rate limit exceeded or forbidden access."}
            else:
                return {"valid": False, "reason": f"GitHub API returned status {response.status_code}."}
    except httpx.RequestError as e:
        return {"valid": False, "reason": f"Connection error: {str(e)}"}
 