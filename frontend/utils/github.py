import git 
from typing import Optional
import requests

def is_valid_github_repo(repo_url: str) -> bool:
    """
    Validate whether the provided URL is a valid GitHub repository.
    Checks if the repository exists by making a request to the GitHub API.
    """
    try:
        # GitHub API endpoint format: https://api.github.com/repos/{owner}/{repo}
        # For example, 'https://api.github.com/repos/username/repository'
        if repo_url.startswith("https://github.com/"):
            parts = repo_url[len("https://github.com/"):].split("/")
            if len(parts) == 2:
                owner, repo_name = parts
                api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
                response = requests.get(api_url)
                # Check if the response is a 200 (valid repo)
                return response.status_code == 200
        return False
    except requests.exceptions.RequestException:
        return False


def get_latest_commit_sha(repo_url: str, branch: str = "main") -> Optional[str]:
    """
    Get the latest commit SHA from the specified GitHub repository and branch.
    
    Args:
        repo_url (str): GitHub repository URL (e.g., "https://github.com/username/repo")
        branch (str): The branch to fetch the latest commit from (default is "main").
    
    Returns:
        str: The SHA of the latest commit on the specified branch.
    """
    # Extract the owner and repo name from the GitHub URL
    repo_parts = repo_url.strip("https://github.com/").strip("/").split("/")
    owner, repo = repo_parts[0], repo_parts[1]
    
    # GitHub API endpoint for fetching commits from a repository
    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
    
    # Send request to GitHub API
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raises exception for 4xx/5xx errors
        commit_data = response.json()  # Parse the JSON response
        
        # Extract the commit SHA from the response
        commit_sha = commit_data["sha"]
        
        return commit_sha
    except requests.exceptions.RequestException as e:
        print(f"Error fetching commit data: {e}")
        return None 


def get_latest_commit_sha_local(repo_path: str) -> Optional[str]:
    """
    Get the latest commit SHA from a local Git repository.
    
    Args:
        repo_path (str): The path to the local Git repository (directory).
    
    Returns:
        str: The SHA of the latest commit in the repository.
    """
    try:
        # Initialize the repo object from the local path
        repo = git.Repo(repo_path)
        
        # Get the latest commit from the active branch
        latest_commit = repo.head.commit  # `repo.head.commit` gives you the latest commit
        
        # Return the commit SHA
        return latest_commit.hexsha
    except git.exc.InvalidGitRepositoryError:
        print(f"The path '{repo_path}' is not a valid Git repository.")
        return None

