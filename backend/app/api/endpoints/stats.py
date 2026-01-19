#endpoint 등록
from fastapi import APIRouter, Query
from typing import Optional
from app.services.stats_service import get_registrations

router = APIRouter()

@router.get("/stats/registrations")
def stats_registrations(
    year: Optional[int] = Query(default=None, description="조회 연도"),
    sido_code: Optional[str] = Query(default=None, description="시/도 코드"),
    car_type: Optional[str] = Query(default=None, description="차종 (예: EV)"),
    usage: Optional[str] = Query(default=None, description="용도 (예: PRIVATE)"),
):
    """
    자동차 등록대수 통합 조회 API

    - Query 조건(year, sido_code, car_type, usage)에 따라
      등록대수 데이터를 필터링하여 반환한다.
    - 현재는 더미 데이터 기반이며, 추후 DB 연동 시 repository만 교체한다.
    """
    return get_registrations(year, sido_code, car_type, usage)