# frontend/api/client.py
from typing import List
from dto.dataset_dto import RegionDTO, RegistrationStatDTO, AirPollutionStatDTO


class MockApiClient:

    @staticmethod
    def get_regions() -> List[RegionDTO]:
        # GeoJSON의 'name' 속성과 일치하도록 풀네임으로 정의
        names = [
            ("11", "서울특별시"), ("41", "경기도"), ("28", "인천광역시"),
            ("42", "강원도"), ("43", "충청북도"), ("44", "충청남도"),
            ("30", "대전광역시"), ("36", "세종특별자치시"), ("47", "경상북도"),
            ("48", "경상남도"), ("27", "대구광역시"), ("31", "울산광역시"),
            ("26", "부산광역시"), ("45", "전라북도"), ("46", "전라남도"),
            ("29", "광주광역시"), ("50", "제주특별자치도")
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
                registration_count=100000 + (i * 5000)
            ) for i, r in enumerate(regions)
        ]

    @staticmethod
    def get_air_pollution_stats() -> List[AirPollutionStatDTO]:
        regions = MockApiClient.get_regions()
        return [
            AirPollutionStatDTO(
                year=2023,
                region=r,
                pollution_degree=20 + (i % 20)
            ) for i, r in enumerate(regions)
        ]