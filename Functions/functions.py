import os
from docx import Document
import PyPDF2
import urllib.parse
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def handle_path(path):
    """
    Detects if the given path is a file or folder and returns a response to choose
    between reading a file or listing a folder structure.

    Args:
        path (str): The file or folder path.

    Returns:
        dict: Response indicating the type of operation to perform.
    """
    logging.info(f"Handling path: {path}")
    if os.path.isfile(path):
        logging.debug(f"Path is a file: {path}")
        return {"action": "read_file", "path": path}
    elif os.path.isdir(path):
        logging.debug(f"Path is a directory: {path}")
        return {"action": "list_folder", "path": path}
    else:
        logging.error(f"Invalid path: {path}")
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
        logging.info(f"Reading file: {file_path}")
        if file_path.endswith(".docx"):
            doc = Document(file_path)
            content = "\n".join([para.text for para in doc.paragraphs])
            logging.debug(f"Read .docx file successfully: {file_path}")
            return content
        elif file_path.endswith(".pdf"):
            pdf_text = ""
            with open(file_path, "rb") as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text()
            logging.debug(f"Read .pdf file successfully: {file_path}")
            return pdf_text.strip()
        elif file_path.endswith(".py"):
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                logging.debug(f"Read .py file successfully: {file_path}")
                return content
        else:
            logging.warning(f"Unsupported file type: {file_path}")
            return f"Unsupported file type for reading: {file_path}"

    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return f"Error: File not found at {file_path}"
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
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
        logging.info(f"Writing to file: {file_path}")
        if file_path.endswith(".docx"):
            doc = Document()
            for line in content.split("\n"):
                doc.add_paragraph(line)
            doc.save(file_path)
            logging.debug(f"Successfully wrote .docx file: {file_path}")
            return f"Word file successfully written to {file_path}"
        elif file_path.endswith(".py"):
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)
            logging.debug(f"Successfully wrote .py file: {file_path}")
            return f"Python file successfully written to {file_path}"
        elif file_path.endswith(".pdf"):
            logging.error("Writing to PDF files is not supported.")
            return "Error: Writing to PDF files is not supported."
        else:
            logging.warning(f"Unsupported file type for writing: {file_path}")
            return f"Unsupported file type for writing: {file_path}"

    except Exception as e:
        logging.error(f"Error writing to file {file_path}: {e}")
        return f"Error writing file: {e}"


def list_folder(folder_path: str, enable_preview: bool = True) -> str:
    """
    Lists the structure of the last folder in the given folder path.
    Outputs HTML format with hyperlinks for file previews if enabled.

    Args:
        folder_path (str): The path to the folder.
        enable_preview (bool): Whether to generate hyperlinks for file previews.

    Returns:
        str: A tree-like HTML string representation of the folder structure.
    """
    exclude_dirs = {'__pycache__', '.git', '.venv', 'node_modules'}
    exclude_files = set()

    logging.info(f"Generating folder structure for: {folder_path} with preview enabled: {enable_preview}")

    def build_tree(path, level=0):
        html_structure = ""
        indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * level
        prefix = f"{indent}├── "

        if os.path.isdir(path):
            dir_name = os.path.basename(path)
            if dir_name.startswith('.') or dir_name in exclude_dirs:
                logging.debug(f"Skipping excluded directory: {dir_name}")
                return ""

            html_structure += f"{prefix}<span>{dir_name}/</span><br>"
            logging.debug(f"Added directory: {dir_name}")

            for item in sorted(os.listdir(path)):
                if item.startswith('.'):
                    logging.debug(f"Skipping hidden file/directory: {item}")
                    continue
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path) and item in exclude_dirs:
                    logging.debug(f"Skipping excluded subdirectory: {item}")
                    continue
                if os.path.isfile(item_path) and item in exclude_files:
                    logging.debug(f"Skipping excluded file: {item}")
                    continue
                html_structure += build_tree(item_path, level + 1)
        else:
            file_name = os.path.basename(path)
            if file_name.startswith('.') or file_name in exclude_files:
                logging.debug(f"Skipping hidden or excluded file: {file_name}")
                return ""

            if enable_preview:
                encoded_path = urllib.parse.quote(path)
                html_structure += f'{prefix}<a href="javascript:void(0);" class="file-link" data-file-path="{encoded_path}">{file_name}</a><br>'
                logging.debug(f"Added file with preview link: {file_name}")
            else:
                html_structure += f"{prefix}{file_name}<br>"
                logging.debug(f"Added file without preview link: {file_name}")

        return html_structure

    if not os.path.exists(folder_path):
        logging.error(f"Path does not exist: {folder_path}")
        return f"<p>Error: {folder_path} does not exist.</p>"
    if not os.path.isdir(folder_path):
        logging.error(f"Path is not a folder: {folder_path}")
        return f"<p>Error: {folder_path} is not a folder.</p>"

    try:
        last_folder_name = os.path.basename(os.path.abspath(folder_path))
        html_tree = f'<div class="folder-structure">├── {last_folder_name}/<br>'
        for item in sorted(os.listdir(folder_path)):
            if item.startswith('.'):
                logging.debug(f"Skipping hidden file/directory in root: {item}")
                continue
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path) and item in exclude_dirs:
                logging.debug(f"Skipping excluded directory in root: {item}")
                continue
            if os.path.isfile(item_path) and item in exclude_files:
                logging.debug(f"Skipping excluded file in root: {item}")
                continue
            html_tree += build_tree(item_path, level=1)
        html_tree += "</div>"
        logging.info(f"Successfully generated folder structure for: {folder_path}")
        return html_tree
    except Exception as e:
        logging.error(f"Error reading folder: {e}")
        return f"<p>Error reading folder: {e}</p>"