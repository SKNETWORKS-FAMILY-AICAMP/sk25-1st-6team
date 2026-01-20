from typing import Optional
from app.repositories.stats_repository import find_registrations

def _filter(items: list[dict], key: str, value):
    """
    공통 필터 함수
    - value가 None이면 필터링하지 않고 그대로 반환
    - value가 있으면 해당 key의 값이 일치하는 데이터만 반환
    """
    if value is None:
        return items
    return [x for x in items if x.get(key) == value]

def get_registrations(
    year: Optional[int] = None,
    sido_code: Optional[str] = None,
    car_type: Optional[str] = None,
    usage: Optional[str] = None,
):
    """
    자동차 등록대수 조회 서비스

    Query 조건(year, sido_code, car_type, usage)에 따라
    더미 등록대수 데이터를 필터링하여 반환한다.

    ※ 현재는 더미 데이터 기반이며,
      추후 DB 연동 시 repository만 교체하면 된다.
    """
    # 1. 전체 등록대수 데이터 조회 (현재는 더미 데이터)
    data = find_registrations()

    # 2. Query 파라미터별 필터 적용
    data = _filter(data, "year", year)
    data = _filter(data, "sido_code", sido_code)
    data = _filter(data, "car_type", car_type)
    data = _filter(data, "usage", usage)

    # 3. 필터링된 결과 반환
    return data