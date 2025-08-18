from fastapi import FastAPI
from App.services.extraction.extract_route import router as extraction_router
from fastapi.middleware.cors import CORSMiddleware
from App.services.rating.rating_route import router as rating_router
from App.services.chatbot.chatbot_routes import router as chatbot_router

app = FastAPI(
              title="Document-AI FastAPI", 
              version="1.0.0"
              )

app.include_router(extraction_router)
app.include_router(rating_router)
app.include_router(chatbot_router)