import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import auth

from database import engine
import models


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="User-Guide-Ai-Chatbot-Plugin")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# REGISTER ROUTERS
# ==========================================
app.include_router(auth.router) 

