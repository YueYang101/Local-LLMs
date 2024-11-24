import uvicorn
from fastapi import FastAPI
from web_app.routes import router

# Initialize FastAPI app
app = FastAPI(title="File Interaction Assistant API", version="1.0")

# Include the router from routes.py
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)