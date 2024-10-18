import os
import requests
from flask import Flask, request
import github
from github import GithubIntegration
from dotenv import load_dotenv
import logging

from github_functions.handle_new_pr import handle_new_pr
from github_functions.handle_new_comment import handle_new_comment
import hmac
import hashlib
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address

# limiter = Limiter(
#     get_remote_address,
#     app=app,
#     default_limits=["200 per day", "50 per hour"]
# )
load_dotenv()
app = Flask(__name__)
app_id = os.getenv("APP_ID")

perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
ai_fixed_code_list = []
ai_fixed_code = ""
with open(
        os.path.normpath(os.path.expanduser(os.getenv("PRIVATE_KEY_PATH"))),
        'r'
) as cert_file:
    app_key = cert_file.read()
git_integration = GithubIntegration(
    app_id,
    app_key, 
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_valid_signature(signature, payload, secret):
    expected_signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
@app.route("/", methods=['POST'])
# @limiter.limit("10 per minute")
def bot():
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Hub-Signature-256')
        if not is_valid_signature(signature, request.data, os.getenv('GITHUB_WEBHOOK_SECRET')):
            return "Invalid signature", 403
        payload = request.json
        if payload.get('action') == 'opened' and 'pull_request' in payload:
            logger.info("Handling new pull request")
            return handle_new_pr(payload)
        elif payload.get('action') == 'created' and 'comment' in payload and 'issue' in payload and 'pull_request' in payload['issue']:
            logger.info("Handling new comment")
            return handle_new_comment(payload)
        else:
            logger.info("Received unhandled webhook event")
        return "ok"
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return "Internal server error", 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)

