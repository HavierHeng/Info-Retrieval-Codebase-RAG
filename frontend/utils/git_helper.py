import git 
from typing import Optional, Union, Tuple
import requests
import streamlit as st
from pathlib import Path
import shutil
import os
import platform
import tempfile

class STGitCloneProgress(git.RemoteProgress):
    """
    Updates a global streamlit status in session state for rendering.
    To use this class, pass it into Gitpython's clone_from() method. 
    Then in streamlit's session_state, download status is stored as session_state.git.clone_progress as a float from 0 to 1.0, and can be read for rendering using st.progress(). The current operation and message are stored in session_state.git.curr_op (as a human readable string) and session_state.git.message respectively.

    This is current broken due to GitPython API being borked
    """
    OP_CODES = [
        "BEGIN",
        "CHECKING_OUT",
        "COMPRESSING",
        "COUNTING",
        "END",
        "FINDING_SOURCES",
        "RECEIVING",
        "RESOLVING",
        "WRITING",
    ]
    OP_CODE_MAP = {
        getattr(git.RemoteProgress, _op_code): _op_code for _op_code in OP_CODES
    }
    
    def __init__(self):
        # Initialize progress variables
        super().__init__()
        if "git" not in st.session_state:
            st.session_state["git"] = {
                "clone_progress": 0.0,
                "curr_op": "",
                "message": ""
            }

    @classmethod
    def get_curr_op(cls, op_code: int) -> str:
        """Get OP name from OP code."""
        op_code_masked = op_code & cls.BEGIN | cls.END
        return cls.OP_CODE_MAP.get(op_code_masked, "?").title()

    def update(
        self,
        op_code: int,
        cur_count: Union[str, float],
        max_count: Optional[Union[str, float]] = None,
        message: str = ''
    ) -> None:
        """Update Streamlit's progress bar and session state during Git operations."""
        
        if op_code & self.BEGIN:
            # Starting operation, initialize progress and message
            st.session_state["git"]["clone_progress"] = 0.0
            st.session_state["git"]["curr_op"] = self.get_curr_op(op_code)
            st.session_state["git"]["message"] = message
            st.session_state["git"]["total"] = max_count
        
        if op_code & self.END:
            # Operation ended
            st.session_state["git"]["clone_progress"] = 1.0
            st.session_state["git"]["message"] = f"{message} - Completed"

        # Update progress
        if max_count:
            progress = float(cur_count) / float(max_count)
            st.session_state["git"]["clone_progress"] = progress
        
        # Update the operation message (for user feedback)
        st.session_state["git"]["message"] = message


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

def clone_repo(repo_url: str, clone_dir = "") -> Optional[os.PathLike]:
    """ 
    Attempts to clone repo given the github URL and clone directory.
    Always overrides if repo already exists at path - for reasons to keep up to date as possible.
    """
    clone_path = Path(clone_dir)

    if len(clone_dir.strip()) == 0:
        owner, repo_name = get_repo_owner_name_from_url(repo_url)

        temp_path = Path("/tmp" if platform.system() == "Darwin" else tempfile.gettempdir())

        clone_path = temp_path / Path(owner) / Path(repo_name)  # TODO: This will break on Windows, *nix assumption
        clone_path.mkdir(parents=True, exist_ok=True)

    if clone_path.exists:
        print(f"Directory {clone_path.resolve()} already exists. Overriding the existing repository.")
        shutil.rmtree(clone_path.resolve())

    if is_valid_github_repo(repo_url) and clone_path.exists:
        try:
            # Clone the repository to the specified directory
            print(f"Cloning repository from {repo_url} into {clone_path}...")
            # time.sleep(4)  # For testing
            # TODO: Progress broken due to GitPython API
            git.Repo.clone_from(url=repo_url, to_path=clone_path.resolve())
            return clone_path.resolve()
        except Exception as e:
            print(f"Error encountered while cloning repository: {e}")
            return None 
    return None 


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

def delete_downloaded_repo(repo_path : os.PathLike) -> bool:
    """
    Will try to delete local repo if it exists
    Returns true if success, false if it does not do so.
    """
    repo_dir = Path(repo_path)
    if repo_dir.exists:
        print(f"Deleting chat with existing repository at {repo_dir.resolve()}")
        shutil.rmtree(repo_dir.resolve())
        return True
    return False

def get_latest_commit_sha(repo_url: str, branch: str = "main") -> Tuple[Optional[str], Optional[str]]:
    """
    Get the latest commit SHA from the specified GitHub repository and branch.
    
    Args:
        repo_url (str): GitHub repository URL (e.g., "https://github.com/username/repo")
        branch (str): The branch to fetch the latest commit from (default is "main"). Might need to specify master if legacy
    
    Returns:
        str: The SHA of the latest commit on the specified branch. None if 'main', 'master' and branch all fails.
        str: The branch of which the commit info was successfully pulled from. None if 'main', 'master' and branch all fails.
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
        branch = "main"

    if commit_sha is None and branch != 'master': 
        # If fetching from the branch fails, try the master branch
        print(f"Trying 'master' branch after failure with '{branch}' branch.")
        commit_sha = fetch_commit("master")
        branch = "master"

    if commit_sha is None:
        print(f"'{branch}' is likely not a valid branch of the repo.")
        return None, None

    return commit_sha, branch


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

