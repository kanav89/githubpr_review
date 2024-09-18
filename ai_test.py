import os

from dotenv import load_dotenv
from flask import Flask, request
from github import Github
from github import GithubIntegration

from anthropic import Anthropic
from flake8_checker import check_flake8
from get_pr import get_file_content, get_pr_files

load_dotenv()

app = Flask(__name__)
app_id = os.getenv("APP_ID")

with open(os.path.normpath(os.path.expanduser('./prreviewer.2024-08-31.private-key.pem')), 'r') as cert_file:
    app_key = cert_file.read()

git_integration = GithubIntegration(app_id, app_key)

# Initialize Anthropic client
claude_client = Anthropic(api_key=os.getenv("CLAUDE_TOKEN"))


def analyze_code(code_content, flake8_output):
    prompt = (f"Analyze Python code and suggest PEP 8 improvements. "
              f"Code:\n{code_content}\n\n"
              f"Flake8 output:\n{flake8_output}")

    response = claude_client.completions.create(
        model="claude-2",
        prompt=prompt,
        max_tokens_to_sample=1500
    )
    return response.completion


@app.route("/", methods=['POST'])
def bot():
    payload = request.json

    if not (payload.get('action') == 'opened' and
            'pull_request' in payload):
        return "ok"

    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']
    pull_number = payload['pull_request']['number']

    git_connection = Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id
        ).token
    )
    repo = git_connection.get_repo(f"{owner}/{repo_name}")

    try:
        issue = repo.get_issue(number=pull_number)
    except github.GithubException as e:
        print(f"Error getting issue: {e}")
        return "Error", 500

    files = get_pr_files(owner, repo_name, pull_number,
                         os.getenv("GITHUB_TOKEN"))

    for file in files:
        if (file['status'] != 'removed' and
                file['filename'].endswith('.py')):
            content = get_file_content(file['contents_url'],
                                       os.getenv("GITHUB_TOKEN"))

            # Run Flake8
            flake8_output = check_flake8(content)

            # Use Claude API to analyze the code
            analysis_result = analyze_code(content, flake8_output)

            # Ask user if they want to process the changes
            user_input = input("Do you want to process the changes? "
                               "(yes/no): ")

            if user_input.lower() == 'yes':

                # Create a new branch
                new_branch_name = f"code-review-{pull_number}"
                try:
                    main_branch = repo.get_branch("main")
                    repo.create_git_ref(
                        ref=f"refs/heads/{new_branch_name}",
                        sha=main_branch.commit.sha)
                    print(f"Created new branch: {new_branch_name}")
                except github.GithubException as e:
                    print(f"Error creating branch: {e}")
                    return "Error creating branch", 500

                # Update file in the new branch
                try:
                    file_path = file['filename']
                    repo.update_file(
                        path=file_path,
                        message=f"Apply code review changes for PR #{pull_number}",
                        content=analysis_result.split("Changed Code:")[1].split("Comment:")[0].strip(),
                        sha=repo.get_contents(file_path, ref=new_branch_name).sha,
                        branch=new_branch_name
                    )
                    print(f"Updated file: {file_path}")
                except github.GithubException as e:
                    print(f"Error updating file: {e}")
                    return "Error updating file", 500

                # Create a pull request
                try:
                    pr = repo.create_pull(
                        title=f"Code review changes for PR #{pull_number}",
                        body=f"This PR contains the suggested changes from the code review of PR #{pull_number}",
                        head=new_branch_name,
                        base="main"
                    )
                    print(f"Created PR: {pr.html_url}")
                except github.GithubException as e:
                    print(f"Error creating PR: {e}")
                    return "Error creating PR", 500

            # Create a comment with the analysis result
            try:
                comment = issue.create_comment(analysis_result)
                print(f"Comment created: {comment.html_url}")
            except github.GithubException as e:
                print(f"Error creating comment: {e}")
                return "Error creating comment", 500

    return "ok"


if __name__ == "__main__":
    app.run(debug=True, port=5000)

