# frontend/api/client.py
import requests
from typing import List, Optional

from dto.dataset_dto import RegionDTO, RegistrationStatDTO, AirPollutionStatDTO, FaqDTO


class MockApiClient:
    BASE_URL = "http://127.0.0.1:8000"  # ✅ 팀 서버 주소로 변경
    TIMEOUT_SEC = 5

    @staticmethod
    def get_regions() -> List[RegionDTO]:
        names = [
            ("11", "서울특별시"), ("41", "경기도"), ("28", "인천광역시"),
            ("42", "강원도"), ("43", "충청북도"), ("44", "충청남도"),
            ("30", "대전광역시"), ("36", "세종특별자치시"), ("47", "경상북도"),
            ("48", "경상남도"), ("27", "대구광역시"), ("31", "울산광역시"),
            ("26", "부산광역시"), ("45", "전라북도"), ("46", "전라남도"),
            ("29", "광주광역시"), ("50", "제주특별자치도"),
        ]
        return [RegionDTO(code=c, name=n) for c, n in names]

    @staticmethod
    def get_registration_stats() -> List[RegistrationStatDTO]:
        regions = MockApiClient.get_regions()
        return [
            RegistrationStatDTO(
                base_month=202401,
                region=r,
                vehicle_type="EV",
                usage_type="PRIVATE",
                registration_count=100000 + (i * 5000),
            )
            for i, r in enumerate(regions)
        ]

    @staticmethod
    def get_air_pollution_stats() -> List[AirPollutionStatDTO]:
        regions = MockApiClient.get_regions()
        return [
            AirPollutionStatDTO(
                year=2023,
                region=r,
                pollution_degree=20 + (i % 20),
            )
            for i, r in enumerate(regions)
        ]

    @staticmethod
    def get_stations(
        car_kind: str,
        n: int = 12,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
    ):
        """
        ✅ 서버에 충전소 목록을 요청 (선택적으로 사용자 위치 lat/lng 전달)
        실패하면 더미로 fallback.

        서버 요청:
          GET {BASE_URL}/stations?kind=EV|H2&limit=12&lat=...&lng=...

        반환 예:
        {
          "id": int,
          "name": str,
          "address": str,
          "distance_m": int,
          "latitude": float|None,
          "longitude": float|None
        }
        """
        kind_param = "EV" if car_kind == "전기차" else "H2"
        url = f"{MockApiClient.BASE_URL}/stations"

        params = {"kind": kind_param, "limit": n}
        if user_lat is not None and user_lng is not None:
            params["lat"] = user_lat
            params["lng"] = user_lng

        try:
            resp = requests.get(url, params=params, timeout=MockApiClient.TIMEOUT_SEC)
            resp.raise_for_status()
            data = resp.json()

            # 서버가 {"items":[...]} 형태 or [...] 형태 등 다양한 케이스 대응
            if isinstance(data, dict):
                items = data.get("items") or data.get("stations") or data.get("data") or []
            else:
                items = data

            results = []
            for i, item in enumerate(items):
                results.append(
                    {
                        "id": item.get("id", i + 1),
                        "name": item.get("name", f"{car_kind} 충전소 {i+1}"),
                        "address": item.get("address", ""),
                        "distance_m": int(item.get("distance_m", 0) or 0),
                        "latitude": item.get("latitude", item.get("lat")),
                        "longitude": item.get("longitude", item.get("lng")),
                    }
                )

            if not results:
                return MockApiClient._fallback_dummy_stations(car_kind=car_kind, n=n)

            return results

        except Exception:
            return MockApiClient._fallback_dummy_stations(car_kind=car_kind, n=n)

    @staticmethod
    def _fallback_dummy_stations(car_kind: str, n: int = 12):
        base = "전기차" if car_kind == "전기차" else "수소차"
        return [
            {
                "id": i + 1,
                "name": f"{base} 충전소 {i+1}",
                "address": f"서울특별시 강남구 테헤란로 {123 + i*7}",
                "distance_m": 120 + i * 180,
                "latitude": None,
                "longitude": None,
            }
            for i in range(n)
        ]

    @staticmethod
    def get_faqs() -> List[FaqDTO]:
        return [
            FaqDTO(
                question="무공해차 보조금은 누구나 받을 수 있나요?",
                answer=(
                    "보조금은 지자체/국비 예산, 차종, 신청 시기, 개인/법인 여부 등에 따라 달라집니다. "
                    "일반적으로 구매(또는 출고) 조건을 충족하고 예산이 남아있을 때 신청 가능합니다."
                ),
                source="환경부 무공해차 통합누리집",
                category="보조금",
            ),
            FaqDTO(
                question="보조금 신청은 언제, 어디서 하나요?",
                answer=(
                    "보통 차량 구매 계약 후 제조사/대리점 안내에 따라 지자체 접수 절차가 진행됩니다. "
                    "지자체별 공고 일정과 서류가 다를 수 있어 해당 지자체 공고를 확인하는 것이 좋습니다."
                ),
                source="지자체 공고 / 무공해차 통합누리집",
                category="신청절차",
            ),
            FaqDTO(
                question="전기차 충전은 얼마나 걸리나요?",
                answer=(
                    "충전 시간은 충전기 종류(완속/급속), 차량 배터리 용량, 잔량에 따라 달라집니다. "
                    "급속은 보통 짧은 시간에 일정 수준까지 충전이 가능하지만, 80% 이후는 속도가 느려질 수 있습니다."
                ),
                source="제조사 안내 / 충전 인프라 안내",
                category="충전",
            ),
            FaqDTO(
                question="수소차는 어디서 충전하나요?",
                answer=(
                    "수소충전소는 지역별로 분포가 다르며, 운영시간/점검 일정에 따라 이용 가능 여부가 달라질 수 있습니다. "
                    "출발 전 운영 여부를 확인하시는 것을 권장합니다."
                ),
                source="수소충전소 안내",
                category="충전",
            ),
            FaqDTO(
                question="전기차 배터리는 얼마나 오래 쓰나요?",
                answer=(
                    "배터리 수명은 사용 환경과 충전 습관에 따라 달라집니다. "
                    "대부분 제조사는 배터리 보증을 제공하므로 차량별 보증 조건을 확인해 주세요."
                ),
                source="제조사 보증 정책",
                category="차량/배터리",
            ),
        ]
