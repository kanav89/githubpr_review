import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def analyze_code_perplexity(code_content, linter_output, language):
    client = OpenAI(api_key=os.getenv("PPLX_API_KEY"),
                    base_url="https://api.perplexity.ai")

    prompt = f"""\
As a {language} expert, fix the following code based on the linter output:

1. Apply all linter errors and warnings.
2. Keep line length below 80 characters.
3. Ensure proper indentation and consistent style.
4. Only remove unused imports.
5. Return only the corrected code without explanations.

{language} Code:
{code_content}

Linter Output:
{linter_output}

Provide only the corrected code:"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-sonar-small-128k-chat",
            max_tokens=2000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content[10:-3]
    except Exception as e:
        print(f"Error in API call: {str(e)}")
        return f"An error occurred: {str(e)}"


def test_analyze_code_perplexity():
    test_code = """import os
import sys

def my_function():
    x = 1
    y = 2
    print(x + y)
    """

    flake8_output = """
test_code.py:1:10: E401 multiple imports on one line
test_code.py:2:16: E201 whitespace after '('
test_code.py:3:5: E225 missing whitespace around operator
test_code.py:4:6: E225 missing whitespace around operator
test_code.py:5:11: E226 missing whitespace around arithmetic operator
"""

    corrected_code = analyze_code_perplexity(test_code, flake8_output)
    print("Original code:")
    print(test_code)
    print("\nCorrected code:")
    print(corrected_code[10:-3])


if __name__ == "__main__":
    test_analyze_code_perplexity()