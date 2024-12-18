# uvicorn main:app --host 127.0.0.1 --port 8000 --reload

import os
from docx import Document
import PyPDF2
import json
import logging
from LLM_interface.query_llm import preprocess_prompt_with_functions, query_llm_function_decision, API_URL, MODEL_NAME, query_llm_marked_response, convert_marked_to_html
from PyPDF2 import PdfReader
import docx

# ========================
# LLM DECISION FUNCTION
# ========================
def llm_decision(user_prompt: str):
    """
    Decides which functions to execute based on the LLM response and processes results.

    Args:
        user_prompt (str): The user's input or request.

    Returns:
        dict: Combined HTML response and detailed information.
    """
    logging.info("Starting llm_decision function.")

    # Preprocess the prompt
    enriched_prompt = preprocess_prompt_with_functions(user_prompt)
    logging.debug(f"Enriched prompt: {enriched_prompt}")

    # Query the LLM for a decision
    llm_response = query_llm_function_decision(API_URL, MODEL_NAME, enriched_prompt, stream=False)
    logging.debug(f"Raw LLM Response: {llm_response}")

    try:
        # Parse LLM response as JSON
        response_data = json.loads(llm_response)
        logging.info("Successfully parsed LLM response as JSON.")

        # Extract functions and parameters
        functions = response_data.get("function", [])
        parameters = response_data.get("parameters", [])

        # Ensure correct format for functions and parameters
        if isinstance(functions, str):
            functions = [functions]
        if isinstance(parameters, dict):
            parameters = [parameters]
        if len(functions) != len(parameters):
            raise ValueError("Mismatch between number of functions and parameters.")

        # Process functions and store results
        results = []
        for func, param in zip(functions, parameters):
            logging.info(f"Processing function: {func} with parameters: {param}")
            path = param.get("path")

            if func == "handle_path":
                action_response = handle_path(path)
                logging.debug(f"Action response from handle_path: {action_response}")

                for action_func, action_param in zip(action_response.get("function", []), action_response.get("parameters", [])):
                    if action_func == "read_file":
                        results.append(read_file(**action_param))
                    elif action_func == "list_folder":
                        results.append(list_folder(**action_param))
                    else:
                        results.append({"html_response": f"<p>Unknown action '{action_func}'</p>"})

            elif func == "read_file":
                results.append(read_file(**param))
            elif func == "write_file":
                results.append(write_file(**param))
            elif func == "list_folder":
                results.append(list_folder(**param))
            elif func == "general_question":
                # Use the HTML response directly
                general_response = general_question(user_prompt)
                results.append(general_response)  # Already includes 'html_response'
            else:
                logging.warning(f"Unknown function '{func}'.")
                results.append({"html_response": f"<p>Error: Unknown function '{func}'</p>"})

        # Combine results: Use pre-converted HTML responses directly
        combined_html_response = ""
        combined_detailed_info = []

        for res in results:
            if isinstance(res, dict):
                # Directly check for 'html_response'
                html_response = res.get("html_response")
                if html_response:
                    combined_html_response += html_response
                else:
                    logging.warning("No HTML response found. Using fallback.")
                    combined_html_response += "<p>No valid response to display.</p>"

                # Collect detailed info
                detailed_info = res.get("detailed_info", {})
                if detailed_info:
                    combined_detailed_info.append(detailed_info)

        # Log final outputs
        logging.debug(f"Combined HTML Response: {combined_html_response}")
        logging.debug(f"Combined Detailed Info: {combined_detailed_info}")

        logging.info("Successfully processed all functions.")
        return {
            "html_response": combined_html_response,
            "detailed_info": combined_detailed_info,
        }

    except json.JSONDecodeError:
        logging.error(f"Error decoding LLM response as JSON: {llm_response}")
        return {
            "html_response": f"<p>Error: Invalid JSON response from LLM. Raw output: {llm_response}</p>",
            "detailed_info": {},
        }
    except Exception as e:
        logging.error(f"Error in llm_decision function: {e}")
        return {
            "html_response": f"<p>Error executing function: {e}</p>",
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
import os
import logging
from docx import Document
import PyPDF2

def read_file(path: str):
    logging.info(f"Starting read_file function for path: {path}")

    try:
        # Log initial metadata setup
        logging.debug("Initializing file metadata.")
        file_metadata = {
            "name": os.path.basename(path),
            "contents": None
        }

        # File type detection and content extraction
        if path.endswith(".docx"):
            logging.info("Detected .docx file. Attempting to read content.")
            try:
                doc = Document(path)
                file_metadata["contents"] = "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                logging.error(f"Error reading .docx file: {e}")
                raise
        elif path.endswith(".pdf"):
            logging.info("Detected .pdf file. Attempting to read content.")
            try:
                pdf_text = ""
                with open(path, "rb") as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    for page in pdf_reader.pages:
                        pdf_text += page.extract_text() or ""
                file_metadata["contents"] = pdf_text.strip()
            except Exception as e:
                logging.error(f"Error reading .pdf file: {e}")
                raise
        elif path.endswith(".py"):
            logging.info("Detected .py file. Attempting to read content.")
            try:
                with open(path, "r", encoding="utf-8") as file:
                    file_metadata["contents"] = file.read()
            except Exception as e:
                logging.error(f"Error reading .py file: {e}")
                raise
        elif path.endswith(".md") or file_metadata["name"].lower() == "readme.md":
            logging.info("Detected .md (Markdown) file. Attempting to read content.")
            try:
                with open(path, "r", encoding="utf-8") as file:
                    file_metadata["contents"] = file.read()
            except Exception as e:
                logging.error(f"Error reading .md file: {e}")
                raise
        else:
            logging.warning(f"Unsupported file type for: {path}")
            return {
                "plain_text_response": f"Unsupported file type: {file_metadata['name']}",
                "detailed_info": file_metadata
            }

        # Check if content extraction was successful
        if not file_metadata["contents"]:
            logging.error(f"Failed to extract content from file: {path}")
            raise Exception("Failed to extract file content.")

        logging.info(f"Successfully read content from file: {file_metadata['name']}")

        # Prepare the enriched prompt
        logging.info("Preparing to query the LLM with file content.")
        enriched_prompt = f"Explain the following content:\n\n{file_metadata['contents']}"
        logging.debug(f"Enriched Prompt:\n{enriched_prompt}")

        # Query the LLM for marked plain-text response
        logging.info("Querying the LLM for marked plain-text explanation.")
        llm_response = general_question(enriched_prompt)  # Returns a dict with "html_response"

        # Log the raw LLM response
        logging.debug(f"Raw LLM Response: {repr(llm_response)}")

        # Validate and handle the LLM response
        if isinstance(llm_response, dict):
            html_response = llm_response.get("html_response", "")
            if not html_response.strip():
                logging.warning("No valid html_response found in LLM result.")
                html_response = "<p>Error: No valid explanation provided.</p>"
        else:
            logging.warning("LLM response did not return a valid dictionary format.")
            html_response = "<p>Error: LLM response format invalid.</p>"

        # Return html_response and detailed info
        logging.info(f"LLM successfully explained the file: {file_metadata['name']}")
        return {
            "html_response": html_response,
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
import os
import logging
import docx
from PyPDF2 import PdfReader

def list_folder(path: str) -> dict:
    """
    Lists the structure of the folder, extracts file contents, 
    and queries the LLM to explain the project structure and files.

    Args:
        path (str): The path to the folder.

    Returns:
        dict: A JSON structure containing 'html_response' and 'detailed_info'.
    """
    logging.info(f"Generating folder structure and content for: {path}")

    # Helper function to read file content
    def read_file_content(file_path: str) -> str:
        try:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

            if ext == '.pdf':
                with open(file_path, 'rb') as f:
                    reader = PdfReader(f)
                    return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

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

    # Helper function to build tree structure and aggregate file content
    def build_tree_and_content(path, level=0):
        indent = "    " * level
        prefix = f"{indent}├── "
        plain_text_structure = ""
        aggregated_content = ""

        if os.path.isdir(path):
            dir_name = os.path.basename(path)
            plain_text_structure += f"{prefix}{dir_name}/\n"

            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if item.startswith('.') or item == "__pycache__":
                    continue

                sub_tree, sub_content = build_tree_and_content(item_path, level + 1)
                plain_text_structure += sub_tree
                aggregated_content += sub_content
        else:
            file_name = os.path.basename(path)
            plain_text_structure += f"{prefix}{file_name}\n"
            aggregated_content += f"\n### {file_name}\n{read_file_content(path)}\n"

        return plain_text_structure, aggregated_content

    # Validate the folder path
    if not os.path.exists(path):
        return {"html_response": "<p>Error: Path does not exist.</p>", "detailed_info": {"error": "Path does not exist"}}
    if not os.path.isdir(path):
        return {"html_response": "<p>Error: Path is not a folder.</p>", "detailed_info": {"error": "Path is not a folder"}}

    try:
        # Generate tree structure and aggregate file content
        folder_structure, aggregated_content = build_tree_and_content(path)

        # Combine tree and content for LLM prompt
        enriched_prompt = (
            f"Here is the folder structure of a programming project:\n\n{folder_structure}\n\n"
            f"Below are the contents of the files:\n{aggregated_content}\n\n"
            "Explain the overall purpose of the project, key components, and functionality."
        )

        logging.info("Querying the LLM with folder structure and content.")
        llm_response = general_question(enriched_prompt)

        # Process LLM response
        html_response = llm_response.get("html_response", "") if isinstance(llm_response, dict) else llm_response
        if not html_response.strip():
            html_response = "<p>No explanation provided by the LLM.</p>"

        return {
            "html_response": html_response,
            "detailed_info": {"folder_structure": folder_structure}
        }

    except Exception as e:
        logging.error(f"Error processing folder: {e}")
        return {"html_response": f"<p>Error: {e}</p>", "detailed_info": {"error": str(e)}}
    
# ========================
# General Question with HTML conversion
# ========================
def general_question(user_prompt, stream=False):
    """
    Handles general knowledge questions by querying the LLM and converting marked responses to HTML.
    """
    logging.info("Handling general question.")

    # Query the LLM
    marked_response = query_llm_marked_response(API_URL, MODEL_NAME, user_prompt, stream=stream)
    logging.debug(f"Raw Marked Response: {repr(marked_response)}")

    # Extract and validate response
    if isinstance(marked_response, dict):
        marked_response = marked_response.get("html_response", "Error: Missing 'html_response' key in response.")
        logging.debug(f"Extracted 'html_response': {repr(marked_response)}")

    if not isinstance(marked_response, str) or not marked_response.strip():
        logging.error("Invalid or empty LLM response received.")
        return {"html_response": "Error: Invalid or empty LLM response.", "detailed_info": {}}

    # Convert marked response to HTML
    html_response = convert_marked_to_html(marked_response)
    logging.debug(f"Converted HTML Response: {html_response}")

    return {
        "html_response": html_response,
        "detailed_info": {"type": "general_question", "prompt": user_prompt},
    }