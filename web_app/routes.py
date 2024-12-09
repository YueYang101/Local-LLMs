from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from Functions.functions import llm_decision

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
        # Log rendering attempt
        logging.debug("Attempting to render index.html with Jinja2 templates.")
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
        # Log the start of the LLM decision-making process
        logging.debug("Calling llm_decision function with user prompt.")
        decision = llm_decision(user_prompt)
        logging.debug(f"LLM decision result: {decision}")

        # Validate decision structure
        if not isinstance(decision, dict):
            logging.warning("LLM decision result is not a dictionary. Unexpected format.")
            raise ValueError("Invalid response format from LLM decision function.")

        # Check if the decision contains the 'html_response' key
        if "html_response" in decision:
            logging.info("HTML response key detected in LLM decision result.")
            logging.debug(f"HTML Response: {decision.get('html_response')}")
            return JSONResponse(content={
                "html_response": decision.get("html_response"),
                "detailed_info": decision.get("detailed_info", {})  # Pass the JSON structure if available
            })
        else:
            # Log missing 'html_response' key
            logging.warning("'html_response' key not found in LLM decision result.")
            logging.debug(f"Fallback decision content: {decision}")
            return JSONResponse(content={"result": decision})
    except ValueError as ve:
        logging.error(f"ValueError during processing: {ve}")
        return JSONResponse(content={"error": f"Invalid response format: {ve}"}, status_code=500)
    except Exception as e:
        logging.error(f"Error processing user prompt: {e}")
        return JSONResponse(content={"error": f"Unable to process your request: {e}"}, status_code=500)