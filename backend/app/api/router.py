from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/health")
def health():
    return {"status": "ok"}

from app.api.endpoints.regions import router as regions_router
api_router.include_router(regions_router, tags=["Regions"])

#라우터 등록
from app.api.endpoints.stats import router as stats_router
api_router.include_router(stats_router, tags=["Stats"])

from app.api.endpoints.db_ping import router as db_ping_router
api_router.include_router(db_ping_router, tags=["DB"])

from app.api.endpoints.health import router as health_router
api_router.include_router(health_router, tags=["Health"])