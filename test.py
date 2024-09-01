import sys
import tempfile
import os
import pycodestyle

def check_pep8(code):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    try:
        # Create a StyleGuide instance
        style_guide = pycodestyle.StyleGuide(quiet=True)

        # Check the code
        result = style_guide.check_files([temp_file_path])

        return result.total_errors, result.get_statistics()
    finally:
        # Ensure the temporary file is removed
        os.unlink(temp_file_path)

def main():
    print("Enter/paste your Python code. Press Ctrl-D (Unix) or Ctrl-Z (Windows) to finish:")
    code = sys.stdin.read()

    error_count, messages = check_pep8(code)

    if error_count == 0:
        print("\nNo PEP 8 issues found. Your code adheres to the style guide!")
    else:
        print(f"\nFound {error_count} PEP 8 style issues:")
        for message in messages:
            print(message)

if __name__ == "__main__":
    main()