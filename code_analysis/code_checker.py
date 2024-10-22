import subprocess
import tempfile


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

