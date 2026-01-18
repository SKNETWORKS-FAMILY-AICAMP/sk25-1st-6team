# frontend/dto/dataset_dto.py
from typing import List, Optional
from pydantic import BaseModel


# -----------------------
# 1. 시/도 목록 (/regions)
# -----------------------
class RegionDTO(BaseModel):
    code: str
    name: str


# ----------------------------------------
# 2. 자동차 등록대수 (/stats/registrations)
# ----------------------------------------
class RegistrationStatDTO(BaseModel):
    base_month: int
    region: RegionDTO
    vehicle_type: str          # EV, HYBRID, ICE 등
    usage_type: str             # PRIVATE, COMMERCIAL
    registration_count: int


# ----------------------------------------
# 3. 대기질 통계 (/stats/air)
# ----------------------------------------
class AirPollutionStatDTO(BaseModel):
    year: int
    region: RegionDTO
    pollution_degree: int


class FaqDTO(BaseModel):
    question: str
    answer: str
    source: str
    category: str


# ----------------------------------------
# 4. 충전소 (/stations)
# ----------------------------------------
class StationDTO(BaseModel):
    station_id: str
    name: str
    address: str
    region: RegionDTO
    lat: float
    lng: float
    type: str

class StationListResponseDTO(BaseModel):
    page: int
    size: int
    total: int
    data: List[StationDTO]


# ----------------------------------------
# 5. 보조금 계산 (/subsidies/calc)
# ----------------------------------------
class SubsidyCalcDTO(BaseModel):
    year: int
    sido_code: str
    car_type: str
    model_code: str
    buyer_type: str
    subsidy_national: int
    subsidy_local: int
    subsidy_total: int