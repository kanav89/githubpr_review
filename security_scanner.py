import json
import subprocess
import tempfile
import os

def scan_security(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    try:
        result = subprocess.run(['bandit', '-f', 'json', '-q', temp_file_path], capture_output=True, text=True)
        output = json.loads(result.stdout)
        
        if not output['results']:
            return "No security issues found."
        
        issues = []
        for result in output['results']:
            issues.append(f"Line {result['line_number']}: {result['issue_text']} (Severity: {result['issue_severity']})")
        
        return "\n".join(issues)
    finally:
        os.unlink(temp_file_path)
