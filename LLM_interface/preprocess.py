import json

# Available functions for the LLM
AVAILABLE_FUNCTIONS = {
    "read_file": "Reads the contents of a file. Input: file_path (str).",
    "write_file": "Writes or updates a file with given content. Input: file_path (str), content (str).",
    "list_folder": "Lists the structure of a folder. Optionally reads the content of files. Input: folder_path (str), include_contents (bool).",
}

def preprocess_prompt_with_functions(user_prompt):
    """
    Prepares the user prompt with a list of available functions for the LLM.
    """
    system_directive = f"""
    You are a code assistant with access to the following functions:
    {json.dumps(AVAILABLE_FUNCTIONS, indent=2)}
    
    Your task is to decide which function to use based on the user's input. Respond only with the function name and its parameters in JSON format. 
    For example:
    {{
        "function": "read_file",
        "parameters": {{
            "file_path": "/path/to/file"
        }}
    }}
    """
    return f"{system_directive}\n\nUser Prompt: {user_prompt}"