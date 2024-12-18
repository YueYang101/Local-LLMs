from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from Functions.functions import llm_decision
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="server.log",
    filemode="a",
)

router = APIRouter()
router.mount("/static", StaticFiles(directory="web_app/static"), name="static")

@router.get("/")
async def home(request: Request):
    try:
        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="web_app/templates")
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logging.error(f"Error rendering the homepage: {e}")
        raise HTTPException(status_code=500, detail="Error rendering the homepage.")


@router.post("/handle-prompt/")
async def handle_prompt(user_prompt: str = Form(...)):
    logging.info(f"Received user prompt: {user_prompt}")

    # Currently llm_decision returns a dict with "html_response".
    # We'll just stream this final response as a single chunk.
    # For real-time token streaming, refactor llm_decision to yield chunks.
    
    def response_generator():
        decision = llm_decision(user_prompt)
        html_response = decision.get("html_response", "<p>No content</p>")
        yield html_response

    return StreamingResponse(response_generator(), media_type="text/html")