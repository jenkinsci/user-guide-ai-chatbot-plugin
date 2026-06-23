from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, chat
from manage_env import verify_env_variables
from contextlib import asynccontextmanager
import models
from database import db_engine, Base

verify_env_variables()


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Code executed exactly once before the application starts receiving requests.
    """
    print("[*] Initializing database connection and creating tables...")
    
    async with db_engine.begin() as connection:
        # This will safely create all tables that don't already exist
        await connection.run_sync(Base.metadata.create_all)
        
    print("[+] Database tables are ready!")
    
    # Yield control back to FastAPI to start the server
    yield
    
    print("[*] Shutting down application and closing database engine...")
    await db_engine.dispose()

 
app = FastAPI(title="user-guide-ai-chatbot-plugin",
              lifespan=app_lifespan)

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
app.include_router(chat.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5173, reload=True)
