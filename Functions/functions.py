import os
from docx import Document
import PyPDF2
import json
import logging
from LLM_interface.query_llm import preprocess_prompt_with_functions, query_llm, API_URL, MODEL_NAME, query_llm_html_response
from PyPDF2 import PdfReader
import docx

# ========================uvicorn main:app --host 127.0.0.1 --port 8000 --reload
# LLM DECISION FUNCTION
# ========================
def llm_decision(user_prompt: str):
    """
    Handles the LLM decision-making process and executes the chosen function(s).

    Args:
        user_prompt (str): The user's input describing the task.

    Returns:
        dict: JSON-like structure with 'plain_text' and 'detailed_info'.
    """
    logging.info("Starting llm_decision function.")
    enriched_prompt = preprocess_prompt_with_functions(user_prompt)
    logging.debug(f"Enriched prompt: {enriched_prompt}")
    llm_response = query_llm(API_URL, MODEL_NAME, enriched_prompt, stream=False)
    logging.debug(f"LLM Response: {llm_response}")

    try:
        # Parse the response as JSON
        response_data = json.loads(llm_response)
        logging.info("Successfully parsed LLM response as JSON.")

        # Extract functions and parameters
        functions = response_data.get("function")
        parameters = response_data.get("parameters", [])

        # Ensure functions is a list
        if isinstance(functions, str):
            functions = [functions]
        elif not isinstance(functions, list):
            raise ValueError("Invalid format for 'function'. Expected string or list.")

        # Ensure parameters is a list matching the number of functions
        if isinstance(parameters, dict):
            parameters = [parameters]  # Convert single dict to list for consistency
        if len(functions) != len(parameters):
            raise ValueError("Mismatch between number of functions and parameters.")

        # Process functions in order
        results = []
        for func, param in zip(functions, parameters):
            logging.info(f"Processing function: {func} with parameters: {param}")
            path = param.get("path")  # Consistent use of 'path'
            if func == "handle_path":
                action_response = handle_path(path)

                # Ensure action_response structure matches the expected format
                action_functions = action_response.get("function", [])
                action_parameters = action_response.get("parameters", [])
                if not isinstance(action_functions, list) or not isinstance(action_parameters, list):
                    results.append({
                        "plain_text": "Error: Invalid structure from handle_path.",
                        "detailed_info": {"path": path},
                    })
                    continue

                # Process the actions returned by handle_path
                for action_func, action_param in zip(action_functions, action_parameters):
                    if action_func == "read_file":
                        results.append(read_file(**action_param))
                    elif action_func == "list_folder":
                        results.append(list_folder(**action_param))
                    else:
                        results.append({
                            "plain_text": f"Error: Unknown action '{action_func}' from handle_path.",
                            "detailed_info": {"path": path},
                        })
            elif func == "read_file":
                results.append(read_file(**param))
            elif func == "write_file":
                results.append(write_file(**param))
            elif func == "list_folder":
                results.append(list_folder(**param))
            else:
                logging.warning(f"Unknown function '{func}' encountered.")
                results.append({
                    "plain_text": f"Error: Unknown function '{func}' requested by the LLM.",
                    "detailed_info": {},
                })

        # Combine results
        combined_plain_text = "\n\n".join([res["plain_text"] for res in results if "plain_text" in res])
        combined_detailed_info = [res.get("detailed_info", {}) for res in results]

        logging.info("Successfully processed all functions.")
        return {
            "plain_text": combined_plain_text,
            "detailed_info": combined_detailed_info,
        }
    except json.JSONDecodeError:
        logging.error("Error decoding LLM response as JSON.")
        return {"plain_text": llm_response.strip(), "detailed_info": {}}
    except Exception as e:
        logging.error(f"Error in llm_decision function: {e}")
        return {
            "plain_text": f"Error executing function: {e}",
            "detailed_info": {},
        }

