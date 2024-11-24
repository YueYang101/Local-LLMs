import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from web_app.routes import router
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize FastAPI app
app = FastAPI(title="File Interaction Assistant API", version="1.0")

# Include the router
app.include_router(router)

# Mount static files
app.mount("/static", StaticFiles(directory="web_app/static"), name="static")

@app.on_event("startup")
async def startup_event():
    logging.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Application shutdown.")

if __name__ == "__main__":
    try:
        logging.info("Starting the server...")
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        logging.error(f"Failed to start the server: {e}")