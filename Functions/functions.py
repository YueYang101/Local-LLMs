import os
import json
import logging
from docx import Document
import PyPDF2
from LLM_interface.query_llm import (
    preprocess_prompt_with_functions,
    query_llm_function_decision,
    API_URL,
    MODEL_NAME,
    query_llm_marked_response
)
from PyPDF2 import PdfReader
import docx
from Functions.local_formatter import LocalFormatter

def llm_decision(user_prompt: str):
    logging.info("Starting llm_decision function.")

    enriched_prompt = preprocess_prompt_with_functions(user_prompt)
    logging.debug(f"Enriched prompt: {enriched_prompt}")

    # For decision, we do not stream. We need full JSON response.
    llm_response = query_llm_function_decision(API_URL, MODEL_NAME, enriched_prompt, stream=False)
    logging.debug(f"Raw LLM Decision Response: {llm_response}")

    try:
        response_data = json.loads(llm_response)
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
            path = param.get("path", "")

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
                # We'll return a generator (stream) for this response.
                # Instead of returning a dict immediately, let's store a generator.
                # We'll handle the generator in routes.py where we build the StreamingResponse.
                gen = general_question(user_prompt, stream=True)
                results.append({"stream_generator": gen})
            else:
                logging.warning(f"Unknown function '{func}'.")
                results.append({"html_response": f"<p>Error: Unknown function '{func}'</p>"})

        # Combine results
        # If there's a streaming result, we return that directly.
        # If multiple functions are called, let's just combine their HTML.
        # For simplicity, assume only one streaming function per request.
        combined_html_response = ""
        stream_generator = None
        combined_detailed_info = []
        for res in results:
            if "stream_generator" in res:
                stream_generator = res["stream_generator"]
            else:
                html_response = res.get("html_response")
                if html_response:
                    combined_html_response += html_response
                detailed_info = res.get("detailed_info", {})
                if detailed_info:
                    combined_detailed_info.append(detailed_info)

        # If we got a stream generator, return that directly. Otherwise return normal HTML.
        if stream_generator:
            return {
                "stream_generator": stream_generator,
                "detailed_info": combined_detailed_info
            }
        else:
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

def handle_path(path):
    logging.info(f"Starting handle_path function with path: {path}")
    if os.path.isfile(path):
        return {
            "function": ["read_file"],
            "parameters": [{"path": path}]
        }
    elif os.path.isdir(path):
        return {
            "function": ["list_folder"],
            "parameters": [{"path": path}]
        }
    else:
        return {
            "function": ["error"],
            "parameters": [
                {"error_message": f"{path} is neither a valid file nor a folder."}
            ]
        }

def read_file(path: str):
    logging.info(f"Starting read_file function for path: {path}")

    try:
        file_metadata = {"name": os.path.basename(path), "contents": None}
        if path.endswith(".docx"):
            doc = Document(path)
            file_metadata["contents"] = "\n".join([para.text for para in doc.paragraphs])
        elif path.endswith(".pdf"):
            pdf_text = ""
            with open(path, "rb") as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text() or ""
            file_metadata["contents"] = pdf_text.strip()
        elif path.endswith(".py") or path.endswith(".md") or path.endswith(".txt"):
            with open(path, "r", encoding="utf-8") as f:
                file_metadata["contents"] = f.read()
        else:
            return {
                "plain_text_response": f"Unsupported file type: {file_metadata['name']}",
                "detailed_info": file_metadata
            }

        if not file_metadata["contents"]:
            raise Exception("Failed to extract file content.")

        enriched_prompt = f"Explain the following content:\n\n{file_metadata['contents']}"
        # Stream from LLM and format locally
        gen = general_question(enriched_prompt, stream=True)
        return {"stream_generator": gen, "detailed_info": file_metadata}

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
        elif path.endswith(".py") or path.endswith(".md") or path.endswith(".txt"):
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
    logging.info(f"Generating folder structure and content for: {path}")
    import os
    from PyPDF2 import PdfReader

    def read_file_content(file_path: str) -> str:
        try:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            if ext == '.pdf':
                with open(file_path, 'rb') as f:
                    reader = PdfReader(f)
                    return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
            elif ext in {'.txt', '.py', '.js', '.html', '.md'}:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            elif ext == '.docx':
                d = Document(file_path)
                return "\n".join(paragraph.text for paragraph in d.paragraphs)
            return "Unsupported file type for preview."
        except Exception as e:
            return f"Error reading file: {e}"

    def build_tree_and_content(path, level=0):
        indent = "    " * level
        tree_prefix = f"{indent}├── "
        plain_text_structure = ""
        aggregated_content = ""

        if os.path.isdir(path):
            dir_name = os.path.basename(path)
            plain_text_structure += f"{tree_prefix}{dir_name}/\n"
            for item in sorted(os.listdir(path)):
                if item.startswith('.') or item == "__pycache__":
                    continue
                item_path = os.path.join(path, item)
                sub_plain, sub_content = build_tree_and_content(item_path, level + 1)
                plain_text_structure += sub_plain
                aggregated_content += sub_content
        else:
            file_name = os.path.basename(path)
            plain_text_structure += f"{tree_prefix}{file_name}\n"
            file_content = read_file_content(path)
            aggregated_content += f"\n# {file_name}\n{file_content}\n"

        return plain_text_structure, aggregated_content

    if not os.path.exists(path):
        return {"html_response": "<p>Error: Path does not exist.</p>", "detailed_info": {"error": "Path does not exist"}}
    if not os.path.isdir(path):
        return {"html_response": "<p>Error: Path is not a folder.</p>", "detailed_info": {"error": "Path is not a folder"}}

    try:
        folder_structure, aggregated_content = build_tree_and_content(path)
        enriched_prompt = (
            f"Here is the folder structure of a programming project:\n\n{folder_structure}\n\n"
            f"Below are the contents of the files:\n{aggregated_content}\n\n"
            "Explain the overall purpose of the project, key components, and functionality."
        )

        gen = general_question(enriched_prompt, stream=True)
        return {"stream_generator": gen, "detailed_info": {"folder_structure": folder_structure}}

    except Exception as e:
        logging.error(f"Error processing folder: {e}")
        return {"html_response": f"<p>Error: {e}</p>", "detailed_info": {"error": str(e)}}

def general_question(user_prompt, stream=False):
    """
    Handles general questions.
    Streams chunks from the LLM, passes them to local formatter, and yields HTML incrementally.
    """
    logging.info("Starting general_question function.")
    response_chunks = query_llm_marked_response(API_URL, MODEL_NAME, user_prompt, stream=stream)

    if stream:
        formatter = LocalFormatter()
        # As chunks come in, feed them to the formatter and yield the HTML
        for chunk in response_chunks:
            html = formatter.feed_text(chunk)
            if html:
                # Yield incremental formatted HTML
                yield html
        # After all chunks done, close formatter
        final_html = formatter.close()
        if final_html:
            yield final_html
    else:
        # Non-streaming mode: accumulate all chunks and then format once at the end
        all_text = ""
        for chunk in response_chunks:
            all_text += chunk
        formatter = LocalFormatter()
        html = formatter.feed_text(all_text)
        html += formatter.close()
        return {
            "html_response": html,
            "detailed_info": {"type": "general_question", "prompt": user_prompt},
        }