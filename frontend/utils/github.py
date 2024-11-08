# import gitpython
import requests

def is_valid_github_repo(repo_url):
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

