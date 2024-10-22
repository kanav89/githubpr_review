
import os
from dotenv import load_dotenv
from anthropic import Anthropic


load_dotenv()


def analyze_code_anthropic(code_content, linter_output, language):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""\
As a {language} expert, fix the following code based on the linter output:

1. Apply all linter errors and warnings.
2. Keep line length below 80 characters.
3. Return only the corrected code without explanations.

{language} Code:
{code_content}

Linter Output:
{linter_output}

Provide only the corrected code:"""

    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )
        
        return response.content[0].text.strip()
    except Exception as e:
        print(f"Error in API call: {str(e)}")
        return f"An error occurred: {str(e)}"



