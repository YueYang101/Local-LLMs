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