import requests
import base64

import os
from dotenv import load_dotenv

def load_github_token():
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not set in environment variables")
    return token

def create_headers(token):
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

def check_repository_access(base_url, headers):
    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error accessing repository: {response.status_code}\n{response.json()}")
    return response.json()

def get_default_branch_sha(base_url, default_branch, headers):
    branch_url = f'{base_url}/git/ref/heads/{default_branch}'
    response = requests.get(branch_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error getting base branch: {response.status_code}\n{response.json()}")
    return response.json()['object']['sha']

def check_branch_exists(base_url, branch_name, headers):
    branch_url = f'{base_url}/git/ref/heads/{branch_name}'
    response = requests.get(branch_url, headers=headers)
    return response.status_code == 200

def get_or_create_branch(base_url, new_branch_name, base_sha, headers):
    if check_branch_exists(base_url, new_branch_name, headers):
        print(f"Branch '{new_branch_name}' already exists. Using existing branch.")
        return {"ref": f"refs/heads/{new_branch_name}"}
    else:
        return create_new_branch(base_url, new_branch_name, base_sha, headers)

def create_new_branch(base_url, new_branch_name, base_sha, headers):
    create_branch_url = f'{base_url}/git/refs'
    data = {
        "ref": f"refs/heads/{new_branch_name}",
        "sha": base_sha
    }
    response = requests.post(create_branch_url, json=data, headers=headers)
    if response.status_code != 201:
        raise Exception(f"Error creating branch: {response.status_code}\n{response.json()}")
    return response.json()

def create_pull_request(base_url, new_branch_name, default_branch, headers, title, body):
    pr_url = f'{base_url}/pulls'
    data = {
        "title": title,
        "body": body,
        "head": new_branch_name,
        "base": default_branch
    }
    response = requests.post(pr_url, json=data, headers=headers)
    if response.status_code != 201:
        raise Exception(f"Error creating pull request: {response.status_code}\n{response.json()}")
    return response.json()

def get_file_sha(base_url, branch_name, file_path, headers):
    get_file_url = f'{base_url}/contents/{file_path}?ref={branch_name}'
    response = requests.get(get_file_url, headers=headers)
    if response.status_code == 200:
        return response.json()['sha']
    elif response.status_code == 404:
        return None
    else:
        raise Exception(f"Error getting file SHA: {response.status_code}\n{response.json()}")

def create_file_on_branch(base_url, branch_name, file_path, file_content, commit_message, headers):
    create_file_url = f'{base_url}/contents/{file_path}'
    print("create_file_url", create_file_url)
    print(f"File content before encoding: {file_content}")
    
    # Check if file already exists
    existing_file_sha = get_file_sha(base_url, branch_name, file_path, headers)
    
    data = {
        "message": commit_message,
        "content": base64.b64encode(file_content.encode()).decode(),
        "branch": branch_name
    }
    
    if existing_file_sha:
        print("file exists")
        data["sha"] = existing_file_sha
    
    response = requests.put(create_file_url, json=data, headers=headers)
    if response.status_code not in [200, 201]:
        raise Exception(f"Error creating/updating file: {response.status_code}\n{response.json()}")
    return response.json()

def create_and_merge(owner, repo, file_path, file_content):
    print("here")
    token = load_github_token()
    headers = create_headers(token)
    new_branch_name = 'bot-branch'
    try:
        base_url = f'https://api.github.com/repos/{owner}/{repo}'

        repo_info = check_repository_access(base_url, headers)
        default_branch = repo_info['default_branch']
        print(f"Default branch: {default_branch}")

        base_sha = get_default_branch_sha(base_url, default_branch, headers)

        branch = get_or_create_branch(base_url, new_branch_name, base_sha, headers)
        print(f"Using branch: {branch['ref']}")
        print("file content", file_content)

        # Create or update file on the branch
        commit_message = 'Add or update feature file'
        try:
            updated_file = create_file_on_branch(base_url, new_branch_name, file_path, file_content, commit_message, headers)
            print(f"File created/updated: {updated_file['content']['path']}")
        except Exception as e:
            print(f"Error creating/updating file: {str(e)}")
            raise e

        pr_title = "New feature implementation"
        pr_body = "This pull request adds or updates a feature in our project."
        try:
            new_pr = create_pull_request(base_url, new_branch_name, default_branch, headers, pr_title, pr_body)
            print(f"New pull request created: {new_pr['html_url']}")
        except Exception as e:
            if "A pull request already exists" in str(e):
                print("A pull request for this branch already exists. Skipping PR creation.")
            else:
                raise e

    except Exception as e:
        print(f"An error occurred: {str(e)}")

# def main():
#     try:
#         token = load_github_token()
#         headers = create_headers(token)

#         owner = 'kanav89'
#         repo = 'githubpr_review'
#         new_branch_name = 'new-feature-branch'

#         base_url = f'https://api.github.com/repos/{owner}/{repo}'

#         repo_info = check_repository_access(base_url, headers)
#         default_branch = repo_info['default_branch']
#         print(f"Default branch: {default_branch}")

#         base_sha = get_default_branch_sha(base_url, default_branch, headers)

#         branch = get_or_create_branch(base_url, new_branch_name, base_sha, headers)
#         print(f"Using branch: {branch['ref']}")

#         # Create a new file on the branch
#         file_path = 'new_feature.txt'
#         file_content = 'This is a new feature.'
#         commit_message = 'Add new feature file'
#         try:
#             new_file = create_file_on_branch(base_url, new_branch_name, file_path, file_content, commit_message, headers)
#             print(f"New file created: {new_file['content']['path']}")
#         except Exception as e:
#             if "sha" in str(e):
#                 print(f"File '{file_path}' already exists. Skipping file creation.")
#             else:
#                 raise e

#         pr_title = "New feature implementation"
#         pr_body = "This pull request adds a new feature to our project."
#         try:
#             new_pr = create_pull_request(base_url, new_branch_name, default_branch, headers, pr_title, pr_body)
#             print(f"New pull request created: {new_pr['html_url']}")
#         except Exception as e:
#             if "A pull request already exists" in str(e):
#                 print("A pull request for this branch already exists. Skipping PR creation.")
#             else:
#                 raise e

#     except Exception as e:
#         print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    create_and_merge()