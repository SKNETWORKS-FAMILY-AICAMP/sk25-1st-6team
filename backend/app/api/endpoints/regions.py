from fastapi import APIRouter
from app.services.region_service import get_regions

router = APIRouter()

@router.get("/regions")
def regions():
    return get_regions()
