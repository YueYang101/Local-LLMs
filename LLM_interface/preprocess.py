import json

# Available functions for the LLM
AVAILABLE_FUNCTIONS = {
    "handle_path": "Detects if the given path is a file or folder and returns a response to choose between reading a file or listing a folder structure.",
    "read_file": "Reads the contents of a file if user specify it is a file.",
    "write_file": "Writes or updates a file with given content.",
    "list_folder": "Lists the tree structure of a folder if user specify it is a folder.",
}

def preprocess_prompt_with_functions(user_prompt):
    """
    Prepares the user prompt with a list of available functions for the LLM.
    """
    system_directive = f"""
    You are a multi-functional assistant. You can:
    1. Use the following functions:
    {json.dumps(AVAILABLE_FUNCTIONS, indent=2)}
    
    2. Answer general knowledge questions or queries. For such queries, respond directly with the answer as text.
    
    Your task is to decide whether the user's input requires the use of one of the provided functions or if it is a general question.
    - For file or folder operations, respond only with the function name and its parameters in JSON format. 
    For example:
    {{
        "function": "read_file",
        "parameters": {{
            "file_path": "/path/to/file"
        }}
    }}
    - For general questions, respond directly with the answer in plain text.
    """
    return f"{system_directive}\n\nUser Prompt: {user_prompt}"