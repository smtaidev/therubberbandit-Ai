from fastapi import FastAPI
from App.services.extraction.extract_route import router as extraction_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
              title="Document-AI FastAPI", 
              version="1.0.0"
              )

app.include_router(extraction_router)