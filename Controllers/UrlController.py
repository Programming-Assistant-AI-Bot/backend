import httpx
import re
from schemas.url import UrlInput
from services.loaders.websiteLoader import get_split_chunks_from_url
from services.loaders.gitRepoLoader import get_split_chunks_from_github
from vectordb.persistentFaiss import PersistentSessionStorage

# —— Per-session FAISS storage helper ——
storage = PersistentSessionStorage(base_directory="./session_storage")

async def validateUrl(data: UrlInput):
    url = str(data.link)  # This is already syntactically valid thanks to HttpUrl
    session_id = data.session_id


    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.head(url)
            
            # Some servers don't allow HEAD, fall back to GET
            if response.status_code == 405:
                response = await client.get(url)

        if response.status_code < 400:
            try:
                chunks = get_split_chunks_from_url(url=url)
                storage.add_documents_to_session(session_id=session_id, documents=chunks)
                
                return {
                    "message": "The URL is valid and reachable.",
                    "status_code": response.status_code,
                    "url": url
                }
            except Exception as e:
                return {
                    "message": f"URL is valid but failed to process content: {str(e)}",
                    "status_code": response.status_code,
                    "url": url
                }
        else:
            return {
                "message": " URL exists but returned an error.",
                "status_code": response.status_code,
                "url": url
            }

    except httpx.RequestError:
        return {
            "message": " The URL is syntactically valid, but not reachable.",
            "url": url
        }
    except Exception as e:
        return {
            "message": f"Unexpected error: {str(e)}",
            "url": url
        }

# Updated regex pattern to handle .git suffix and http/https
GITHUB_REPO_REGEX = r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"

async def validateGithubUrl(url: str, session_id: str, token: str = None) -> dict:
    """
    Validate a GitHub repository URL and check if it's public or private.
    
    Args:
        url (str): The GitHub repository URL (e.g., https://github.com/owner/repo)
        session_id (str): The session identifier for storing documents
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
                
                # Only process public repositories
                if is_private:
                    return {
                        "valid": False,
                        "reason": "Repository is private. Only public repositories are supported.",
                        "url": url
                    }
                
                # Repository is public, proceed with processing
                try:
                    chunks = get_split_chunks_from_github(url)
                    storage.add_documents_to_session(session_id=session_id, documents=chunks)
                    return {
                        "valid": True,
                        "reason": "Repository is public and has been processed successfully.",
                        "url": url
                    }
                except Exception as e:
                    return {
                        "valid": False,
                        "reason": f"Repository is public but failed to process content: {str(e)}",
                        "url": url,
                        "error": "content_processing_failed"
                    }
            elif response.status_code == 404:
                return {"valid": False, "reason": "Repository not found or inaccessible (private or does not exist).", "url": url}
            elif response.status_code == 403:
                return {"valid": False, "reason": "API rate limit exceeded or forbidden access.", "url": url}
            else:
                return {"valid": False, "reason": f"GitHub API returned status {response.status_code}.", "url": url}
    except httpx.RequestError as e:
        return {"valid": False, "reason": f"Connection error: {str(e)}"}
 