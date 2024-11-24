from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from Functions.LLM_decision import handle_llm_decision

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
    logging.info("Rendering the homepage.")
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/handle-prompt/", response_class=JSONResponse)
async def handle_prompt(user_prompt: str = Form(...)):
    try:
        logging.info(f"Received user prompt: {user_prompt}")
        result = handle_llm_decision(user_prompt)
        logging.debug(f"Generated response: {result}")

        # Return the result in JSON format
        return JSONResponse(content={"result": result})
    except Exception as e:
        logging.error(f"Error processing prompt: {e}")
        return JSONResponse(content={"error": f"Unable to process your request: {e}"}, status_code=500)