from fastapi import APIRouter, HTTPException, Request, Form, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from Functions.LLM_decision import llm_decision
from Functions.functions import read_file, list_folder
import os

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="server.log",
    filemode="a",
)

# Initialize router
router = APIRouter()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="web_app/templates")

# Mount static files
router.mount("/static", StaticFiles(directory="web_app/static"), name="static")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Renders the homepage for the web app.
    """
    logging.info("Rendering the homepage.")
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logging.error(f"Error rendering the homepage: {e}")
        raise HTTPException(status_code=500, detail="Error rendering the homepage.")


@router.post("/handle-prompt/", response_class=JSONResponse)
async def handle_prompt(user_prompt: str = Form(...)):
    """
    Handles user prompts and passes them to the LLM for processing.

    Args:
        user_prompt (str): The user-inputted prompt.

    Returns:
        JSONResponse: The result of the LLM decision or an error message.
    """
    logging.info(f"Received user prompt: {user_prompt}")
    try:
        result = llm_decision(user_prompt)
        logging.debug(f"Generated response: {result}")
        return JSONResponse(content={"result": result})
    except Exception as e:
        logging.error(f"Error processing user prompt: {e}")
        return JSONResponse(content={"error": f"Unable to process your request: {e}"}, status_code=500)


@router.get("/preview/", response_class=HTMLResponse)
async def preview_file(path: str = Query(...)):
    """
    Endpoint to preview the content of a file.

    Args:
        path (str): The full path of the file to preview.

    Returns:
        HTMLResponse: The content of the file or an error message.
    """
    logging.info(f"Previewing file: {path}")
    try:
        file_content = read_file(path)
        if "Error" in file_content:
            logging.warning(f"Error in file content for preview: {file_content}")
            return HTMLResponse(content=f"<p>{file_content}</p>", status_code=400)
        logging.debug(f"File content successfully fetched for preview: {path}")
        return HTMLResponse(content=f"<pre>{file_content}</pre>", status_code=200)
    except Exception as e:
        logging.error(f"Error previewing file: {e}")
        return HTMLResponse(content=f"<p>Error: Unable to preview file: {e}</p>", status_code=500)


@router.get("/list-folder/", response_class=JSONResponse)
async def list_folder_route(folder_path: str = Query(...)):
    """
    Endpoint to list the folder structure in plain text and JSON format.

    Args:
        folder_path (str): The path to the folder.

    Returns:
        JSONResponse: Plain text and JSON structure.
    """
    logging.info(f"Listing folder structure for: {folder_path}")
    try:
        folder_data = list_folder(folder_path)
        if "error" in folder_data:
            return JSONResponse(content={"error": folder_data["error"]}, status_code=400)
        
        # Return only plain_text for now
        return JSONResponse(content={"plain_text": folder_data["plain_text"]})
    except Exception as e:
        logging.error(f"Error listing folder: {e}")
        return JSONResponse(content={"error": f"Unable to list folder: {e}"}, status_code=500)


@router.post("/upload-file/", response_class=JSONResponse)
async def upload_file(file: bytes = Form(...), filename: str = Form(...)):
    """
    Endpoint to upload a file for processing.

    Args:
        file (bytes): The file data.
        filename (str): The name of the file.

    Returns:
        JSONResponse: A confirmation message or error message.
    """
    logging.info(f"Uploading file: {filename}")
    try:
        upload_dir = "./uploaded_files/"
        os.makedirs(upload_dir, exist_ok=True)
        with open(os.path.join(upload_dir, filename), "wb") as f:
            f.write(file)
        logging.info(f"File uploaded successfully: {filename}")
        return JSONResponse(content={"message": f"File {filename} uploaded successfully."})
    except Exception as e:
        logging.error(f"Error uploading file: {e}")
        return JSONResponse(content={"error": f"Unable to upload file: {e}"}, status_code=500)


@router.get("/log-history/", response_class=HTMLResponse)
async def log_history():
    """
    Endpoint to retrieve and display the server logs.

    Returns:
        HTMLResponse: The server logs in preformatted text.
    """
    logging.info("Fetching log history.")
    try:
        with open("server.log", "r") as log_file:
            logs = log_file.read()
        return HTMLResponse(content=f"<pre>{logs}</pre>", status_code=200)
    except Exception as e:
        logging.error(f"Error fetching log history: {e}")
        return HTMLResponse(content=f"<p>Error retrieving logs: {e}</p>", status_code=500)


@router.delete("/delete-file/", response_class=JSONResponse)
async def delete_file(path: str = Query(...)):
    """
    Endpoint to delete a specified file.

    Args:
        path (str): The full path of the file to delete.

    Returns:
        JSONResponse: Success message or error message.
    """
    logging.info(f"Attempting to delete file: {path}")
    try:
        if os.path.isfile(path):
            os.remove(path)
            logging.info(f"File deleted successfully: {path}")
            return JSONResponse(content={"message": f"File {path} deleted successfully."})
        else:
            logging.warning(f"File not found for deletion: {path}")
            return JSONResponse(content={"error": f"File {path} not found."}, status_code=404)
    except Exception as e:
        logging.error(f"Error deleting file: {e}")
        return JSONResponse(content={"error": f"Unable to delete file: {e}"}, status_code=500)