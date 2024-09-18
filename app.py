import os
import requests
from flask import Flask, request
import github
from github import GithubIntegration
from dotenv import load_dotenv
from get_pr import get_file_content, get_pr_files
from flake8_checker import check_flake8
from ai_fixer import analyze_code_perplexity
from create_pr import create_and_merge
import tempfile

load_dotenv()

app = Flask(__name__)
app_id = os.getenv("APP_ID")
claude_api_key = os.getenv("ANTHROPIC_API_KEY")
claude_api_url = "https://api.perplexity.ai/chat/completions"
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
with open(
        os.path.normpath(os.path.expanduser('./prreviewer.2024-08-31.private-key.pem')),
        'r'
) as cert_file:
    app_key = cert_file.read()

git_integration = GithubIntegration(
    app_id,
    app_key, 
)

def get_perplexity_response(question, pr_files, conversation_history):
    content = ""
    for i in conversation_history:
        content += i
    content += question
    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                'content': f"Context: {pr_files}\n\nQuestion: {question}"
            },
            {
                "role": "user",
                "content": content
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.2,
        
    }
    headers = {
        "Authorization": f"Bearer {perplexity_api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    # print(response.json())
    return response.json()['choices'][0]['message']['content']
    

def get_claude_response(question, pr_files, conversation_history):
    import openai
    openai.api_key = perplexity_api_key

    messages = conversation_history + [
        {'role': 'user', 'content': f"Context: {pr_files}\n\nQuestion: {question}"}
    ]

    response = openai.ChatCompletion.create(
        model="llama-3-sonar-large-32k-online",
        messages=messages,
        max_tokens=2000,
        temperature=0.1
    )

    if response.status_code == 200:
        return ''.join(block for block in response.choices[0].message.content)
    else:
        print(f"Error: {response.status_code}, {response.error}")
        return 'Sorry, I could not get an answer.'

@app.route("/", methods=['POST'])
def bot():
    payload = request.json
    if payload.get('action') == 'opened' and 'pull_request' in payload:
        return handle_new_pr(payload)
        
    elif payload.get('action') == 'created' and 'comment' in payload and 'issue' in payload and 'pull_request' in payload['issue']:
        return handle_new_comment(payload)
    
    return "ok"

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
    files = get_pr_files(owner, repo_name, pull_number, os.getenv("GITHUB_TOKEN"))
    # content_list = [get_file_content(file['contents_url'], os.getenv("GITHUB_TOKEN")) for file in files]
    
    try:
        issue = repo.get_issue(number=pull_number)
        issue.create_comment("""
        👋 Hello! I'm a bot that can assist you with this pull request.

        Here's how you can interact with me:
        
        💬 Chat with the code - @bot - Followed by the message
        🎨 Check styling issues - @style
        🔒 Check security issues - @security
        🧠 Check complexity issues - @complexity

        Feel free to use any of these commands in a comment, and I'll be happy to help!
        """)
    except github.GithubException as e:
        print(f"Error creating initial comment: {e}")
    
    return "ok"

conversation_histories = {}
file_to_apply_changes = ""

def handle_new_comment(payload):
    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']
    pull_number = payload['issue']['number']
    comment_body = payload['comment']['body']
    ai_fixed_code = ""

    print(f"New comment on PR #{pull_number} by {owner}/{repo_name}: {comment_body}")

    git_connection = github.Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id
        ).token
    )
    repo = git_connection.get_repo(f"{owner}/{repo_name}")
    
    files = get_pr_files(owner, repo_name, pull_number, os.getenv("GITHUB_TOKEN"))
    content_list = [get_file_content(file['contents_url'], os.getenv("GITHUB_TOKEN")) for file in files]


    # Get the conversation history for this pull request
    
    if comment_body.lower().startswith('@bot'):
        if pull_number not in conversation_histories:
            conversation_histories[pull_number] = []
        question = comment_body.split(' ', 1)[1]
        conversation_history = conversation_histories[pull_number]
        response = get_perplexity_response(question, content_list, conversation_history)

        # Update the conversation history only if it's not an error message
        if not response.startswith("An error occurred") and not response.startswith("Sorry, I couldn't generate"):
            conversation_histories[pull_number].append({'role': 'user', 'content': question})
            conversation_histories[pull_number].append({'role': 'assistant', 'content': response})

    elif comment_body.lower().startswith('@style'):
        if len(comment_body.split(' '))>1:
            # approve = comment_body.split(' ', 1)[1]
            response = ""
            if comment_body.lower().strip() == "@style approve changes":
                for file in files:
                    content = get_file_content(file['contents_url'], os.getenv("GITHUB_TOKEN"))
                    flake8_output = check_flake8(content)
                    ai_fixed_code = analyze_code_perplexity(content,flake8_output=flake8_output)
                    
                    
                    with open('app_fixed.py', 'w',encoding='utf-8') as f:
                        f.write(ai_fixed_code)
                    # with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as temp_file:
                    #     temp_file.write(ai_fixed_code)
                        # fixed_files.append((file['filename'], temp_file.name))
                    print("Fixed code written to file")
                    response = f"```python\n{ai_fixed_code}\n```"
                    response += "Changes applied successfully"
                    response += "\n\nTo merge these changes reply with '@style Merge Changes'"
            elif comment_body.lower().strip() == "@style merge changes":
                for file in files:
                    print(file['filename'])
                    create_and_merge(owner,repo_name,"bot-code.py",ai_fixed_code)
                    print("branch created")
                    response = "Changes merged successfully"
            # elif flake8_output==None:
            #     response = "Run @style first to apply the changes"
        else:   
            for file in files:
                print(file['filename'])
                content = get_file_content(file['contents_url'], os.getenv("GITHUB_TOKEN"))
                flake8_output = check_flake8(content)
                response = f"<details>\n<summary>{file['filename']}</summary>\n\n```\n{flake8_output.strip()}\n```\n\n</details>\n\n"
            
                response += "\nTo apply these changes reply with '@style Approve Changes'"

    else:
        return "ok"
    
    
    try:
        issue = repo.get_issue(number=pull_number)
        issue.create_comment(response)
    except github.GithubException as e:
        print(f"Error creating response comment: {e}")

    return "ok"

if __name__ == "__main__":
    app.run(debug=True, port=5000)