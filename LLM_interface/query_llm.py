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
    "general_question": "Generates a marked response using special markers for titles, subtitles, and code blocks. This is triggered when the user asks a general question. The parameter should be /:/ to keep consistency"
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
    
    2. Answer general knowledge questions or queries. For such queries use general_question function.
    
    Your task is to decide whether the user's input requires the use of one or more of the provided functions or if it is a general question.
    
    - Respond with the function names only (in the order they should be executed) and their corresponding parameters in JSON format.
    Your response **must strictly** follow the JSON format with the exact keys, structure and parameter names provided below:
    {{
        "function": ["write_file", "read_file", "general_question"],
        "parameters": [
            {{
                "path": "/path/to/file",
                "content": "Example content to write"
            }},
            {{
                "path": "/path/to/file"
            }}
            {{
                "general_question": "Answer of the question"
            }}
        ]
    }}
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
def query_llm_function_decision(api_url, model_name, prompt, stream=False):
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
# QUERY LLM and return Enhanced HTML Response
# ========================
def query_llm_marked_response(api_url, model_name, prompt, stream=False):
    """
    Queries the API with a prompt, asking the LLM to generate a marked plain-text response.
    Titles, subtitles, and code blocks are marked with distinct identifiers.

    Args:
        api_url (str): The API URL to query.
        model_name (str): The name of the model to use.
        prompt (str): The prompt to send to the LLM.
        stream (bool): Whether to handle streamed responses.

    Returns:
        str: The LLM's response in plain text with distinct markers.
    """
    # Enhanced pre-prompt with plain text markers
    pre_prompt = """
    You are a data assistant tasked with generating a plain-text response. 
    Use the following markers to identify sections and code blocks:

    ### Marking Guidelines:
    1. **Titles**:
       - Use `<<title>>` before the main title and `<<endtitle>>` after the title.

    2. **Subtitles**:
       - Use `<<subtitle>>` before a subtitle and `<<endsubtitle>>` after the subtitle.

    3. **Code Blocks**:
       - Use `<<code>>` before the code block and `<<endcode>>` after the code block.
       - Do not include formatting like indentation changes or HTML.

    4. **Explanations**:
       - Write explanations as plain text without markers.

    ### Example Input:
    Explain the following Python script and mark titles, subtitles, and code blocks:
    ```
    import math

    def calculate_circle_area(radius):
        return math.pi * radius**2
    ```

    ### Example Output:
    <<title>>Python Script Explanation<<endtitle>>
    This script defines a function to calculate the area of a circle given its radius.

    <<subtitle>>Code Implementation<<endsubtitle>>
    <<code>>
    import math

    def calculate_circle_area(radius):
        return math.pi * radius**2
    <<endcode>>

    Now, generate a response for the following input:
    """
    
    full_prompt = f"{pre_prompt}\n\n{prompt}"

    # Prepare the request payload
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": full_prompt, "stream": stream}

    logging.info("Sending request to LLM for marked plain-text response.")
    logging.debug(f"Model: {model_name}, API URL: {api_url}")
    logging.debug(f"Prompt: {full_prompt}")

    try:
        with requests.post(api_url, headers=headers, json=payload, stream=stream) as response:
            response.raise_for_status()

            if stream:
                logging.info("Processing streamed response from LLM.")
                # Process the streamed response incrementally
                return process_streamed_responses(response)
            else:
                # Process the full response
                llm_response = response.json().get("response", "No response generated.")
                logging.info("Received response from LLM.")
                logging.debug(f"Marked Plain-Text Response: {llm_response}")
                return llm_response
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return f"Error: Request failed: {e}"


def convert_marked_to_html(marked_response):
    """
    Converts a marked response with <<title>>, <<subtitle>>, <<code>>, and <<endcode>> into HTML.
    """
    import re

    html_output = marked_response
    html_output = re.sub(r"<<title>>(.*?)<<subtitle>>", r"<h1>\1</h1>", html_output)
    html_output = re.sub(r"<<subtitle>>(.*?)<<code>>", r"<h2>\1</h2>", html_output)
    html_output = re.sub(r"<<code>>", r"<pre><code>", html_output)
    html_output = re.sub(r"<<endcode>>", r"</code></pre>", html_output)
    
    # Ensure proper handling of any extra markers
    html_output = html_output.replace("<<title>>", "").replace("<<subtitle>>", "")
    return html_output