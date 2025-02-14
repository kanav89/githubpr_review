import os
from flask import Flask, request, Response
from github import GithubIntegration
from dotenv import load_dotenv
import logging
from github_functions.handle_new_pr import handle_new_pr
from github_functions.handle_new_comment import handle_new_comment
import hmac
import hashlib
import base64

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

app_id = os.getenv("APP_ID")

github_private_key_base64 = os.environ.get("PRIVATE_KEY_BASE64")
github_private_key = base64.b64decode(github_private_key_base64).decode("utf-8")
app_key = github_private_key
git_integration = GithubIntegration(
    app_id,
    app_key,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_valid_signature(signature: str, payload: bytes, secret: str) -> bool:
    """
    Validate the GitHub webhook signature against the payload.

    Args:
        signature: The signature from X-Hub-Signature-256 header
        payload: The raw request payload
        secret: The webhook secret

    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not secret:
        logger.error("Webhook secret is not set")
        return False
    if not signature:
        logger.error("X-Hub-Signature-256 header is missing")
        return False
    try:
        logger.debug(f"Received signature: {signature}")
        expected_signature = hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        logger.debug(f"Expected signature: sha256={expected_signature}")
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    except Exception as e:
        logger.error(f"Error validating signature: {str(e)}")
        return False


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__)

    @app.route("/", methods=["POST"])
    def bot():
        """
        Handle incoming GitHub webhook requests.

        Returns:
            tuple[str, int] | str: Response message and status code
        """
        try:
            signature = request.headers.get("X-Hub-Signature-256")
            webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
            logger.info(f"Received webhook with signature: {signature}")
            logger.debug(f"Request headers: {dict(request.headers)}")

            if not webhook_secret:
                logger.error("GITHUB_WEBHOOK_SECRET environment variable is not set")
                return "Configuration error", 500

            if not is_valid_signature(signature, request.data, webhook_secret):
                logger.warning(f"Invalid signature. Received: {signature}")
                return "Invalid signature", 403

            payload = request.json
            if payload.get("action") == "opened" and "pull_request" in payload:
                logger.info("Handling new pull request")
                return handle_new_pr(payload)
            elif (
                payload.get("action") == "created"
                and "comment" in payload
                and "issue" in payload
                and "pull_request" in payload["issue"]
            ):
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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
