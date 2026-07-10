from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.database import engine


router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "unavailable"},
        )

    return {"status": "ok", "database": "ok"}
