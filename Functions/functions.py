import os
from docx import Document
import PyPDF2
import urllib.parse
import logging

# All the output from the llm is plain text format in case it will be used for input again.

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
            logging.debug("File type detected: .docx")
            doc = Document(file_path)
            content = "\n".join([para.text for para in doc.paragraphs])
            logging.debug(f"Successfully read .docx file: {file_path}")
            return content
        elif file_path.endswith(".pdf"):
            logging.debug("File type detected: .pdf")
            pdf_text = ""
            with open(file_path, "rb") as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text()
            logging.debug(f"Successfully read .pdf file: {file_path}")
            return pdf_text.strip()
        elif file_path.endswith(".py"):
            logging.debug("File type detected: .py")
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                logging.debug(f"Successfully read .py file: {file_path}")
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
            logging.debug("File type detected: .docx")
            doc = Document()
            for line in content.split("\n"):
                doc.add_paragraph(line)
            doc.save(file_path)
            logging.debug(f"Successfully wrote .docx file: {file_path}")
            return f"Word file successfully written to {file_path}"
        elif file_path.endswith(".py"):
            logging.debug("File type detected: .py")
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

def list_folder(folder_path: str) -> dict:
    """
    Lists the structure of the last folder in the given folder path.
    Always outputs a JSON structure that includes both plain text format
    and hierarchical JSON format.

    Args:
        folder_path (str): The path to the folder.

    Returns:
        dict: A JSON structure containing plain text and hierarchical structure.
    """
    logging.info(f"Generating folder structure for: {folder_path}")

    def build_tree(path, level=0):
        logging.debug(f"Building tree for path: {path}, level: {level}")
        plain_text_structure = ""
        json_structure = {"name": os.path.basename(path), "type": "folder", "children": []}
        indent = "    " * level
        prefix = f"{indent}├── "

        if os.path.isdir(path):
            dir_name = os.path.basename(path)
            if dir_name.startswith('.'):  # Skip hidden directories
                logging.debug(f"Skipping hidden directory: {dir_name}")
                return "", None

            plain_text_structure += f"{prefix}{dir_name}/\n"
            logging.debug(f"Added directory: {dir_name}")

            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if item.startswith('.'):  # Skip hidden files/directories
                    logging.debug(f"Skipping hidden file/directory: {item}")
                    continue

                sub_plain, sub_json = build_tree(item_path, level + 1)
                plain_text_structure += sub_plain
                if sub_json:  # Add child to JSON structure
                    json_structure["children"].append(sub_json)
        else:
            file_name = os.path.basename(path)
            if file_name.startswith('.'):  # Skip hidden files
                logging.debug(f"Skipping hidden file: {file_name}")
                return "", None

            plain_text_structure += f"{prefix}{file_name}\n"
            logging.debug(f"Added file: {file_name}")

            # Add file to JSON structure
            json_structure = {"name": file_name, "type": "file", "path": path}

        return plain_text_structure, json_structure

    if not os.path.exists(folder_path):
        logging.error(f"Path does not exist: {folder_path}")
        return {"error": f"Path does not exist: {folder_path}", "plain_text": "", "folder_json": None}

    if not os.path.isdir(folder_path):
        logging.error(f"Path is not a folder: {folder_path}")
        return {"error": f"Path is not a folder: {folder_path}", "plain_text": "", "folder_json": None}

    try:
        last_folder_name = os.path.basename(os.path.abspath(folder_path))
        logging.debug(f"Processing root folder: {last_folder_name}")
        plain_text_tree = f"{last_folder_name}/\n"
        json_tree = {"name": last_folder_name, "type": "folder", "children": []}

        for item in sorted(os.listdir(folder_path)):
            item_path = os.path.join(folder_path, item)
            if item.startswith('.'):  # Skip hidden files/directories
                logging.debug(f"Skipping hidden file/directory in root: {item}")
                continue

            sub_plain, sub_json = build_tree(item_path, level=1)
            plain_text_tree += sub_plain
            if sub_json:  # Add child to JSON root
                json_tree["children"].append(sub_json)

        logging.info(f"Successfully generated folder structure for: {folder_path}")

        # Return combined output
        return {"plain_text": plain_text_tree, "folder_json": json_tree}
    except Exception as e:
        logging.error(f"Error reading folder: {e}")
        return {"error": f"Error reading folder: {e}", "plain_text": "", "folder_json": None}