import json
import requests
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

AVAILABLE_FUNCTIONS = {
    "handle_path": "If the user only gives a path, detect if it is a file or folder.",
    "read_file": "Read the contents of a file.",
    "write_file": "Write or update a file with given content.",
    "list_folder": "List folder structure and explain project.",
    "general_question": "Answer general questions. Parameter should be /:/ to keep consistency."
}

CONFIG_PATH = "LLM_interface/config.json"
try:
    with open(CONFIG_PATH, "r") as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise Exception(f"Configuration file not found at {CONFIG_PATH}")

MODEL_NAME = config.get("model_name", "llama3.1:70b")
API_URL = config.get("api_url", "http://localhost:11434/api/generate")

def preprocess_prompt_with_functions(user_prompt):
    system_directive = f"""
    You are a multi-functional assistant. You can:
    1. Use the following functions:
    {json.dumps(AVAILABLE_FUNCTIONS, indent=2)}
    
    2. Answer general knowledge questions or queries. For such queries use general_question function.
    
    Your task is to decide whether the user's input requires the use of one or more of the provided functions or if it is a general question.
    
    - Respond with the function names only (in the order they should be executed) and their corresponding parameters in JSON format.
    {{
        "function": ["write_file", "read_file", "general_question"],
        "parameters": [
            {{
                "path": "/path/to/file",
                "content": "Example content to write"
            }},
            {{
                "path": "/path/to/file"
            }},
            {{
                "general_question": "Answer of the question"
            }}
        ]
    }}
    """
    return f"{system_directive}\n\nUser Prompt: {user_prompt}"

def process_streamed_responses(response):
    """
    Yields raw text chunks from the response stream.
    If your LLM returns JSON lines with a 'response' key, parse it here.
    Otherwise, yield lines as is.
    """
    for chunk in response.iter_lines(decode_unicode=True):
        if chunk:
            # If the LLM returns raw text
            yield chunk + "\n"

def query_llm_function_decision(api_url, model_name, prompt, stream=True):
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": prompt, "stream": stream}

    logging.info("Sending request to LLM for function decision.")
    with requests.post(api_url, headers=headers, json=payload, stream=stream) as response:
        response.raise_for_status()
        if stream:
            # Accumulate all chunks (for function decision we need the full JSON)
            decision_text = ""
            for chunk in process_streamed_responses(response):
                decision_text += chunk
            return decision_text
        else:
            data = response.json()
            return data.get("response", "No response.")

def query_llm_marked_response(api_url, model_name, prompt, stream=True):
    """
    Query the LLM and return a generator of text chunks.
    We no longer do special formatting instructions in the prompt.
    Just return plain text and rely on local formatting.
    """
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": prompt, "stream": stream}

    logging.info("Sending request to LLM for a general answer (streamed).")
    with requests.post(api_url, headers=headers, json=payload, stream=stream) as response:
        response.raise_for_status()
        # Return generator over chunks
        return process_streamed_responses(response)