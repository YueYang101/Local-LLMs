from Functions.functions import read_file, write_file, list_folder

def read_file_tool(file_path: str) -> str:
    """
    LangChain-compatible wrapper for the read_file function.
    """
    return read_file(file_path)

def list_folder_tool(folder_path: str) -> str:
    """
    LangChain-compatible wrapper for the list_folder function.
    """
    return list_folder(folder_path)

def write_file_tool(file_path: str, content: str) -> str:
    """
    LangChain-compatible wrapper for the write_file function.
    """
    return write_file(file_path, content)