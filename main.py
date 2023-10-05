import asyncio

import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter

from src.conf.config import settings
from src.routes.contacts import router as contacts_router
from src.routes.auth import auth_router as auth_router
from src.routes.users import user_router

app = FastAPI()


# @app.on_event("startup")
# async def startup():
#     r = await redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)
#     await FastAPILimiter.init(r)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts_router, tags=["contacts"])
app.include_router(auth_router, tags=["auth"], prefix="/auth")
app.include_router(user_router, tags=["users"], prefix="/users")


async def main():
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)


if __name__ == "__main__":
    asyncio.run(main())
