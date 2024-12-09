import json
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# ========================
# AVAILABLE FUNCTIONS
# ========================
AVAILABLE_FUNCTIONS = {
    "handle_path": "If the user only give a path, detects if the given path is a file or folder and returns a response to choose between read_file function or list_folder function.",
    "read_file": "Reads the contents of a file if user specify it is a file.",
    "write_file": "Writes or updates a file with given content.",
    "list_folder": "Lists the tree structure of a folder and provides detailed information about its contents when the user specifies it is a folder.",
}

# ========================
# Load LLM Configuration
# ========================
CONFIG_PATH = "LLM_interface/config.json"
try:
    with open(CONFIG_PATH, "r") as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise Exception(f"Configuration file not found at {CONFIG_PATH}")

MODEL_NAME = config.get("model_name", "llama3.1:70b")
API_URL = config.get("api_url", "http://localhost:11434/api/generate")


# ========================
# PREPROCESS PROMPT with Function selection
# ========================
def preprocess_prompt_with_functions(user_prompt):
    """
    Prepares the user prompt with a list of available functions for the LLM.
    """
    system_directive = f"""
    You are a multi-functional assistant. You can:
    1. Use the following functions:
    {json.dumps(AVAILABLE_FUNCTIONS, indent=2)}
    
    2. Answer general knowledge questions or queries. For such queries, respond directly with the answer as text.
    
    Your task is to decide whether the user's input requires the use of one or more of the provided functions or if it is a general question.
    
    - For file or folder operations, respond with the function names (in the order they should be executed) and their corresponding parameters in JSON format only.
    Your response **must strictly** follow the JSON format with the exact keys, structure and parameter names provided below:
    {{
        "function": ["write_file", "read_file"],
        "parameters": [
            {{
                "path": "/path/to/file",
                "content": "Example content to write"
            }},
            {{
                "path": "/path/to/file"
            }}
        ]
    }}
    
    - For general questions, respond directly with the answer as plain text.
    """
    return f"{system_directive}\n\nUser Prompt: {user_prompt}"

# ========================
# PROCESS STREAMED RESPONSES
# ========================
def process_streamed_responses(response):
    """
    Processes the API streamed response to display generated text incrementally.
    """
    generated_text = ""
    for chunk in response.iter_lines():
        if chunk:
            try:
                json_data = json.loads(chunk.decode("utf-8"))
                if "response" in json_data:
                    generated_text += json_data["response"]
                    print(json_data["response"], end="", flush=True)
            except json.JSONDecodeError:
                pass
    return generated_text

# ========================
# QUERY LLM
# ========================
def query_llm(api_url, model_name, prompt, stream=False):
    """
    Queries the API with a prompt and handles streamed responses for incremental updates.
    """
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": prompt, "stream": stream}

    logging.info("Sending request to LLM.")
    logging.debug(f"Model: {model_name}, API URL: {api_url}")
    logging.debug(f"Prompt: {prompt}")

    try:
        with requests.post(api_url, headers=headers, json=payload, stream=stream) as response:
            response.raise_for_status()
            if stream:
                logging.info("Processing streamed response from LLM.")
                return process_streamed_responses(response)
            else:
                llm_response = response.json().get("response", "No response generated.")
                logging.info("Received response from LLM.")
                logging.debug(f"LLM Response: {llm_response}")
                return llm_response
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return f"Request failed: {e}"

# ========================
# QUERY LLM HTML Response
# ========================
def query_llm_html_response(api_url, model_name, prompt, stream=False):
    """
    Queries the API with a prompt, asking the LLM to generate an HTML-formatted response.
    The HTML includes highlighted titles and formatted code blocks.

    Args:
        api_url (str): The API URL to query.
        model_name (str): The name of the model to use.
        prompt (str): The prompt to send to the LLM.
        stream (bool): Whether to handle streamed responses.

    Returns:
        str: The LLM's response in HTML format.
    """
    # Add a pre-prompt to guide the LLM to format the output in HTML
    pre_prompt = """
    You are a data assistant. Your task is to respond with HTML-formatted content.
    The output must include:
    1. Titles highlighted using <h1>, <h2>, etc.
    2. Code presented in <pre><code> blocks for formatting.
    3. Explanations styled in <p> for clarity.
    The HTML should be clean and well-structured.
    """
    full_prompt = f"{pre_prompt}\n\n{prompt}"

    # Prepare the request payload
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": full_prompt, "stream": stream}

    logging.info("Sending request to LLM for HTML-formatted response.")
    logging.debug(f"Model: {model_name}, API URL: {api_url}")
    logging.debug(f"Prompt: {full_prompt}")

    try:
        with requests.post(api_url, headers=headers, json=payload, stream=stream) as response:
            response.raise_for_status()
            if stream:
                logging.info("Processing streamed response from LLM.")
                return process_streamed_responses(response)
            else:
                llm_response = response.json().get("response", "No response generated.")
                logging.info("Received response from LLM.")
                logging.debug(f"LLM HTML Response: {llm_response}")
                return llm_response
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return f"<p><strong>Error:</strong> Request failed: {e}</p>"