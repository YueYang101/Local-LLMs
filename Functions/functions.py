# uvicorn main:app --host 127.0.0.1 --port 8000 --reload
import os
from docx import Document
import PyPDF2
import json
import logging
from LLM_interface.query_llm import (
    preprocess_prompt_with_functions,
    query_llm_function_decision,
    API_URL,
    MODEL_NAME,
    query_llm_marked_response,
    convert_marked_to_html
)
from PyPDF2 import PdfReader
import docx

def llm_decision(user_prompt: str):
    logging.info("Starting llm_decision function.")

    enriched_prompt = preprocess_prompt_with_functions(user_prompt)
    logging.debug(f"Enriched prompt: {enriched_prompt}")

    # IMPORTANT CHANGE: Now llm_response is a generator if stream=True
    llm_response_chunks = query_llm_function_decision(API_URL, MODEL_NAME, enriched_prompt, stream=True)

    # We need to accumulate the streamed response to parse JSON.
    # The LLM must return JSON for the function decision in the first message.
    decision_text = ""
    for chunk in llm_response_chunks:
        decision_text += chunk
    logging.debug(f"Raw LLM Decision Response: {decision_text}")

    try:
        response_data = json.loads(decision_text)
        logging.info("Successfully parsed LLM response as JSON.")

        functions = response_data.get("function", [])
        parameters = response_data.get("parameters", [])

        if isinstance(functions, str):
            functions = [functions]
        if isinstance(parameters, dict):
            parameters = [parameters]
        if len(functions) != len(parameters):
            raise ValueError("Mismatch between number of functions and parameters.")

        results = []
        for func, param in zip(functions, parameters):
            logging.info(f"Processing function: {func} with parameters: {param}")
            path = param.get("path")

            if func == "handle_path":
                action_response = handle_path(path)
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
                # CHANGED: now get streamed response directly from general_question
                general_response = general_question(user_prompt, stream=True)
                # general_response is a generator yielding chunks of HTML

                # We'll accumulate these chunks:
                streamed_html = ""
                for html_chunk in general_response:
                    streamed_html += html_chunk
                results.append({"html_response": streamed_html})
            else:
                logging.warning(f"Unknown function '{func}'.")
                results.append({"html_response": f"<p>Error: Unknown function '{func}'</p>"})

        combined_html_response = ""
        combined_detailed_info = []
        for res in results:
            if isinstance(res, dict):
                html_response = res.get("html_response")
                if html_response:
                    combined_html_response += html_response
                else:
                    combined_html_response += "<p>No valid response to display.</p>"

                detailed_info = res.get("detailed_info", {})
                if detailed_info:
                    combined_detailed_info.append(detailed_info)

        return {
            "html_response": combined_html_response,
            "detailed_info": combined_detailed_info,
        }

    except json.JSONDecodeError:
        logging.error(f"Error decoding LLM response as JSON: {decision_text}")
        return {
            "html_response": f"<p>Error: Invalid JSON response from LLM. Raw output: {decision_text}</p>",
            "detailed_info": {},
        }
    except Exception as e:
        logging.error(f"Error in llm_decision function: {e}")
        return {
            "html_response": f"<p>Error executing function: {e}</p>",
            "detailed_info": {},
        }

def handle_path(path):
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

import logging
from docx import Document
import PyPDF2

def read_file(path: str):
    logging.info(f"Starting read_file function for path: {path}")

    try:
        file_metadata = {
            "name": os.path.basename(path),
            "contents": None
        }

        if path.endswith(".docx"):
            doc = Document(path)
            file_metadata["contents"] = "\n".join([para.text for para in doc.paragraphs])
        elif path.endswith(".pdf"):
            pdf_text = ""
            with open(path, "rb") as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text() or ""
            file_metadata["contents"] = pdf_text.strip()
        elif path.endswith(".py") or path.endswith(".md"):
            with open(path, "r", encoding="utf-8") as file:
                file_metadata["contents"] = file.read()
        else:
            logging.warning(f"Unsupported file type for: {path}")
            return {
                "plain_text_response": f"Unsupported file type: {file_metadata['name']}",
                "detailed_info": file_metadata
            }

        if not file_metadata["contents"]:
            raise Exception("Failed to extract file content.")

        enriched_prompt = f"Explain the following content:\n\n{file_metadata['contents']}"

        # CHANGED: general_question called with stream=True
        llm_response_chunks = general_question(enriched_prompt, stream=True)
        streamed_html = ""
        for chunk in llm_response_chunks:
            streamed_html += chunk

        return {
            "html_response": streamed_html,
            "detailed_info": file_metadata
        }

    except FileNotFoundError:
        return {
            "html_response": f"<p>Error: File not found at {path}</p>",
            "detailed_info": {"name": os.path.basename(path)}
        }
    except Exception as e:
        return {
            "html_response": f"<p>Error reading file: {e}</p>",
            "detailed_info": {"name": os.path.basename(path)}
        }

