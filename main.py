import uvicorn
from FastAPI.routes import app  # Import the FastAPI app from routes.py

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(app, host="127.0.0.1", port=8000)