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

def check_eslint(code_content):
    """
    Run ESLint on the given JavaScript code content using a separate Node.js script.
    """
    # Path to the run_eslint.js file
    script_path = os.path.join(os.path.dirname(__file__), 'run_eslint.js')

    try:
        # Run the Node.js script
        result = subprocess.run(['node', script_path, code_content], capture_output=True, text=True, check=False)
        
        # Try to parse stdout as JSON
        try:
            lint_results = json.loads(result.stdout)
        except json.JSONDecodeError:
            # If stdout is not valid JSON, check if there's output in stderr
            if result.stderr:
                try:
                    error_data = json.loads(result.stderr)
                    return f"Error running ESLint: {error_data.get('error', 'Unknown error')}"
                except json.JSONDecodeError:
                    # If stderr is also not valid JSON, return the raw output
                    return f"Error running ESLint. Raw output: {result.stderr or result.stdout}"
            else:
                return f"Error running ESLint. Raw output: {result.stdout}"

        if isinstance(lint_results, dict) and 'error' in lint_results:
            return f"Error running ESLint: {lint_results['error']}"

        if not lint_results or (isinstance(lint_results, list) and len(lint_results) == 0):
            return "No ESLint issues found."

        # Format the results
        formatted_results = []
        for file_result in lint_results:
            for message in file_result['messages']:
                formatted_results.append(f"Line {message['line']}: {message['message']} ({message['ruleId']})")

        return "\n".join(formatted_results)
    except FileNotFoundError:
        return "Node.js is not installed or not in the system PATH. Please install Node.js and ensure it's accessible from the command line."
    except Exception as e:
        return f"Unexpected error: {str(e)}"
