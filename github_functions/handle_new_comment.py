import github
import os
from github import GithubIntegration
from dotenv import load_dotenv
from github_functions.get_pr import get_file_content, get_pr_files
from github_functions.create_pr import create_and_merge
from ai_functions.ai_fixer import  analyze_code_anthropic
from code_analysis.code_checker import check_flake8
from ai_functions.chatbot import create_chatbot
import base64
import json

load_dotenv()



app_id = os.getenv("APP_ID")


github_private_key_base64 = os.environ.get('PRIVATE_KEY_BASE64')
github_private_key = base64.b64decode(github_private_key_base64).decode('utf-8')
app_key = github_private_key
git_integration = GithubIntegration(
    app_id,
    app_key, 
)


conversation_histories = {}
ai_fixed_code_list = []
file_to_apply_changes = ""
def handle_new_comment(payload):
    global ai_fixed_code_list
    
    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']
    pull_number = payload['issue']['number']
    comment_body = payload['comment']['body']
    
    print(f"New comment on PR #{pull_number} by {owner}/{repo_name}: {comment_body}")
    git_connection = github.Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id
        ).token
    )
    repo = git_connection.get_repo(f"{owner}/{repo_name}")
    
    files = get_pr_files(owner, repo_name, pull_number, os.getenv("GITHUB_TOKEN"))
    content_list = []
    for file in files:
        file_url = file['contents_url']
        file_content = get_file_content(file_url, os.getenv("GITHUB_TOKEN"))
        content_list.append(file["filename"] + "\n" + file_content)
    # Get the conversation history for this pull request
    def get_language(filename):
        extension = os.path.splitext(filename)[1]
        language_map = {
            '.py': 'Python',
            
            
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
        
        if len(comment_body.strip().split(' ')) > 1:
            response = ""
            if comment_body.lower().strip() == "@style approve changes":
                ai_fixed_code_list = []  # Local variable
                for file in files:
                    content = get_file_content(file['contents_url'], os.getenv("GITHUB_TOKEN"))
                    language = get_language(file['filename'])
                    print(language)
                    if language == "Unknown":
                        response += f"Skipping {file['filename']} as it is an unsupported language\n"
                        continue
                    linter_output = run_linter(content, language)
                    ai_fixed_code = analyze_code_anthropic(content, linter_output, language)
                    ai_fixed_code_list.append(ai_fixed_code)
                    
                    print("Fixed code written to file")
                    response += f"<details>\n<summary>{file['filename']}</summary>\n\n"
                    if language == 'Python':
                        response += "```python\n"
                    elif language in ['JavaScript', 'TypeScript']:
                        response += "```javascript\n"
                    elif language == 'Java':
                        response += "```java\n"
                    response += ai_fixed_code
                    response += "\n```\n"
                    response += "</details>\n\n"                    
                # Write ai_fixed_code_list to a file
                file_path = f"ai_fixed_code_{owner}_{repo_name}_{pull_number}.json"
                with open(file_path, 'w') as f:
                    json.dump(ai_fixed_code_list, f)
                
                response += "\n\nChanges have been saved. To merge these changes, reply with '@style Merge Changes'"
            elif comment_body.lower().strip() == "@style merge changes":
                # Read ai_fixed_code_list from the file
                file_path = f"ai_fixed_code_{owner}_{repo_name}_{pull_number}.json"
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        ai_fixed_code_list = json.load(f)
                    
                    print(f"Number of files to merge: {len(ai_fixed_code_list)}")
                    if len(ai_fixed_code_list) > 0:
                        count = 0
                        for file in files:
                            print(f"Processing file: {file['filename']}")
                            language = get_language(file['filename'])
                            print(f"Language: {language}")
                            if language == "Unknown":
                                response += f"Skipping {file['filename']} as it is an unsupported language\n"
                                continue
                            if count < len(ai_fixed_code_list):
                                create_and_merge(owner, repo_name, file['filename'], ai_fixed_code_list[count])
                                print(f"Branch created and merged for {file['filename']}")
                                count += 1
                            else:
                                print(f"No changes to apply for {file['filename']}")
                        # Delete the file after successful merge
                        os.remove(file_path)
                        response = "Changes merged successfully"
                    else:
                        response = "No changes to merge. Please run '@style Approve Changes' first."
                else:
                    response = "No approved changes found. Please run '@style Approve Changes' first."
        else:   
            print("Checking for styling issues")
            ai_fixed_code_list = []
            ai_fixed_code = ""
            response = ""
            # print(response)
            for file in files:
                content = get_file_content(file['contents_url'], os.getenv("GITHUB_TOKEN"))
                language = get_language(file['filename'])
                print(language)
                if language == "Unknown":
                    response += f"Skipping {file['filename']} as it is an unsupported language\n"
                    continue
                linter_output = run_linter(content, language)
            
                response += f"<details>\n<summary>{file['filename']}</summary>\n\n```\n{linter_output.strip()}\n```\n\n</details>\n\n"
            
            response += "\nTo apply these changes reply with '@style Approve Changes'"
            print("finished checking for styling issues")
    else:
        print("No comment")
        return "ok"
    
    
    try:
        issue = repo.get_issue(number=pull_number)
        issue.create_comment(response)
    except github.GithubException as e:
        print(f"Error creating response comment: {e}")
    return "ok"
