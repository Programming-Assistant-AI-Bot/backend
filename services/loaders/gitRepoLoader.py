from langchain_community.document_loaders import GitLoader
from langchain.text_splitter import Language
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile, time, shutil, os, stat
import gc
import httpx

from enum import Enum

# Extend the Language enum to include PERL
class ExtendedLanguage(str, Enum):
    """Extended enum of languages including Perl."""
    PERL = "perl"
    # You can add other languages if needed

class PerlTextSplitter(RecursiveCharacterTextSplitter):
    @classmethod
    def from_language(cls, language, **kwargs):
        """Custom from_language method that handles Perl."""
        if language == ExtendedLanguage.PERL:
            separators = [
                # Split on subroutine definitions
                "\nsub ", 
                # Split on package declarations
                "\npackage ", "\nuse ", "\nrequire ",
                # Split on POD documentation markers
                "\n=head", "\n=over", "\n=item", "\n=back", "\n=cut",
                # Split on blocks and statements
                "{\n", "}\n", ";\n",
                # Split on control structures
                "\nif ", "\nfor ", "\nforeach ", "\nwhile ", "\nunless ", "\nuntil ",
                # Split on comments and paragraphs
                "\n#", "\n\n", 
                # Finer-grained splits
                "\n", "}", ";", " ", ""
            ]
            return cls(separators=separators, is_separator_regex=False, **kwargs)
        else:
            # Use the original implementation for other languages
            return super().from_language(language, **kwargs)

def handle_remove_readonly(func, path, exc_info):
    """Error handler for shutil.rmtree to handle readonly files."""
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

async def get_default_branch(clone_url: str) -> str:
    """
    Detect the default branch of a GitHub repository by checking the API.
    Falls back to 'main' if detection fails.
    """
    try:
        # Extract owner/repo from GitHub URL
        import re
        match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", clone_url)
        if not match:
            return "main"  # Default fallback
        
        owner, repo = match.group(1), match.group(2)
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(api_url)
            if response.status_code == 200:
                data = response.json()
                return data.get("default_branch", "main")
    except Exception as e:
        print(f"Could not detect default branch: {e}")
    
    return "main"  # Fallback

def get_split_chunks_from_github(clone_url: str, branch: str = None) -> list:
    
    temp_dir = tempfile.mkdtemp()
    print(f"Temporary directory created at: {temp_dir}")
    
    documents = []
    
    # If no branch specified, try to detect the default branch
    if branch is None:
        try:
            import asyncio
            branch = asyncio.run(get_default_branch(clone_url))
            print(f"Detected default branch: {branch}")
        except Exception as e:
            print(f"Failed to detect branch, using 'main': {e}")
            branch = "main"
    
    try:
        # Initialize GitLoader with a file_filter to pick only specified file types.
        loader = GitLoader(
            clone_url=clone_url,
            repo_path=temp_dir,
            branch=branch,
            file_filter=lambda file_path: file_path.lower().endswith((".pl", ".pm", ".t", ".pod", ".psgi", ".cgi", ".md"))
        )
        documents = loader.load()
        print(f"Loaded {len(documents)} documents from the repository.")
        
        # Release references to help cleanup the temporary directory
        loader = None
        gc.collect()

    except Exception as e:
        print(f"Error loading documents with branch '{branch}': {e}")
        
        # If the detected/specified branch fails, try the other common default branch
        if branch == "main":
            fallback_branch = "master"
        else:
            fallback_branch = "main"
        
        print(f"Trying fallback branch: {fallback_branch}")
        try:
            loader = GitLoader(
                clone_url=clone_url,
                repo_path=temp_dir,
                branch=fallback_branch,
                file_filter=lambda file_path: file_path.lower().endswith((".pl", ".pm", ".t", ".pod", ".psgi", ".cgi", ".md"))
            )
            documents = loader.load()
            print(f"Loaded {len(documents)} documents from the repository using fallback branch.")
            loader = None
            gc.collect()
        except Exception as fallback_error:
            print(f"Error loading documents with fallback branch '{fallback_branch}': {fallback_error}")
            
    finally:
        # Allow time to release file handles before deletion.
        time.sleep(2)
        try:
            shutil.rmtree(temp_dir, onerror=handle_remove_readonly)
            print("Temporary directory deleted.")
        except Exception as e:
            print(f"Warning: Could not delete temporary directory: {e}")
            print("You may need to manually delete it later.")
    
    # If there are no documents loaded, return an empty list.
    if not documents:
        return []

    # Process documents that are safely stored in memory.
    # Split Perl files using language-aware splitting.
    perl_docs = [doc for doc in documents if doc.metadata.get('source', "").lower().endswith((".pl", ".pm", ".t", ".pod", ".psgi", ".cgi"))]
    perl_splitter = PerlTextSplitter.from_language(ExtendedLanguage.PERL, chunk_size=2000, chunk_overlap=200)
    perl_chunks = perl_splitter.split_documents(perl_docs)
    print(f"Perl chunks: {len(perl_chunks)}")
    
    # Split Markdown files using generic text splitting.
    markdown_docs = [doc for doc in documents if doc.metadata.get('source', "").endswith('.md')]
    markdown_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    md_chunks = markdown_splitter.split_documents(markdown_docs)
    print(f"Markdown chunks: {len(md_chunks)}")
    
    # Combine chunks and return.
    all_chunks = perl_chunks + md_chunks
    print(f"Total chunks: {len(all_chunks)}")
    
    return all_chunks