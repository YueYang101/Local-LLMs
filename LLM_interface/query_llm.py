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
# QUERY LLM and return Enhanced HTML Response
# ========================
def query_llm_html_response(api_url, model_name, prompt, stream=False):
    """
    Queries the API with a prompt, asking the LLM to generate an HTML-formatted response.
    The HTML includes enhanced formatting for code blocks, headings, and interactive features.

    Args:
        api_url (str): The API URL to query.
        model_name (str): The name of the model to use.
        prompt (str): The prompt to send to the LLM.
        stream (bool): Whether to handle streamed responses.

    Returns:
        str: The LLM's response in HTML format.
    """
    # Enhanced pre-prompt with detailed HTML generation instructions
    pre_prompt = """
    You are a data assistant tasked with generating a clean and professional HTML response. 
    Ensure the following:

    ### Headings and Titles:
    - Use appropriate headings (<h1>, <h2>, <h3>, etc.) for clear organization.
    - Ensure the main title uses <h1> and subsequent sections are appropriately nested.

    ### Code Blocks:
    - Wrap each code snippet inside a <div class="code-container">.
    - Include a <span class="code-language"> element at the top of the code block to indicate the programming language.
    - Provide a "Copy" button inside the code block container, aligned to the top-right corner, using:
        <button class="copy-button" onclick="copyToClipboard()">Copy</button>
    - The code itself must be wrapped in <pre><code> tags for proper formatting.
    - Ensure the "Copy" button functionality is clearly indicated for developers.

    ### Example Structure:
    ```html
    <div class="code-container">
        <span class="code-language">Python</span>
        <button class="copy-button" onclick="copyToClipboard()">Copy</button>
        <pre><code>
        # Example Python Code
        def greet():
            print("Hello, World!")
        </code></pre>
    </div>
    ```

    ### Explanations:
    - Provide clear, concise, and readable explanations for each section or code snippet.
    - Use <p> tags for explanations, and ensure the text is well-spaced and visually accessible.

    ### Styling Consistency:
    - All HTML should follow semantic and clean formatting.
    - Ensure indentation and closing tags are accurate.

    ### Functionality and Usability:
    - The "Copy" button must copy the content within the <pre><code> block.
    - Include all necessary HTML attributes to ensure proper rendering.

    ### Example Prompt:
    Below is an example of a Python script. Explain the script in detail, include a heading, and render the code block with the "Copy" button:
    ```
    import math

    def calculate_circle_area(radius):
        return math.pi * radius**2
    ```

    ### Example Output:
    ```html
    <h1>Python Script Explanation</h1>
    <p>This script defines a function to calculate the area of a circle given its radius.</p>
    <div class="code-container">
        <span class="code-language">Python</span>
        <button class="copy-button" onclick="copyToClipboard()">Copy</button>
        <pre><code>
        import math

        def calculate_circle_area(radius):
            return math.pi * radius**2
        </code></pre>
    </div>
    ```
    Ensure the generated HTML is clean and ready to be rendered directly in a web application.
    """
    full_prompt = f"{pre_prompt}\n\n{prompt}"

    # Prepare the request payload
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": full_prompt, "stream": stream}

    logging.info("Sending request to LLM for enhanced HTML-formatted response.")
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
                logging.debug(f"Enhanced LLM HTML Response: {llm_response}")
                return llm_response
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return f"<p><strong>Error:</strong> Request failed: {e}</p>"