import git 
from typing import Optional
import requests
import time
from pathlib import Path

def get_repo_owner_name_from_url(repo_url: str) -> tuple[str, str]:
    """
    Given a repo URL link either as a HTTPS github link or a Git SSH URL, extract owner and repo name
    Returns owner and repository name
    """
    owner = ""
    repo_name = ""
    if repo_url.startswith("https://github.com/"):
        parts = repo_url[len("https://github.com/"):].split("/")
        if len(parts) == 2:
            owner, repo_name = parts

    if repo_url.startswith("git@"):
        # Remove the '.git' suffix
        repo_url = repo_url.rstrip(".git")
        # Split the remaining string by ':'
        domain_and_path = repo_url.split(":")
        # Extract the path, which contains 'username/repository'
        path = domain_and_path[1]
        # Split the path by '/' to separate the owner and repository name
        owner, repo_name = path.split("/")

    return owner, repo_name

def clone_repo(repo_url: str, clone_dir = "") -> bool:
    """ 
    Attempts to clone repo given the github URL and clone directory 
    """
    clone_path = Path(clone_dir)

    if len(clone_dir.strip()) == 0:
        owner, repo_name = get_repo_owner_name_from_url(repo_url)
        clone_path = Path(f"/tmp/{owner}/{repo_name}")  # TODO: This will break on Windows, *nix assumption
        clone_path.mkdir(parents=True, exist_ok=True)

    if is_valid_github_repo(repo_url) and clone_path.exists:
        try:
            # Clone the repository to the specified directory
            print(f"Cloning repository from {repo_url} into {clone_dir}...")
            # TODO: Still in testing - spoof with sleep for now
            # git.Repo.clone_from(repo_url, clone_dir)
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Error encountered while cloning repository: {e}")
            return False
    return False

def is_valid_github_repo(repo_url: str) -> bool:
    """
    Validate whether the provided URL is a valid GitHub repository.
    Checks if the repository exists by making a request to the GitHub API.
    """
    try:
        # GitHub API endpoint format: https://api.github.com/repos/{owner}/{repo}
        # For example, 'https://api.github.com/repos/username/repository'
        owner, repo_name = get_repo_owner_name_from_url(repo_url)
        if owner and repo_name:
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
        branch (str): The branch to fetch the latest commit from (default is "main"). Might need to specify master if legacy
    
    Returns:
        str: The SHA of the latest commit on the specified branch.
    """
    owner, repo = get_repo_owner_name_from_url(repo_url) 
    
    # GitHub API endpoint for fetching commits from a repository
    def fetch_commit(branch: str) -> Optional[str]:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
        try:
            response = requests.get(api_url)
            response.raise_for_status()  # Raises exception for 4xx/5xx errors
            commit_data = response.json()  # Parse the JSON response
            return commit_data["sha"]  # Return the commit SHA
        except requests.exceptions.RequestException as e:
            print(f"Error fetching commit data for branch '{branch}': {e}")
            return None

    commit_sha = fetch_commit(branch)
    if commit_sha is None and branch != 'main':
        # Try the main branch first
        print(f"Trying 'main' branch after failure with '{branch}' branch.")
        commit_sha = fetch_commit("main")

    if commit_sha is None and branch != 'master': 
        # If fetching from the branch fails, try the master branch
        print(f"Trying 'master' branch after failure with '{branch}' branch.")
        commit_sha = fetch_commit("master")

    return commit_sha


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
    except git.InvalidGitRepositoryError:
        print(f"The path '{repo_path}' is not a valid Git repository.")
        return None

