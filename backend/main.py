from fastapi.middleware.cors import CORSMiddleware
from routers import auth, chat, message, context
from manage_env import verify_env_variables, get_env_as_list, get_env
from contextlib import asynccontextmanager
from database import db_engine, Base
from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

verify_env_variables()

ALLOW_ORIGINS = get_env_as_list("ALLOW_ORIGINS")
POSTGRES_URL = get_env("POSTGRES_URL")


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Code executed exactly once before the application starts receiving requests.
    """
    print("[*] Initializing database connection and creating tables...")

    async with db_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    print("[+] Database tables are ready!")

    print("[*] Initializing LangGraph checkpointer...")

    # Open the AsyncConnectionPool using a context manager.
    # The pool remains open while the application runs (during the yield).
    async with AsyncConnectionPool(
        conninfo=POSTGRES_URL.replace("+asyncpg", ""),
        max_size=20,
        kwargs={"autocommit": True},
    ) as checkpointer_pool:

        checkpointer = AsyncPostgresSaver(
            conn=checkpointer_pool
        )  # pyright: ignore[reportArgumentType]

        await checkpointer.setup()

        app.state.agent_checkpointer = checkpointer
        print("[+] LangGraph checkpointer is ready!")

        yield

    print("[*] Shutting down application and closing database engine...")
    await db_engine.dispose()
    print("[+] Shutdown complete!")


app = FastAPI(title="user-guide-ai-chatbot-plugin", lifespan=app_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# REGISTER ROUTERS
# ==========================================
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(message.router)
app.include_router(context.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
