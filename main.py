from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
from starlette.responses import HTMLResponse

from api.search_router import router as search_router
from api.search_with_gemini import router as gemini_router

# Configure logging for Vercel (simplified)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Price Finder",
    description="Compare prices across the web and find the best deals",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, prefix="/api")
app.include_router(gemini_router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("index.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Welcome to Smart Price Finder</h1>", status_code=200)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
    

# if __name__ == "__main__":
    
#     port = int(os.environ.get("PORT", 8000))
#     host = os.environ.get("HOST", "0.0.0.0")
    
#     logger.info(f"Starting server on {host}:{port}")
    
#     uvicorn.run(
#         "main:app",
#         host=host,
#         port=port,
#         reload=True,
#         log_level="info",
#         access_log=True
#     )