def write_file(path: str, content: str):
    logging.info(f"Starting write_file function with path: {path}")
    try:
        if path.endswith(".docx"):
            doc = Document()
            for line in content.split("\n"):
                doc.add_paragraph(line)
            doc.save(path)
        elif path.endswith(".py"):
            with open(path, "w", encoding="utf-8") as file:
                file.write(content)
        elif path.endswith(".pdf"):
            return {
                "plain_text": "Error: Writing to PDF files is not supported.",
                "detailed_info": {"path": path, "file_type": "pdf"},
            }
        else:
            return {
                "plain_text": f"Unsupported file type for writing: {path}",
                "detailed_info": {"path": path},
            }
        return {"plain_text": f"File successfully written to {path}", "detailed_info": {"path": path}}
    except Exception as e:
        return {"plain_text": f"Error writing file: {e}", "detailed_info": {"path": path}}

def list_folder(path: str) -> dict:
    import os, logging, docx
    from PyPDF2 import PdfReader

    logging.info(f"Generating folder structure and content for: {path}")

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
            return f"Error reading file: {e}"

    def build_tree_and_content(path, level=0):
        indent = "    " * level
        tree_prefix = f"{indent}├── "
        plain_text_structure = ""
        html_text_structure = ""
        aggregated_content = ""

        if os.path.isdir(path):
            dir_name = os.path.basename(path)
            plain_text_structure += f"{tree_prefix}{dir_name}/\n"
            html_text_structure += f"{tree_prefix}{dir_name}/\n"

            for idx, item in enumerate(sorted(os.listdir(path))):
                if item.startswith('.') or item == "__pycache__":
                    continue
                item_path = os.path.join(path, item)
                sub_plain, sub_html, sub_content = build_tree_and_content(item_path, level + 1)
                plain_text_structure += sub_plain
                html_text_structure += sub_html
                aggregated_content += sub_content
        else:
            file_name = os.path.basename(path)
            plain_text_structure += f"{tree_prefix}{file_name}\n"
            html_text_structure += f"{tree_prefix}{file_name}\n"
            aggregated_content += f"\n### {file_name}\n{read_file_content(path)}\n"

        return plain_text_structure, html_text_structure, aggregated_content

    if not os.path.exists(path):
        return {"html_response": "<p>Error: Path does not exist.</p>", "detailed_info": {"error": "Path does not exist"}}
    if not os.path.isdir(path):
        return {"html_response": "<p>Error: Path is not a folder.</p>", "detailed_info": {"error": "Path is not a folder"}}

    try:
        folder_structure, html_tree_structure, aggregated_content = build_tree_and_content(path)
        enriched_prompt = (
            f"Here is the folder structure of a programming project:\n\n{folder_structure}\n\n"
            f"Below are the contents of the files:\n{aggregated_content}\n\n"
            "Explain the overall purpose of the project, key components, and functionality."
        )

        # general_question with stream=True
        llm_response_chunks = general_question(enriched_prompt, stream=True)

        streamed_html = ""
        for chunk in llm_response_chunks:
            streamed_html += chunk

        combined_html_response = (
            "<h2>Folder Structure</h2>\n<pre>\n" + html_tree_structure + "</pre>\n" +
            "<h2>Explanation</h2>\n" + streamed_html
        )

        return {
            "html_response": combined_html_response,
            "detailed_info": {"folder_structure": folder_structure}
        }

    except Exception as e:
        logging.error(f"Error processing folder: {e}")
        return {"html_response": f"<p>Error: {e}</p>", "detailed_info": {"error": str(e)}}

def general_question(user_prompt, stream=False):
    from LLM_interface.query_llm import query_llm_marked_response, convert_marked_to_html

    # query_llm_marked_response now returns a generator if stream=True
    response_chunks = query_llm_marked_response(API_URL, MODEL_NAME, user_prompt, stream=stream)

    # If streaming, yield converted chunks as they arrive:
    if stream:
        # Each chunk might be partial text. We convert incrementally:
        # For simplicity, we'll accumulate and convert at the end of each chunk,
        # but better approach might be to handle partial markers carefully.
        # Here, just yield raw text and convert after all chunks:
        # Actually, let's just yield raw text first and convert after accumulation in calling functions.
        accumulated = ""
        for chunk in response_chunks:
            accumulated += chunk
            # We won't convert until the caller finishes accumulating.
            # Just yield the chunk raw for now.
            # The caller does the conversion after fully accumulated.
        # After done, convert once:
        html_response = convert_marked_to_html(accumulated)
        yield html_response
    else:
        # Not streaming
        llm_response = ""
        for chunk in response_chunks:
            llm_response += chunk
        html_response = convert_marked_to_html(llm_response)
        return {
            "html_response": html_response,
            "detailed_info": {"type": "general_question", "prompt": user_prompt},
        }