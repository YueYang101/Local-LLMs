from fastapi import APIRouter, HTTPException, Request, Form, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from Functions.LLM_decision import llm_decision
from Functions.functions import read_file, list_folder

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

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
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/handle-prompt/", response_class=JSONResponse)
async def handle_prompt(user_prompt: str = Form(...)):
    """
    Handles user prompts and passes them to the LLM for processing.

    Args:
        user_prompt (str): The user-inputted prompt.

    Returns:
        JSONResponse: The result of the LLM decision or an error message.
    """
    try:
        logging.info(f"Received user prompt: {user_prompt}")
        result = llm_decision(user_prompt)
        logging.debug(f"Generated response: {result}")

        # Return the result in JSON format
        return JSONResponse(content={"result": result})
    except Exception as e:
        logging.error(f"Error processing prompt: {e}")
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
    try:
        logging.info(f"Previewing file: {path}")

        # Read the file content
        file_content = read_file(path)
        if "Error" in file_content:
            return HTMLResponse(content=f"<p>{file_content}</p>", status_code=400)

        # Render the file content as preformatted text
        return HTMLResponse(
            content=f"<pre>{file_content}</pre>",
            status_code=200,
        )
    except Exception as e:
        logging.error(f"Error previewing file: {e}")
        return HTMLResponse(content=f"<p>Error: Unable to preview file: {e}</p>", status_code=500)

@router.get("/list-folder/", response_class=JSONResponse)
async def list_folder_route(folder_path: str = Query(...)):
    """
    Endpoint to list the folder structure with hyperlinks for files.

    Args:
        folder_path (str): The path to the folder.

    Returns:
        JSONResponse: A JSON object containing the folder structure.
    """
    try:
        logging.info(f"Listing folder structure for: {folder_path}")
        folder_structure = list_folder(folder_path, enable_preview=True)
        return JSONResponse(content={"structure": folder_structure})
    except Exception as e:
        logging.error(f"Error listing folder: {e}")
        return JSONResponse(content={"error": f"Unable to list folder: {e}"}, status_code=500)