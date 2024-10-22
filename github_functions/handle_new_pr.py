import github
import os
from github import GithubIntegration
from dotenv import load_dotenv
import base64
load_dotenv()
app_id = os.getenv("APP_ID")

github_private_key_base64 = os.environ.get('PRIVATE_KEY_BASE64')
github_private_key = base64.b64decode(github_private_key_base64).decode('utf-8')
app_key = github_private_key
git_integration = GithubIntegration(
    app_id,
    app_key, 
)
def handle_new_pr(payload):
    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']
    pull_number = payload['pull_request']['number']
    git_connection = github.Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id
        ).token
    )
    repo = git_connection.get_repo(f"{owner}/{repo_name}")
    
    
    try:
        issue = repo.get_issue(number=pull_number)
        issue.create_comment("""
        👋 Hello! I'm a bot that can assist you with this pull request.
        Here's how you can interact with me:
        
        💬 Chat with the code - @bot - Followed by the message
        🎨 Check styling issues - @style

        Feel free to use any of these commands in a comment, and I'll be happy to help!
        """)
    except github.GithubException as e:
        print(f"Error creating initial comment: {e}")
    
    return "ok"