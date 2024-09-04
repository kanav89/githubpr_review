import requests
import os
from getpass import getpass
from base64 import b64decode
import tempfile
from flake8.api import legacy as flake8
from get_pr import get_file_content,get_pr_files,get_user_prs,get_github_token

def check_flake8(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    try:
        style_guide = flake8.get_style_guide()
        report = style_guide.check_files([temp_file_path])
        
        if report.total_errors == 0:
            print("No issues found in the code")
        else:
            print(f"Found {report.total_errors} issues in the code:")
            # TODO: Implement error reporting
    finally:
        os.unlink(temp_file_path)



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

    check_flake8(content)
    # check_code_style(code)
if __name__ == "__main__":
    main()