from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth
from .manage_env import verify_env_variables
from database import engine
import models

verify_env_variables()

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
