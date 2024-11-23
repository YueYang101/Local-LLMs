from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from Functions.LLM_decision import handle_llm_decision
import logging

# Initialize FastAPI app
app = FastAPI(title="File Interaction Assistant API", version="1.0")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Serve static files (if needed)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logging.warning(f"Static directory not found: {e}")

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Render the homepage with a form for inputting user prompts.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/handle-prompt/", summary="Handle LLM Prompt", description="Processes a prompt and returns the LLM's response.")
async def handle_prompt(user_prompt: str = Form(...)):
    """
    Handle a user prompt and return the LLM's response.
    """
    try:
        logging.info(f"Received prompt: {user_prompt}")
        result = handle_llm_decision(user_prompt)
        return {"result": result}
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")