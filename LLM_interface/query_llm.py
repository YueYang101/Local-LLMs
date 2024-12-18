import json
import requests
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

AVAILABLE_FUNCTIONS = {
    "handle_path": "If the user only give a path, detects if the given path is a file or folder and returns a response to choose between read_file function or list_folder function.",
    "read_file": "Reads the contents of a file if user specify it is a file.",
    "write_file": "Writes or updates a file with given content.",
    "list_folder": "Lists the tree structure of a folder and provides detailed information about its contents when the user specifies it is a folder.",
    "general_question": "Generates a marked response using special markers for titles, subtitles, and code blocks. This is triggered when the user asks a general question. The parameter should be /:/ to keep consistency"
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
    Changed: Instead of returning a single string, we yield each line.
    We expect each chunk of 'response' from the LLM server as a JSON line or raw text.
    """
    for chunk in response.iter_lines(decode_unicode=True):
        if chunk:
            # If your LLM returns JSON chunks, parse them. If it returns plain text, just yield the chunk.
            # Example assuming JSON lines with a 'response' key:
            try:
                json_data = json.loads(chunk)
                if "response" in json_data:
                    yield json_data["response"]
                else:
                    # If there's no 'response' key, just yield raw chunk
                    yield chunk
            except json.JSONDecodeError:
                # Not JSON, yield raw text
                yield chunk

def query_llm_function_decision(api_url, model_name, prompt, stream=True):
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": prompt, "stream": stream}

    logging.info("Sending request to LLM for function decision.")
    logging.debug(f"Model: {model_name}, API URL: {api_url}")
    logging.debug(f"Prompt: {prompt}")

    try:
        response = requests.post(api_url, headers=headers, json=payload, stream=stream)
        response.raise_for_status()

        if stream:
            # Return a generator that yields as chunks arrive
            return process_streamed_responses(response)
        else:
            response_data = response.json()
            llm_response = response_data.get("response", "No response generated.")
            return llm_response
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return f"Error: Request failed: {e}"
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON response.")
        return "Error: Invalid JSON response received."

def query_llm_marked_response(api_url, model_name, prompt, stream=True):
    pre_prompt = """
    You are a data assistant tasked with generating a plain-text response. 
    Use the following markers to identify sections and code blocks:

    ### Marking Guidelines:
    1. Titles:
       - Use `<<title>>` before the main title and `<<endtitle>>` after the title.

    2. Subtitles:
       - Use `<<subtitle>>` before a subtitle and `<<endsubtitle>>` after the subtitle.

    3. Code Blocks:
       - Use `<<code>>` before the code block and `<<endcode>>` after the code block.

    4. Explanations:
       - Write explanations as plain text without markers.
    """
    full_prompt = f"{pre_prompt}\n\n{prompt}"
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": full_prompt, "stream": stream}

    logging.info("Sending request to LLM for marked response.")
    logging.debug(f"Model: {model_name}, API URL: {api_url}")
    logging.debug(f"Prompt: {full_prompt}")

    try:
        response = requests.post(api_url, headers=headers, json=payload, stream=stream)
        response.raise_for_status()

        if stream:
            # Stream the response
            return process_streamed_responses(response)
        else:
            response_data = response.json()
            llm_response = response_data.get("response", "No marked response generated.")
            return llm_response
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return f"Error: Request failed: {e}"
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON response.")
        return "Error: Invalid JSON response received."

import re

def convert_marked_to_html(marked_response):
    html_output = marked_response
    html_output = re.sub(r"<<title>>(.*?)<<endtitle>>", r"<h1>\1</h1>", html_output, flags=re.DOTALL)
    html_output = re.sub(r"<<subtitle>>(.*?)<<endsubtitle>>", r"<h2>\1</h2>", html_output, flags=re.DOTALL)
    html_output = re.sub(r"<<code>>", r"<pre><code>", html_output)
    html_output = re.sub(r"<<endcode>>", r"</code></pre>", html_output)
    html_output = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html_output)
    html_output = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", html_output, flags=re.MULTILINE)

    lines = html_output.split("\n")
    in_list = False
    formatted_lines = []

    for line in lines:
        if line.startswith("* "):
            if not in_list:
                formatted_lines.append("<ul>")
                in_list = True
            formatted_lines.append(f"<li>{line[2:].strip()}</li>")
        else:
            if in_list:
                formatted_lines.append("</ul>")
                in_list = False
            formatted_lines.append(line)

    if in_list:
        formatted_lines.append("</ul>")

    html_output = "\n".join(formatted_lines)
    html_output = re.sub(r"<<.*?>>", "", html_output)
    return html_output