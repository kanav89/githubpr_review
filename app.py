import os
import requests
from flask import Flask, request, Response
import github
from github import GithubIntegration
from dotenv import load_dotenv
import logging

from github_functions.handle_new_pr import handle_new_pr
from github_functions.handle_new_comment import handle_new_comment
import hmac
import hashlib
import base64
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address

# limiter = Limiter(
#     get_remote_address,
#     app=app,
#     default_limits=["200 per day", "50 per hour"]
# )
load_dotenv()

perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
ai_fixed_code_list = []
ai_fixed_code = ""
# with open(
#         os.path.normpath(os.path.expanduser(os.getenv("PRIVATE_KEY_PATH"))),
#         'r'
# ) as cert_file:
#     app_key = cert_file.read()'
app_id = os.getenv("APP_ID")

github_private_key_base64 = os.environ.get('PRIVATE_KEY_BASE64')
github_private_key = base64.b64decode(github_private_key_base64).decode('utf-8')
app_key = github_private_key
git_integration = GithubIntegration(
    app_id,
    app_key, 
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def is_valid_signature(signature, payload, secret):
    if not secret:
        logger.error("Webhook secret is not set")
        return False
    if not signature:
        logger.error("X-Hub-Signature-256 header is missing")
        return False
    try:
        expected_signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    except Exception as e:
        logger.error(f"Error validating signature: {str(e)}")
        return False

def create_app():
    app = Flask(__name__)
    
    @app.route("/", methods=['POST'])
    def bot():
        try:
            # Verify webhook signature
            signature = request.headers.get('X-Hub-Signature-256')
            webhook_secret = os.getenv('GITHUB_WEBHOOK_SECRET')
            if not is_valid_signature(signature, request.data, webhook_secret):
                print(f"Invalid signature received: {signature}")
                print(f"Webhook secret: {webhook_secret}")
                # print(f"Request data: {request.data}")
                logger.warning("Invalid signature received")
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
            logger.error(f"An error occurred: {str(e)}", exc_info=True)
            return Response("Internal server error", status=500)

    return app

# Create the app instance
app = create_app()
