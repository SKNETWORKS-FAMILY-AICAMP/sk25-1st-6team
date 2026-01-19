from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
import logging

router = APIRouter()

@router.get("/db/ping")
def db_ping(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"db": "ok"}
    except Exception as e:
        logging.exception("DB ping failed")
        return JSONResponse(
            status_code=500,
            content={"error_type": type(e).__name__, "error": str(e)}
        )