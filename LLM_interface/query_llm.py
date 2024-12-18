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
    Logs each chunk to help debug streaming issues.
    """
    chunk_count = 0
    for chunk in response.iter_lines(decode_unicode=True):
        if chunk is not None:
            chunk_count += 1
            logging.debug(f"process_streamed_responses: Received chunk #{chunk_count}: {chunk[:100]}...")
            yield chunk + "\n"
    logging.info(f"process_streamed_responses: Total {chunk_count} chunks received.")

def query_llm_function_decision(api_url, model_name, prompt, stream=True):
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": prompt, "stream": stream}

    logging.info("query_llm_function_decision: Sending request to LLM for function decision.")
    logging.debug(f"query_llm_function_decision: Payload: {payload}")

    with requests.post(api_url, headers=headers, json=payload, stream=stream) as response:
        logging.info(f"query_llm_function_decision: Received status {response.status_code} from LLM.")
        response.raise_for_status()
        if stream:
            decision_text = ""
            for chunk in process_streamed_responses(response):
                decision_text += chunk
            logging.debug(f"query_llm_function_decision: Full decision response: {decision_text}")
            return decision_text
        else:
            data = response.json()
            return data.get("response", "No response.")

def query_llm_marked_response(api_url, model_name, prompt, stream=True):
    """
    Query the LLM and return a generator of text chunks.
    Logging added to debug streaming issues.
    """
    logging.info("query_llm_marked_response: Preparing to send request for streamed response.")
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": prompt, "stream": stream}
    logging.debug(f"query_llm_marked_response: Payload: {payload}")

    with requests.post(api_url, headers=headers, json=payload, stream=stream) as response:
        logging.info(f"query_llm_marked_response: LLM responded with status {response.status_code}")
        response.raise_for_status()
        chunk_count = 0
        for chunk in response.iter_lines(decode_unicode=True):
            if chunk:
                chunk_count += 1
                logging.debug(f"query_llm_marked_response: Chunk #{chunk_count}: {chunk[:100]}...")
                yield chunk
            else:
                # It's possible to get empty chunks, log them
                logging.debug("query_llm_marked_response: Received empty chunk.")
        logging.info(f"query_llm_marked_response: Streaming ended after {chunk_count} chunks.")