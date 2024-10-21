import subprocess
import tempfile
import json
import os

def check_flake8(code_content):
    """
    Run Flake8 on the given code content and return the output.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False,encoding='utf-8') as temp_file:
        temp_file.write(code_content)
        temp_file_path = temp_file.name

    try:
        result = subprocess.run(['flake8', temp_file_path], capture_output=True, text=True)
        return result.stdout if result.stdout else "No Flake8 issues found."
    except subprocess.CalledProcessError as e:
        return f"Error running Flake8: {e}"
    finally:
        import os
        os.unlink(temp_file_path)

# def check_eslint(code_content):
#     """
#     Run ESLint on the given JavaScript code content and return the output.
#     """
#     with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as temp_file:
#         temp_file.write(code_content)
#         temp_file_path = temp_file.name

#     try:
#         # Check if eslint is available
#         subprocess.run(['eslint', '--version'], check=True, capture_output=True, text=True)
#     except subprocess.CalledProcessError:
#         return "ESLint is not installed or not in the system PATH."
#     except FileNotFoundError:
#         return "File not found"

#     try:
#         result = subprocess.run(['eslint', '-f', 'json', temp_file_path], capture_output=True, text=True)
#         if result.returncode == 0:
#             return "No ESLint issues found."
        
#         # Parse the JSON output
#         lint_results = json.loads(result.stdout)
#         if not lint_results:
#             return "No ESLint issues found."

#         # Format the results
#         formatted_results = []
#         for file_result in lint_results:
#             for message in file_result['messages']:
#                 formatted_results.append(f"Line {message['line']}: {message['message']} ({message['ruleId']})")

#         return "\n".join(formatted_results)
#     except subprocess.CalledProcessError as e:
#         return f"Error running ESLint: {e}"
#     finally:
#         os.unlink(temp_file_path)


