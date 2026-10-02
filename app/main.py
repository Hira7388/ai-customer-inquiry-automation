from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.inquiries import router as inquiries_router

app = FastAPI()
app.include_router(health_router)
app.include_router(inquiries_router)
