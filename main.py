import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import os
import asyncio

# Load environment variables
load_dotenv()

# Initialize database
from app.database import init_db
init_db()

# Initialize FastAPI app
app = FastAPI(
    title="LinkedIn Post Automation API",
    description="AI-powered LinkedIn post generation and scheduling API",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to LinkedIn Post Automation API", "docs": "/docs"}

@app.post('/api/generate-content')
async def generate_content(request: Request):
    data = await request.json()
    return {"content": "Generated content", "input": data}

# Include routers from other modules
from app.routers import content, scheduler

app.include_router(content.router)
app.include_router(scheduler.router)

# Initialize post publisher background task
from app.scheduler.publisher import post_publisher

@app.on_event("startup")
async def startup_event():
    # Start the post publisher background task
    asyncio.create_task(post_publisher.start())

@app.on_event("shutdown")
def shutdown_event():
    # Stop the post publisher background task
    post_publisher.stop()

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)