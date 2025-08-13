import asyncio
from fastapi import FastAPI
from database import Base, engine
import models
from auth import router as auth_router

app = FastAPI(title="CarWash API")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(auth_router)

@app.get("/")
def root():
    return {"status": "ok"}
