import os
import time
import jwt
import requests
from github import Github, Auth


def get_github_app_jwt():
    """
    Generates a JSON Web Token (JWT) for authenticating as the GitHub App.
    This JWT is short-lived (10 minutes) and used to get installation tokens.
    """
    app_id = os.environ.get('GITHUB_APP_ID')
    
    private_key_path = os.environ.get('GITHUB_PRIVATE_KEY_PATH')
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(f"Private key file not found at: {private_key_path}")
        
    with open(private_key_path, 'r') as f:
        private_key = f.read()

    payload = {
        'iat': int(time.time()), 
        'exp': int(time.time()) + (10 * 60), 
        'iss': app_id 
    }

    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token

def get_installation_access_token(installation_id):
    """
    Uses the App's JWT to get a temporary access token for a specific installation.
    """
    app_jwt = get_github_app_jwt()
    
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()  
        
        token_data = response.json()
        return token_data['token']
        
    except requests.exceptions.RequestException as e:
        print(f"Error getting installation access token: {e}")
        print(f"Response body: {e.response.text}")
        return None

def get_github_client(installation_id):
    """
    Returns an authenticated PyGithub client for a specific installation.
    """
    if not installation_id:
        raise ValueError("Installation ID is required")
        
    access_token = get_installation_access_token(installation_id)
    if not access_token:
        raise Exception("Failed to get installation access token")

    auth = Auth.Token(access_token)
    
    return Github(auth=auth)


def get_issue_data(client, repo_full_name, issue_number):
    """Fetches the issue title, body, and labels."""
    try:
        repo = client.get_repo(repo_full_name)
        issue = repo.get_issue(number=issue_number)
        
        # --- NEW: Get label names ---
        labels = [label.name for label in issue.labels]
        
        return {
            "title": issue.title,
            "body": issue.body or "",
            "labels": labels  
        }
    except Exception as e:
        print(f"Error fetching issue data: {e}")
        return None

def get_repo_data(client, repo_full_name):
    """Fetches the repo's main language and README."""
    try:
        repo = client.get_repo(repo_full_name)
        
        try:
            readme = repo.get_readme()
            readme_content = readme.decoded_content.decode('utf-8')
        except Exception:
            readme_content = "README not found."
            
        return {
            "language": repo.language,
            "readme": readme_content
        }
    except Exception as e:
        print(f"Error fetching repo data: {e}")
        return None

def get_user_data(client, username, repo_full_name):
    """
    Fetches user's profile info, activity, and
    the code diffs of their last 3 merged PRs in the target repo.
    """
    try:
        user = client.get_user(username)
        
        bio = user.bio or ""
        
        events = user.get_public_events()
        pr_details = []
        
        for event in events[:30]:
            if event.type == 'PullRequestEvent':
                pr = event.payload.get('pull_request', {})
                pr_title = pr.get('title')
                pr_repo = event.repo.name
                if pr_title:
                    pr_details.append(f"PR to {pr_repo}: {pr_title}")
        
        repo_contribution_count = 0
        
        pr_diffs = []
        try:
            query = f"is:pr is:merged author:{username} repo:{repo_full_name}"
            search_results = client.search_issues(query, sort='created', order='desc')
            
            repo_contribution_count = search_results.totalCount
            print(f"Found {repo_contribution_count} merged PRs for {username} in {repo_full_name}")
            
            token = client.auth.token
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3.diff", 
            }
            
            for issue in search_results[:3]:
                pr = issue.as_pull_request()
                diff_url = pr.diff_url
                
                diff_response = requests.get(diff_url, headers=headers)
                diff_response.raise_for_status()
                
                pr_diffs.append(diff_response.text[:4000])

        except Exception as e:
            print(f"Error searching or fetching PR diffs: {e}")

            
        repo_languages = set()
        try:
            print("Fetching user's owned repo languages...")
            owned_repos = user.get_repos(type='owner', sort='updated')
            for repo in owned_repos[:10]:
                if repo.language:
                    repo_languages.add(repo.language)
        except Exception as e:
            print(f"Could not fetch user's repo languages: {e}")
            pass

        return {
            "bio": bio,
            "recent_prs": "\n".join(pr_details),
            "repo_contribution_count": repo_contribution_count,
            "repo_languages": list(repo_languages),
            "pr_diffs": pr_diffs
        }
    except Exception as e:
        print(f"Error fetching user data for {username}: {e}")
        return None