import subprocess
import sys
import anthropic
from anthropic import HUMAN_PROMPT,AI_PROMPT
import os
from dotenv import load_dotenv
from anthropic import Anthropic
import hashlib
import json
from openai import OpenAI
import requests
load_dotenv()

# api_key = os.getenv("CALUDE_TOKEN")

def get_flake8_errors(code):
    with open('temp.py', 'w') as f:
        f.write(code)
    
    result = subprocess.run(['flake8', 'temp.py'], capture_output=True, text=True)
    return result.stdout

# CACHE_FILE = 'code_fixes_cache.json'

# def load_cache():
#     try:
#         with open(CACHE_FILE, 'r') as f:
#             return json.load(f)
#     except (FileNotFoundError, json.JSONDecodeError):
#         return {}

# def save_cache(cache):
#     with open(CACHE_FILE, 'w') as f:
#         json.dump(cache, f)

# @lru_cache(maxsize=100)
# def get_cache_key(code_content, flake8_output):
#     return hashlib.md5((code_content + flake8_output).encode()).hexdigest()


def analyze_code_perplexity(code_content, flake8_output):

    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                'content': f"""\
As a Python expert, your task is to fix the following code based on the Flake8 output provided. Please follow these instructions:

1. Apply all the given Flake8 errors and warnings to the code.
2. Return the full corrected code.
3. Keep line length below 80 characters (including whitespaces).
4. Add docstrings or comments for clarity where appropriate.

Python Code:
{code_content}

Flake8 Output:
{flake8_output}


Please provide the corrected code."""
            },
            {
                "role": "user",
                "content": "Please give corrected code and only remove unused imports. Don't give any description or explanation."
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.2,
        
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    # print(response.json())
    return response.json()['choices'][0]['message']['content']


def analyze_code(code_content, flake8_output):
    client = OpenAI(api_key=os.getenv("PERPLEXITY_API_KEY"), base_url="https://api.perplexity.ai")
#     cache = load_cache()
#     cache_key = get_cache_key(code_content, flake8_output)

#     if cache_key in cache:
#         previous_response = cache[cache_key]
#     else:
#         previous_response = None
    prompt = f"""\
{HUMAN_PROMPT} As a Python expert, your task is to fix the following code based on the Flake8 output provided. Please follow these instructions:

1. Analyze the Flake8 errors and warnings.
2. Apply all the given Flake8 errors and warnings to the code.
3. Return the full corrected code.
4. Keep line length below 80 characters (including whitespaces).
5. Ensure proper indentation and consistent code style.
6. Add docstrings or comments for clarity where appropriate.

Python Code:
{code_content}

Flake8 Output:
{flake8_output}


Please provide the corrected code.

{AI_PROMPT}
"""

    response = client.chat.completions.create(
        model="llama-3-sonar-large-32k-online",
        max_tokens=2000,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )
    
    # Concatenate all text blocks into a single string
    # print(response)
    full_response = ''.join(block for block in response.choices[0].message.content)
    # # Update cache
    # cache[cache_key] = full_response
    # save_cache(cache)
    
    return full_response

# if __name__ == "__main__":
#     analyze_code()

def main():
    with open('app.py', 'r') as file:
        code = file.read()
    
    errors = get_flake8_errors(code)
    
    if not errors:
        print("No flake8 errors found.")
        return
    
    fixed_and_highlighted = analyze_code_perplexity(code, errors)
    
    print(fixed_and_highlighted)

if __name__ == "__main__":
    main()