# ========================
# HANDLE PATH FUNCTION
# ========================
def handle_path(path):
    """
    Determines if the given path is a file or directory and returns a structured response.

    Args:
        path (str): The file or folder path.

    Returns:
        dict: JSON-like structure with 'function' and 'parameters' to align with the LLM input/output format.
    """
    logging.info(f"Starting handle_path function with path: {path}")
    if os.path.isfile(path):
        logging.info(f"Detected file: {path}")
        return {
            "function": ["read_file"],
            "parameters": [
                {
                    "path": path
                }
            ]
        }
    elif os.path.isdir(path):
        logging.info(f"Detected directory: {path}")
        return {
            "function": ["list_folder"],
            "parameters": [
                {
                    "path": path
                }
            ]
        }
    else:
        logging.error(f"Invalid path: {path}")
        return {
            "function": ["error"],
            "parameters": [
                {
                    "error_message": f"{path} is neither a valid file nor a folder."
                }
            ]
        }

# ========================
# READ FILE FUNCTION
# ========================
def read_file(path: str):
    """
    Reads a file and queries the LLM to explain the content in HTML format.

    Args:
        path (str): The path to the file.

    Returns:
        dict: JSON structure with 'html_response' (LLM response in HTML) and 'detailed_info' (file name and content).
    """
    logging.info(f"Starting read_file function for path: {path}")

    try:
        # Log initial metadata setup
        logging.debug("Initializing file metadata.")
        file_metadata = {
            "name": os.path.basename(path),
            "contents": None
        }

        # Log file type detection
        if path.endswith(".docx"):
            logging.info("Detected .docx file. Attempting to read content.")
            doc = Document(path)
            file_metadata["contents"] = "\n".join([para.text for para in doc.paragraphs])
        elif path.endswith(".pdf"):
            logging.info("Detected .pdf file. Attempting to read content.")
            pdf_text = ""
            with open(path, "rb") as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text()
            file_metadata["contents"] = pdf_text.strip()
        elif path.endswith(".py"):
            logging.info("Detected .py file. Attempting to read content.")
            with open(path, "r", encoding="utf-8") as file:
                file_metadata["contents"] = file.read()
        else:
            logging.warning(f"Unsupported file type for: {path}")
            return {
                "html_response": f"<p>Unsupported file type for reading: {file_metadata['name']}</p>",
                "detailed_info": file_metadata
            }

        # Log content extraction
        if file_metadata["contents"] is None:
            logging.error(f"Failed to extract content from file: {path}")
            raise Exception("Failed to extract file content.")

        logging.info(f"Successfully read content from file: {file_metadata['name']}")

        # Log LLM query preparation
        logging.info("Preparing to query the LLM with file content.")
        enriched_prompt = f"Explain the following code:\n\n{file_metadata['contents']}"
        logging.debug(f"Enriched Prompt:\n{enriched_prompt}")

        # Query the LLM using the query_llm_html_response function
        logging.info("Querying the LLM to explain the code in HTML format.")
        llm_response_html = query_llm_html_response(API_URL, MODEL_NAME, enriched_prompt, stream=False)
        logging.debug(f"LLM HTML Response: {llm_response_html}")

        # Log final response preparation
        logging.info(f"LLM successfully explained the file: {file_metadata['name']}")

        return {
            "html_response": llm_response_html,  # Save the HTML response in the new key
            "detailed_info": file_metadata
        }

    except FileNotFoundError:
        logging.error(f"File not found: {path}")
        return {
            "html_response": f"<p>Error: File not found at {path}</p>",
            "detailed_info": {"name": os.path.basename(path)}
        }
    except Exception as e:
        logging.error(f"Error occurred while processing file {path}: {e}")
        return {
            "html_response": f"<p>Error reading file: {e}</p>",
            "detailed_info": {"name": os.path.basename(path)}
        }

# ========================
# WRITE FILE FUNCTION
# ========================
def write_file(path: str, content: str):
    logging.info(f"Starting write_file function with path: {path}")
    try:
        if path.endswith(".docx"):
            logging.info("Writing to .docx file.")
            doc = Document()
            for line in content.split("\n"):
                doc.add_paragraph(line)
            doc.save(path)
        elif path.endswith(".py"):
            logging.info("Writing to .py file.")
            with open(path, "w", encoding="utf-8") as file:
                file.write(content)
        elif path.endswith(".pdf"):
            logging.error("Writing to .pdf files is not supported.")
            return {
                "plain_text": "Error: Writing to PDF files is not supported.",
                "detailed_info": {"path": path, "file_type": "pdf"},
            }
        else:
            logging.warning("Unsupported file type.")
            return {
                "plain_text": f"Unsupported file type for writing: {path}",
                "detailed_info": {"path": path},
            }
        logging.info("Successfully wrote to file.")
        return {"plain_text": f"File successfully written to {path}", "detailed_info": {"path": path}}
    except Exception as e:
        logging.error(f"Error writing to file {path}: {e}")
        return {"plain_text": f"Error writing file: {e}", "detailed_info": {"path": path}}

