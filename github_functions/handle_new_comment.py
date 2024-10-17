import os
from github import GithubIntegration
from dotenv import load_dotenv
from github_functions.get_pr import get_file_content, get_pr_files
from github_functions.create_pr import create_and_merge
from code_analysis.flake8_checker import check_flake8
from ai_functions.chatbot import create_chatbot

load_dotenv()
app_id = os.getenv("APP_ID")

with open(os.path.normpath(os.path.expanduser(
        './prreviewer.2024-08-31.private-key.pem')), 'r') as cert_file:
    app_key = cert_file.read()
git_integration = GithubIntegration(app_id, app_key)

conversation_histories = {}
file_to_apply_changes = ""


def handle_new_comment(payload):
    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']
    pull_number = payload['issue']['number']
    comment_body = payload['comment']['body']
    global ai_fixed_code_list
    global ai_fixed_code

    print(f"New comment on PR #{pull_number} by {owner}/{repo_name}: "
          f"{comment_body}")
    git_connection = github.Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id).token)
    repo = git_connection.get_repo(f"{owner}/{repo_name}")

    files = get_pr_files(owner, repo_name, pull_number, os.getenv("GITHUB_TOKEN"))
    content_list = []
    for file in files:
        file_url = file['contents_url']
        file_content = get_file_content(file_url, os.getenv("GITHUB_TOKEN"))
        content_list.append(file["filename"] + "\n" + file_content)

    def get_language(filename):
        extension = os.path.splitext(filename)[1]
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.rb': 'Ruby'
        }
        return language_map.get(extension, 'Unknown')

    def run_linter(content, language):
        if language == 'Python':
            return check_flake8(content)
        else:
            return "Unsupported language"

    if comment_body.lower().startswith('@bot'):
        if pull_number not in conversation_histories:
            conversation_histories[pull_number] = []
        question = comment_body.split(' ', 1)[1]
        print(question)
        response = create_chatbot(question, content_list)
    elif comment_body.lower().startswith('@style'):
        if len(comment_body.split(' ')) > 1:
            response = ""
            if comment_body.lower().strip() == "@style approve changes":
                for file in files:
                    content = get_file_content(file['contents_url'], os.getenv("GITHUB_TOKEN"))
                    flake8_output = check_flake8(content)
                    ai_fixed_code = analyze_code_perplexity(content, flake8_output=flake8_output)
                    ai_fixed_code_list.append(ai_fixed_code)
                    print("Fixed code written to file")
                    response += f"<details>\n<summary>{file['filename']}</summary>\n\n"
                    response += "```python\n"
                    response += ai_fixed_code
                    response += "\n```\n"
                    response += "</details>\n\n"
                response += "Changes applied successfully"
                response += "\n\nTo merge these changes reply with '@style Merge Changes'"
            elif comment_body.lower().strip() == "@style merge changes":
                print(len(ai_fixed_code_list))
                if len(ai_fixed_code_list) > 0:
                    count = 0
                    for file in files:
                        print(file['filename'])
                        create_and_merge(owner, repo_name, file['filename'],
                                         ai_fixed_code_list[count])
                        print(f"Branch created and merged for {file['filename']}")
                        count += 1
                    response = "Changes merged successfully"
                else:
                    response = "No changes to merge. Please run '@style Approve Changes' first."
        else:
            ai_fixed_code_list = []
            ai_fixed_code = ""
            response = ""
            for file in files:
                content = get_file_content(file['contents_url'], os.getenv("GITHUB_TOKEN"))
                language = get_language(file['filename'])
                linter_output = run_linter(content, language)
                ai_fixed_code = analyze_code_perplexity(content, linter_output, language)
                response += f"<details>\n<summary>{file['filename']}</summary>\n\n```\n"
                response += f"{ai_fixed_code.strip()}\n```\n\n</details>\n\n"
            response += "\nTo apply these changes reply with '@style Approve Changes'"
    else:
        return "ok"

    try:
        issue = repo.get_issue(number=pull_number)
        issue.create_comment(response)
    except github.GithubException as e:
        print(f"Error creating response comment: {e}")
    return "ok"