import requests
import os
from getpass import getpass
from base64 import b64decode
from dotenv import load_dotenv
import asyncio

load_dotenv()

def get_github_token():
    return os.getenv('GITHUB_TOKEN') 

async def get_user_prs(username, token):
    url = f'https://api.github.com/search/issues?q=is:pr+author:{username}+is:open'
    headers = {'Authorization': f'token {token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['items']

async def get_pr_files(owner, repo, pull_number, token):
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files'
    headers = {'Authorization': f'token {token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

async def get_file_content(file_url, token):
    headers = {'Authorization': f'token {token}'}
    response = requests.get(file_url, headers=headers)
    response.raise_for_status()
    content = response.json()['content']
    return b64decode(content).decode('utf-8')

def main():
    username = input('Enter your GitHub username: ')
    token = get_github_token()

    prs = get_user_prs(username, token)
    
    if not prs:
        print('No open pull requests found.')
        return

    print(f'Found {len(prs)} open pull requests:')
    for i, pr in enumerate(prs, 1):
        print(f"{i}. {pr['title']} ({pr['html_url']})")

    pr_number = int(input('Enter the number of the PR you want to inspect: ')) - 1
    selected_pr = prs[pr_number]

    # Extract owner and repo from the PR URL
    owner, repo = selected_pr['repository_url'].split('/')[-2:]
    pull_number = selected_pr['number']

    files = get_pr_files(owner, repo, pull_number, token)
    
    print(f"\nFiles changed in PR '{selected_pr['title']}':")
    for file in files:
        
        if file['status'] != 'removed':
            content = get_file_content(file['contents_url'], token)
            
            print(content)

if __name__ == '__main__':
    # files = get_pr_files("kanav89", "githubpr_review", "15", os.getenv("GITHUB_TOKEN"))
    
    # print(files)
    main()