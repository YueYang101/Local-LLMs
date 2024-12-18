from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging
from Functions.functions import llm_decision

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="server.log",
    filemode="a",
)

router = APIRouter()
router.mount("/static", StaticFiles(directory="web_app/static"), name="static")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="web_app/templates")
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/handle-prompt/", response_class=JSONResponse)
async def handle_prompt(user_prompt: str = Form(...)):
    logging.info(f"handle_prompt: Received user prompt: {user_prompt}")
    decision = llm_decision(user_prompt)

    if "stream_generator" in decision:
        logging.info("handle_prompt: Streaming response detected.")

        async def stream_response():
            try:
                for chunk in decision["stream_generator"]:
                    # Split the chunk into words
                    words = chunk.split()
                    for word in words:
                        yield f"{word} "  # Send each word followed by a space
                logging.info("handle_prompt: Finished streaming all chunks.")
            except Exception as e:
                logging.error(f"handle_prompt: Error during streaming: {e}")
                yield f"<p>Error: {str(e)}</p>"

        return StreamingResponse(stream_response(), media_type="text/html")
    else:
        logging.info("handle_prompt: Returning normal JSON response.")
        return JSONResponse(content={
            "html_response": decision.get("html_response", ""),
            "detailed_info": decision.get("detailed_info", {})
        })