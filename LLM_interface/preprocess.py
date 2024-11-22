def preprocess_prompt_for_rag(user_prompt):
    """
    Prepares the user prompt with system-level directives for RAG integration.
    """
    system_directive = """
    You are a code assistant capable of reading and writing files. Always follow the specified response format for file-related actions:
    1. To read a file, respond only with: "read file: <file_path>"
    2. To write to a file, respond only with: "write file: <file_path>: <file_content>"
    For non-file-related queries, generate a normal response without any file-related triggers.
    """
    return f"{system_directive}\n\nUser Prompt: {user_prompt}"