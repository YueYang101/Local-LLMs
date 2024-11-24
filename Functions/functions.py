import os
from docx import Document
import PyPDF2


def handle_path(path):
    """
    Detects if the given path is a file or folder and returns a response to choose
    between reading a file or listing a folder structure.

    Args:
        path (str): The file or folder path.

    Returns:
        str: Response indicating the type of operation to perform.
    """
    if os.path.isfile(path):
        return {"action": "read_file", "path": path}
    elif os.path.isdir(path):
        return {"action": "list_folder", "path": path}
    else:
        return {"error": f"{path} is neither a valid file nor a folder."}


def read_file(file_path):
    """
    Reads the contents of a file.
    Supports .docx (Word), .py (Python), and .pdf (PDF) files.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file or an error message.
    """
    try:
        if file_path.endswith(".docx"):
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        elif file_path.endswith(".pdf"):
            pdf_text = ""
            with open(file_path, "rb") as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text()
            return pdf_text.strip()
        elif file_path.endswith(".py"):
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        else:
            return f"Unsupported file type for reading: {file_path}"

    except FileNotFoundError:
        return f"Error: File not found at {file_path}"
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(file_path, content):
    """
    Writes or updates a file with the specified content.

    Args:
        file_path (str): The path to the file.
        content (str): The content to write.

    Returns:
        str: Success message or an error message.
    """
    try:
        if file_path.endswith(".docx"):
            doc = Document()
            for line in content.split("\n"):
                doc.add_paragraph(line)
            doc.save(file_path)
            return f"Word file successfully written to {file_path}"
        elif file_path.endswith(".py"):
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)
            return f"Python file successfully written to {file_path}"
        elif file_path.endswith(".pdf"):
            return "Error: Writing to PDF files is not supported."
        else:
            return f"Unsupported file type for writing: {file_path}"

    except Exception as e:
        return f"Error writing file: {e}"


# test code for the coming function
# '/Users/yang/Library/CloudStorage/OneDrive-Personal/Github Reps/Local-LLMs'

def list_folder(folder_path):
    """
    Lists the structure of the last folder in the given folder path.
    Recursively explores and includes only the subfolder contents under the given folder,
    excluding hidden files/directories and specified system directories.

    Args:
        folder_path (str): The path to the folder.

    Returns:
        str: A tree-like HTML string representation of the folder structure.
    """
    # Set of directory names to exclude
    exclude_dirs = {'__pycache__', '.git', '.venv', 'node_modules'}
    # Set of file names to exclude
    exclude_files = set()

    def build_tree(path, level=0):
        html_structure = ""
        indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * level  # Dynamic indentation for nesting
        prefix = f"{indent}├── "  # Add the '├──' sign before each line

        if os.path.isdir(path):
            dir_name = os.path.basename(path)
            if dir_name.startswith('.') or dir_name in exclude_dirs:
                return ""  # Skip hidden or excluded directories
            html_structure += f"{prefix}{dir_name}/<br>"
            # Iterate through the direct contents of the folder
            for item in sorted(os.listdir(path)):  # Sort for consistent ordering
                if item.startswith('.'):
                    continue  # Skip hidden files and directories
                item_path = os.path.join(path, item)
                # Skip excluded directories and files
                if os.path.isdir(item_path) and item in exclude_dirs:
                    continue
                if os.path.isfile(item_path) and item in exclude_files:
                    continue
                html_structure += build_tree(item_path, level + 1)
        else:
            file_name = os.path.basename(path)
            if file_name.startswith('.') or file_name in exclude_files:
                return ""  # Skip hidden or excluded files
            # Add files to the tree
            html_structure += f"{prefix}{file_name}<br>"

        return html_structure

    # Validate the provided folder path
    if not os.path.exists(folder_path):
        return f"<p>Error: {folder_path} does not exist.</p>"
    if not os.path.isdir(folder_path):
        return f"<p>Error: {folder_path} is not a folder.</p>"

    # Generate the tree structure for the provided folder path
    try:
        # Start from the last folder in the path
        last_folder_name = os.path.basename(os.path.abspath(folder_path))
        html_tree = f"├── {last_folder_name}/<br>"
        for item in sorted(os.listdir(folder_path)):
            if item.startswith('.'):
                continue  # Skip hidden files and directories
            item_path = os.path.join(folder_path, item)
            # Skip excluded directories and files
            if os.path.isdir(item_path) and item in exclude_dirs:
                continue
            if os.path.isfile(item_path) and item in exclude_files:
                continue
            html_tree += build_tree(item_path, level=1)
        return html_tree.strip()
    except Exception as e:
        return f"<p>Error reading folder: {e}</p>"