from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from Functions.LLM_decision import llm_decision

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
    Handles user prompts, passes them to the LLM for processing,
    and triggers appropriate functions based on the LLM decision.

    Args:
        user_prompt (str): The user-inputted prompt.

    Returns:
        JSONResponse: The result from the LLM or any triggered function.
    """
    logging.info(f"Received user prompt: {user_prompt}")
    try:
        # Pass input to LLM decision function
        decision = llm_decision(user_prompt)
        logging.debug(f"LLM decision result: {decision}")

        # Directly return the LLM decision for now
        return JSONResponse(content={"result": decision})
    except Exception as e:
        logging.error(f"Error processing user prompt: {e}")
        return JSONResponse(content={"error": f"Unable to process your request: {e}"}, status_code=500)