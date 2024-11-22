import json
import requests
import os

# Define the path to your config.json file
CONFIG_PATH = os.path.join("LLM_interface", "config.json")

# Load configuration from config.json
try:
    with open(CONFIG_PATH, "r") as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise Exception(f"Configuration file not found at {CONFIG_PATH}")

# Extract model name and API URL from config
MODEL_NAME = config.get("model_name", "default_model_name")
API_URL = config.get("api_url", "http://localhost:11434/api/generate")

# Function to process streamed responses from the API
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

# Function to query the Llama API
def query_ollama_stream(model_name, prompt, stream=False):
    """
    Queries the API with a prompt and handles streamed responses for incremental updates.
    """
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": prompt, "stream": stream}

    try:
        with requests.post(API_URL, headers=headers, json=payload, stream=stream) as response:
            response.raise_for_status()
            if stream:
                return process_streamed_responses(response)
            else:
                return response.json().get("response", "No response generated.")
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"

# Function to read a file and return its contents
def read_file(file_path):
    """
    Reads the contents of a file from the given path.
    """
    try:
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: File not found at {file_path}"
    except Exception as e:
        return f"Error reading file: {e}"

# Function to write or update a file with given contents
def write_file(file_path, content):
    """
    Writes or updates a file with the specified content.
    """
    try:
        with open(file_path, "w") as file:
            file.write(content)
        return f"File successfully written to {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"

# Function to preprocess user input for LLM to decide actions
def preprocess_prompt_for_rag(prompt):
    """
    Adds a system directive to the user's prompt to help the LLM determine if RAG is needed.
    """
    system_directive = (
        "You are a code assistant with access to file reading and writing capabilities. "
        "If the user asks for file operations, suggest the file path or content to read or write. "
        "If no file operation is needed, proceed as usual."
    )
    return f"{system_directive}\n\nUser Prompt: {prompt}"

# Function to handle LLM decision and execute RAG if needed
def handle_llm_decision(user_prompt):
    """
    Decides whether to execute a RAG function based on the LLM's response.
    """
    enriched_prompt = preprocess_prompt_for_rag(user_prompt)
    response = query_ollama_stream(MODEL_NAME, enriched_prompt, stream=False)
    print("\nLLM Decision Response:")
    print(response)

    # Parse the LLM response for RAG triggers
    if "read file" in response.lower():
        # Extract file path from response (assume a format like "read file: <path>")
        file_path = response.split("read file:")[-1].strip()
        return read_file(file_path)

    elif "write file" in response.lower():
        # Extract file path and content (assume a format like "write file: <path>: <content>")
        try:
            _, file_path, content = response.split(":", 2)
            return write_file(file_path.strip(), content.strip())
        except ValueError:
            return "Error: LLM response format invalid for writing file."

    return response  # Default response if no RAG action is needed

# Main function
if __name__ == "__main__":
    while True:
        user_prompt = input("Enter your prompt (or 'exit' to quit): ").strip()
        if user_prompt.lower() == "exit":
            break

        print("\nProcessing...")
        final_response = handle_llm_decision(user_prompt)
        print("\nFinal Response:")
        print(final_response)