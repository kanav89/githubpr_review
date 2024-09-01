import os
import requests

from flask import Flask, request
import github
from github import Github, GithubIntegration
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# MAKE SURE TO CHANGE TO YOUR APP NUMBER!!!!!
app_id = os.getenv("APP_ID")
# Read the bot certificate
with open(
        os.path.normpath(os.path.expanduser('./prreviewer.2024-08-31.private-key.pem')),
        'r'
) as cert_file:
    app_key = cert_file.read()

# Create an GitHub integration instance
git_integration = GithubIntegration(
    app_id,
    app_key,
)


@app.route("/", methods=['POST'])
def bot():
    # Get the event payload
    payload = request.json
    

    print(f"Received payload for PR #{payload['pull_request']['number']}")
    # Check if the event is a GitHub PR creation event
    if not (payload.get('action') == 'opened' and 'pull_request' in payload):
        print(f"Ignoring event: {payload.get('action', 'unknown')} - not a new PR")
        return "ok"
    print(payload['repository']['owner'])
    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']



    # Get a git connection as our bot
    # Here is where we are getting the permission to talk as our bot and not
    # as a Python webservice
    git_connection = Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id
        ).token
    )
    repo = git_connection.get_repo(f"{owner}/{repo_name}")

    try:
        issue = repo.get_issue(number=payload['pull_request']['number'])
    except github.GithubException as e:
        print(f"Error getting issue: {e}")
        return "Error", 500

    # Call meme-api to get a random meme
    try:
        response = requests.get(url='https://meme-api.herokuapp.com/gimme', timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching meme: {e}")
        return "Error fetching meme", 500

    # Get the best resolution meme
    try:
        meme_url = response.json()['preview'][-1]
    except (KeyError, IndexError) as e:
        print(f"Error parsing meme response: {e}")
        print(f"Response content: {response.text}")
        return "Error parsing meme response", 500

    # Create a comment with the random meme
    try:
        comment = issue.create_comment(f"![Meme]({meme_url})")
        print(f"Comment created: {comment.html_url}")
    except github.GithubException as e:
        print(f"Error creating comment: {e}")
        return "Error creating comment", 500

    return "ok"


if __name__ == "__main__":
    app.run(debug=True, port=5000)