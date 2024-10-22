# GitHub PR Review Bot

This project is an AI-powered GitHub App that automatically reviews pull requests and provides code analysis and styling suggestions.

## Features

- Automatically analyzes new pull requests
- Responds to comments in pull requests
- Uses AI-powered code analysis (Anthropic's Claude model)
- Performs style checking using Flake8 for Python code
- Supports chatbot-like interactions for code-related questions
- Automatically applies and merges approved changes

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)
- [Deployment](#deployment)
- [Security](#security)
- [Support](#support)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/githubpr_review.git
   cd githubpr_review
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables (see [Configuration](#configuration) section).

4. Run the app:
   ```
   python app.py
   ```

## Configuration

Create a `.env` file in the project root with the following variables:
APP_ID=your_github_app_id
PRIVATE_KEY_BASE64=your_base64_encoded_private_key
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_TOKEN=your_github_personal_access_token
ANTHROPIC_API_KEY=your_anthropic_api_key

Make sure to replace the placeholder values with your actual credentials.

## Usage

The bot responds to the following commands in pull request comments:

1. `@bot [your question]`: Ask the bot a question about the code in the pull request.
2. `@style`: Check for styling issues in the code.
3. `@style Approve Changes`: Apply AI-suggested fixes to styling issues.
4. `@style Merge Changes`: Merge the approved changes into the pull request.

For more details on the bot's functionality, refer to the `handle_new_comment` function in `github_functions/handle_new_comment.py`.

## API Reference

The main components of the application are:

1. `app.py`: Flask application setup and webhook handling
2. `github_functions/`: Contains functions for interacting with GitHub API
3. `ai_functions/`: AI-powered code analysis and chatbot functionality
4. `code_analysis/`: Code style checking using Flake8

Key functions:

- `handle_new_pr()`: Handles new pull request events
- `handle_new_comment()`: Processes commands in pull request comments
- `analyze_code_anthropic()`: Performs AI-powered code analysis
- `create_chatbot()`: Generates responses to user queries
- `check_flake8()`: Runs Flake8 style checker on Python code

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Deployment

This project is configured for deployment on Render.

For other deployment options, you may need to adjust the configuration accordingly.

## Security

Please note that this project uses environment variables for sensitive information. Make sure to keep your `.env` file secure and never commit it to version control. The `.gitignore` file is set up to exclude the `.env` file and other sensitive information.

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.

---

Remember to keep your API keys and tokens secure, and never share them publicly. Happy coding!
