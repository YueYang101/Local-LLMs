import json
from preprocess import preprocess_prompt_with_functions
from functions import read_file, write_file, list_folder
from LLM_interface.query_llm import query_ollama_stream

# Load configuration
CONFIG_PATH = "LLM_interface/config.json"
try:
    with open(CONFIG_PATH, "r") as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise Exception(f"Configuration file not found at {CONFIG_PATH}")

MODEL_NAME = config.get("model_name", "llama3.1:70b")
API_URL = config.get("api_url", "http://localhost:11434/api/generate")

def handle_llm_decision(user_prompt):
    """
    Handles the LLM decision-making process and executes the chosen function.
    """
    enriched_prompt = preprocess_prompt_with_functions(user_prompt)
    llm_response = query_ollama_stream(API_URL, MODEL_NAME, enriched_prompt, stream=False)

    try:
        response_data = json.loads(llm_response)
        function_name = response_data.get("function")
        parameters = response_data.get("parameters", {})

        if function_name == "read_file":
            return read_file(**parameters)
        elif function_name == "write_file":
            return write_file(**parameters)
        elif function_name == "list_folder":
            return list_folder(**parameters)
        else:
            return f"Error: Unknown function '{function_name}' requested by the LLM."
    except json.JSONDecodeError:
        return f"Error: Invalid JSON response from LLM. Response: {llm_response}"
    except Exception as e:
        return f"Error executing function: {e}"

if __name__ == "__main__":
    while True:
        user_prompt = input("Enter your prompt (or 'exit' to quit): ").strip()
        if user_prompt.lower() == "exit":
            break
        print("\nProcessing...")
        final_response = handle_llm_decision(user_prompt)
        print("\nFinal Response:")
        print(final_response)