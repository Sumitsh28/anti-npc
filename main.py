import os
import json
import hmac
import hashlib
from flask import Flask, request, abort
from dotenv import load_dotenv

from github_helper import (
    get_github_client, 
    get_issue_data, 
    get_repo_data, 
    get_user_data
)

from analyzer import (
    analyze_issue_and_repo, 
    analyze_user, 
    analyze_contribution_quality
)
from scoring import calculate_score
from cache_helper import user_cache  

load_dotenv()

app = Flask(__name__)

GITHUB_WEBHOOK_SECRET = os.environ.get('GITHUB_WEBHOOK_SECRET')

def verify_signature(payload_body, signature_header):
    """Verify that the payload was sent from GitHub."""
    if not signature_header:
        abort(403, 'Missing X-Hub-Signature-256 header')
    if not GITHUB_WEBHOOK_SECRET:
        abort(500, 'Webhook secret is not configured')

    hash_object = hmac.new(GITHUB_WEBHOOK_SECRET.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        abort(403, 'Signatures do not match')

@app.route("/webhook", methods=['POST'])
def github_webhook():
    """Main webhook endpoint to receive events from GitHub."""

    signature_header = request.headers.get('X-Hub-Signature-256')
    payload_body = request.data
    verify_signature(payload_body, signature_header)

    event = request.headers.get('X-GitHub-Event')
    if not event:
        abort(400, 'Missing X-GitHub-Event header')

    data = request.json

    if event == 'issue_comment' and data.get('action') == 'created':
        
        comment_body_original = data.get('comment', {}).get('body', '')
        
        if data.get('comment', {}).get('user', {}).get('type') == 'Bot':
            return "Ignoring bot comment", 200
            
        try:
            repo_full_name = data.get('repository', {}).get('full_name')
            issue_number = data.get('issue', {}).get('number')
            commenter_username = data.get('comment', {}).get('user', {}).get('login')
            installation_id = data.get('installation', {}).get('id')
            
            if not all([repo_full_name, issue_number, commenter_username, installation_id]):
                print("Incomplete data from webhook.")
                return "Incomplete data", 400

            print(f"Request detected from '{commenter_username}' on {repo_full_name}#{issue_number}")

            print("Authenticating...")
            client = get_github_client(installation_id)
            
            
            cached_data = user_cache.get(commenter_username)
            
            if cached_data:
                print(f"Cache HIT for user: {commenter_username}")
                user_data = cached_data["user_data"]
                contribution_analysis = cached_data["contribution_analysis"]
                user_data['username'] = commenter_username
            
            else:
                print(f"Cache MISS for user: {commenter_username}")
                
                print("Fetching GitHub user data (expensive)...")
                user_data = get_user_data(client, commenter_username, repo_full_name)
                user_data['username'] = commenter_username
                
                print("Analyzing contribution quality (expensive)...")
                contribution_analysis = analyze_contribution_quality(user_data.get('pr_diffs', []))
                
                user_cache[commenter_username] = {
                    "user_data": user_data,
                    "contribution_analysis": contribution_analysis
                }
          
            print("Fetching issue/repo data...")
            issue_data = get_issue_data(client, repo_full_name, issue_number)
            repo_data = get_repo_data(client, repo_full_name)
            
            if not all([issue_data, repo_data]):
                print("Failed to fetch issue/repo data.")
                return "Data fetching error", 500
            
            
            print("--- C. Running AI Analysis (Issue-Specific) ---")
            issue_tech_stack = analyze_issue_and_repo(issue_data, repo_data)
            print(f"Issue tech stack: {issue_tech_stack}")
            
            user_analysis = analyze_user(user_data, comment_body_original)
            print(f"User analysis: {user_analysis}")
            

            print("Calculating final score...")
            report = calculate_score(
                issue_tech_stack,
                user_analysis,
                user_data,
                contribution_analysis,
                repo_full_name
            )
            
            print("Posting comment to issue...")
            repo = client.get_repo(repo_full_name)
            issue = repo.get_issue(number=issue_number)
            issue.create_comment(report)

        except Exception as e:
            print(f"An error occurred in webhook handler: {e}")
            try:
                repo_full_name = data.get('repository', {}).get('full_name')
                issue_number = data.get('issue', {}).get('number')
                installation_id = data.get('installation', {}).get('id')
                if all([repo_full_name, issue_number, installation_id]):
                    client = get_github_client(installation_id)
                    repo = client.get_repo(repo_full_name)
                    issue = repo.get_issue(number=issue_number)
                    issue.create_comment(f"🤖 Oops! An internal error occurred while trying to analyze the request. {e}")
            except Exception as post_e:
                print(f"Failed to post error comment: {post_e}")
            
    return "Webhook processed", 200

if __name__ == "__main__":
    app.run(port=5001, debug=True)