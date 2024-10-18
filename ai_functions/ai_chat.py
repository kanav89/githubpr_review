import requests
import os
from dotenv import load_dotenv

load_dotenv()

perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")




def get_perplexity_response(question, pr_files, conversation_history):
    # Concatenate all conversation history items and the question into a single string
    history_string = " ".join(
        f"{item['role']}: {item['content']}" 
        for item in conversation_history
    )
    content = history_string + question
    url = "https://api.perplexity.ai/chat/completions"
    # Construct the payload for the request
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                'content': f"Context: {pr_files}\n\nQuestion: {question}\n\n"
            },
            {
                "role": "user",
                "content": content
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.2,
        
    }
    # Set the headers for the request
    headers = {
        "Authorization": f"Bearer {perplexity_api_key}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    # print(response.json())
    return response.json()['choices'][0]['message']['content']



    
