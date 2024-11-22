import os
import json
from LLM_interface.query_llm import query_ollama_stream
from LLM_interface.rag_operations import read_file, write_file
from LLM_interface.preprocess import preprocess_prompt_for_rag

# Load configuration
CONFIG_PATH = os.path.join("LLM_interface", "config.json")
try:
    with open(CONFIG_PATH, "r") as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise Exception(f"Configuration file not found at {CONFIG_PATH}")

# Extract configuration
MODEL_NAME = config.get("model_name", "llama3.1:70b")
API_URL = config.get("api_url", "http://localhost:11434/api/generate")

# Function to handle LLM decision and execute RAG if needed
def handle_llm_decision(user_prompt):
    """
    Decides whether to execute a RAG function based on the LLM's response.
    """
    enriched_prompt = preprocess_prompt_for_rag(user_prompt)
    response = query_ollama_stream(API_URL, MODEL_NAME, enriched_prompt, stream=False)
    print("\nLLM Decision Response:")
    print(response)

    # Parse the LLM response for RAG triggers
    if "read file" in response.lower():
        # Extract file path from response
        file_path = response.split("read file:")[-1].strip()
        
        # Check for folder reading flag
        include_contents = "with contents" in response.lower()
        return read_file(file_path, include_contents)

    elif "write file" in response.lower():
        # Extract file path and content
        try:
            _, file_path, content = response.split(":", 2)
            return write_file(file_path.strip(), content.strip())
        except ValueError:
            return "Error: LLM response format invalid for writing file."

    return response  # Default response if no RAG action is needed

if __name__ == "__main__":
    while True:
        user_prompt = input("Enter your prompt (or 'exit' to quit): ").strip()
        if user_prompt.lower() == "exit":
            break

        print("\nProcessing...")
        final_response = handle_llm_decision(user_prompt)
        print("\nFinal Response:")
        print(final_response)