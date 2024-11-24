import json
from Functions.functions import read_file, write_file, list_folder, handle_path
from LLM_interface.query_llm import query_ollama_stream
from LLM_interface.preprocess import preprocess_prompt_with_functions
import logging


# Load configuration
CONFIG_PATH = "LLM_interface/config.json"
try:
    with open(CONFIG_PATH, "r") as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise Exception(f"Configuration file not found at {CONFIG_PATH}")

# Model and API settings
MODEL_NAME = config.get("model_name", "llama3.1:70b")
API_URL = config.get("api_url", "http://localhost:11434/api/generate")


# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def handle_llm_decision(user_prompt: str):
    """
    Handles the LLM decision-making process and executes the chosen function.

    Args:
        user_prompt (str): The user's input describing the task.

    Returns:
        str: The output of the chosen function or a general text response.
    """
    enriched_prompt = preprocess_prompt_with_functions(user_prompt)
    llm_response = query_ollama_stream(API_URL, MODEL_NAME, enriched_prompt, stream=False)

    try:
        # Try to parse the response as JSON
        response_data = json.loads(llm_response)

        # If JSON, extract function and parameters
        function_name = response_data.get("function")
        parameters = response_data.get("parameters", {})

        if function_name == "handle_path":
            path = parameters.get("path")
            action_response = handle_path(path)

            if "action" in action_response:
                if action_response["action"] == "read_file":
                    return read_file(action_response["path"])
                elif action_response["action"] == "list_folder":
                    return list_folder(action_response["path"])
                else:
                    return "Error: Unknown action from handle_path."
            else:
                return action_response.get("error", "Error: Invalid response from handle_path.")
        elif function_name == "read_file":
            return read_file(**parameters)
        elif function_name == "write_file":
            return write_file(**parameters)
        elif function_name == "list_folder":
            return list_folder(**parameters)
        else:
            return f"Error: Unknown function '{function_name}' requested by the LLM."
    except json.JSONDecodeError:
        # If not JSON, treat as a plain text response
        logging.info("Received a general text response from LLM.")
        return llm_response.strip()
    except Exception as e:
        logging.error(f"Error executing function: {e}")
        return f"Error executing function: {e}"