# ========================
# LIST FOLDER FUNCTION
# ========================
def list_folder(path: str) -> dict:
    """
    Lists the structure of the last folder in the given path.
    Outputs a plain text tree and a JSON structure containing file names and contents.

    Args:
        path (str): The path to the folder.

    Returns:
        dict: A JSON structure containing 'plain_text' and 'detailed_info'.
    """
    logging.info(f"Generating folder structure for: {path}")

    # Helper function to read file content
    def read_file_content(file_path: str) -> str:
        try:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

            if ext == '.pdf':
                with open(file_path, 'rb') as f:
                    reader = PdfReader(f)
                    return "\n".join(page.extract_text() for page in reader.pages)

            elif ext == '.docx':
                doc = docx.Document(file_path)
                return "\n".join(paragraph.text for paragraph in doc.paragraphs)

            elif ext in {'.txt', '.py', '.js', '.html', '.md'}:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()

            return "Unsupported file type for preview."
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
            return f"Error reading file: {e}"

    # Helper function to recursively build the folder structure
    def build_tree(path, level=0):
        logging.debug(f"Building tree for path: {path}, level: {level}")
        plain_text_structure = ""
        json_structure = {"name": os.path.basename(path), "content": None}
        indent = "    " * level
        prefix = f"{indent}├── "

        # Check if the path is a directory
        if os.path.isdir(path):
            dir_name = os.path.basename(path)

            # Skip hidden directories and __pycache__
            if dir_name.startswith('.') or dir_name == "__pycache__":
                logging.debug(f"Skipping hidden or __pycache__ directory: {dir_name}")
                return "", None

            plain_text_structure += f"{prefix}{dir_name}/\n"
            logging.debug(f"Added directory: {dir_name}")

            # Recursively process items in the directory
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)

                # Skip hidden files/directories and __pycache__
                if item.startswith('.') or item == "__pycache__":
                    logging.debug(f"Skipping hidden file/directory or __pycache__: {item}")
                    continue

                sub_plain, sub_json = build_tree(item_path, level + 1)
                plain_text_structure += sub_plain
        else:
            # Process files
            file_name = os.path.basename(path)

            # Skip hidden files
            if file_name.startswith('.'):
                logging.debug(f"Skipping hidden file: {file_name}")
                return "", None

            plain_text_structure += f"{prefix}{file_name}\n"
            logging.debug(f"Added file: {file_name}")

            # Add file content to JSON structure
            json_structure["name"] = file_name
            json_structure["content"] = read_file_content(path)

        return plain_text_structure, json_structure

    # Validate the folder path
    if not os.path.exists(path):
        logging.error(f"Path does not exist: {path}")
        return {
            "plain_text": "",
            "detailed_info": {"error": f"Path does not exist: {path}"}
        }

    if not os.path.isdir(path):
        logging.error(f"Path is not a folder: {path}")
        return {
            "plain_text": "",
            "detailed_info": {"error": f"Path is not a folder: {path}"}
        }

    # Try to generate the folder structure
    try:
        last_folder_name = os.path.basename(os.path.abspath(path))
        logging.debug(f"Processing root folder: {last_folder_name}")
        plain_text_tree = f"The tree structure of the folder is:\n{last_folder_name}/\n"
        json_tree = []

        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)

            # Skip hidden files/directories and __pycache__
            if item.startswith('.') or item == "__pycache__":
                logging.debug(f"Skipping hidden file/directory or __pycache__: {item}")
                continue

            sub_plain, sub_json = build_tree(item_path, level=1)
            plain_text_tree += sub_plain
            if sub_json:  # Add child to JSON root
                json_tree.append(sub_json)

        logging.info(f"Successfully generated folder structure for: {path}")

        # Return combined output
        return {"plain_text": plain_text_tree, "detailed_info": json_tree}
    except Exception as e:
        logging.error(f"Error reading folder: {e}")
        return {
            "plain_text": "",
            "detailed_info": {"error": f"Error reading folder: {e}"}
        }