from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from Functions.LLM_decision import handle_llm_decision

# Initialize the router
router = APIRouter()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="web_app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Render the homepage with a form for inputting user prompts.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/handle-prompt/", response_class=HTMLResponse)
async def handle_prompt(user_prompt: str = Form(...)):
    """
    Handle a user prompt and render the response as HTML.
    """
    try:
        result = handle_llm_decision(user_prompt)

        html_content = f"""
        <html>
            <head>
                <title>LLM Response</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        margin: 20px;
                    }}
                    pre {{
                        background-color: #f4f4f4;
                        padding: 10px;
                        border: 1px solid #ddd;
                        overflow-x: auto;
                    }}
                    a {{
                        text-decoration: none;
                        color: #007BFF;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                <h1>LLM Response</h1>
                <pre>{result}</pre>
                <a href="/">Back to Home</a>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))