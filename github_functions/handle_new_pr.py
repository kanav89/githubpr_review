import github
import os
from github import GithubIntegration
from dotenv import load_dotenv

load_dotenv()
app_id = os.getenv("APP_ID")

with open(
        os.path.normpath(os.path.expanduser('./prreviewer.2024-08-31.private-key.pem')),
        'r'
) as cert_file:
    app_key = cert_file.read()
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