import os
import requests
import time
from flask import Flask, request
import github
from github import GithubIntegration
from dotenv import load_dotenv
from complexity_analyzer import analyze_complexity
from security_scanner import scan_security
import subprocess
from ai_fixer import analyze_code


import tempfile
from flake8.api import legacy as flake8
from get_pr import get_file_content, get_pr_files

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

def check_flake8(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False,encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    try:
        result = subprocess.run(['flake8', temp_file_path], capture_output=True, text=True)
        if not result.stdout:
            return ["No issues found in the code"]
        else:
            return result.stdout
    finally:
        os.unlink(temp_file_path)

def format_results(title, results):
    if not results:
        return f"### {title}\nNo issues found.\n"
    
    formatted = f"### {title}\n\n"
    for result in results:
        file_name, content = result.split('\n', 1)
        formatted += f"<details>\n<summary>{file_name}</summary>\n\n```\n{content.strip()}\n```\n\n</details>\n\n"
    return formatted


def wait_for_user_confirmation(issue, comment_id):
    for _ in range(60):  # Wait for up to 5 minute (60 * 5 seconds)
        time.sleep(5)
        comments = issue.get_comments()
        for comment in comments:
            if comment.user.login == issue.user.login and comment.body.lower().strip() == "approve ai changes":
                return True
    return False


@app.route("/", methods=['POST'])
def bot():
    payload = request.json

    if not (payload.get('action') == 'opened' and 'pull_request' in payload):
        return "ok"

    owner = payload['repository']['owner']['login']
    print(owner)
    repo_name = payload['repository']['name']
    print(repo_name)
    pull_number = payload['pull_request']['number']
    print(pull_number)

    git_connection = github.Github(
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
    
    files = get_pr_files(owner, repo_name, pull_number, os.getenv("GITHUB_TOKEN"))
    flake8_results = []
    complexity_results = []
    security_results = []
    files_with_issues = []
    for file in files:
        if file['status'] != 'removed' and file['filename'].endswith('.py'):
            content = get_file_content(file['contents_url'], os.getenv("GITHUB_TOKEN"))
            flake8_result = check_flake8(content)
            complexity_result = analyze_complexity(content)
            security_result = scan_security(content)
            
            all_issues = f"{flake8_result}\n{complexity_result}\n{security_result}"
            
            if all_issues.strip():
                files_with_issues.append((file, content, all_issues))
            
            if flake8_result.strip():
                flake8_results.append(f"File: {file['filename']}\n{flake8_result}")
            if complexity_result.strip():
                complexity_results.append(f"File: {file['filename']}\n{complexity_result}")
            if security_result.strip():
                security_results.append(f"File: {file['filename']}\n{security_result}")

    comment_body = "## PR Review Results\n\n"
    comment_body += format_results("Flake8 Analysis", flake8_results)
    comment_body += format_results("Code Complexity Analysis", complexity_results)
    comment_body += format_results("Security Scan", security_results)

    if not any([flake8_results, complexity_results, security_results]):
        comment_body += "Great job! No issues were found in this PR."
    else:
        comment_body += "Please review the issues found and make necessary changes."
    comment = issue.create_comment(comment_body)
    if files_with_issues:
        confirmation_comment = "AI will automatically change the file.\n\n"
        # for file, content, all_issues in files_with_issues:
        #     suggested_fixes = apply_fixes(content, all_issues)
        #     # print(suggest_fixes)
        #     confirmation_comment += f"**File: {file['filename']}**\n```diff\n{suggested_fixes}\n```\n\n"
        
        confirmation_comment += "Do you want to apply these AI-suggested changes? Reply with 'Approve AI changes' to proceed."
        comment = issue.create_comment(confirmation_comment)
        print(f"Comment created: {comment.html_url}")
        if wait_for_user_confirmation(issue, comment.id):
            for file, content, all_issues in files_with_issues:
                print
                fixed_content = analyze_code(content, flake8_results)
                with open('ai_test.py', 'w') as f:
                    f.write(fixed_content)

        #         # Create a new branch for the fixes
        #         new_branch = f"ai-fixes-{pull_number}-{file['filename'].replace('/', '-')}"
        #         repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=repo.get_branch("main").commit.sha)                
        #         # Commit the changes
        #         repo.update_file(
        #             path=file['filename'],
        #             message=f"AI-suggested fixes for {file['filename']}",
        #             content=fixed_content,
        #             sha=file['sha'],
        #             branch=new_branch
        #         )
                
        #         # Create a new PR with the fixes
        #         repo.create_pull(
        #             title=f"AI-suggested fixes for {file['filename']}",
        #             body="These are AI-suggested fixes. Please review carefully before merging.",
        #             head=new_branch,
        #             base=payload['pull_request']['head']['ref']
        #         )
            
        #     issue.create_comment("AI-suggested changes have been applied in separate pull requests. Please review them carefully.")
        # else:
        #     issue.create_comment("No confirmation received within 5 minutes. AI changes were not applied.")

    try:
        # comment = issue.create_comment(comment_body)
        print(f"Comment created: {comment.html_url}")
    except github.GithubException as e:
        print(f"Error creating comment: {e}")
        return "Error creating comment", 500

    return "ok"


if __name__ == "__main__":
    app.run(debug=True, port=5000)