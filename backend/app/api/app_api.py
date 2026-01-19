from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import SessionLocal

app = FastAPI()

# -------------------------
# 요청 1건당 DB 세션
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# 지역 코드/이름 매핑 (DB에 region_code<->name 테이블이 없어서 코드로 고정)
# registrations는 region_name만 있어서, 코드로 필터 들어오면 이름으로 변환해서 조회함
# -------------------------
REGION_CODE_TO_NAME = {
    "11": "서울특별시",
    "41": "경기도",
    "28": "인천광역시",
    "42": "강원도",
    "43": "충청북도",
    "44": "충청남도",
    "30": "대전광역시",
    "36": "세종특별자치시",
    "47": "경상북도",
    "48": "경상남도",
    "27": "대구광역시",
    "31": "울산광역시",
    "26": "부산광역시",
    "45": "전라북도",
    "46": "전라남도",
    "29": "광주광역시",
    "50": "제주특별자치도",
}
REGION_NAME_TO_CODE = {v: k for k, v in REGION_CODE_TO_NAME.items()}


def _yyyymm_from_date_str(date_str: str) -> int:
    # MySQL DATE -> "YYYY-MM-DD"
    y = int(date_str[0:4])
    m = int(date_str[5:7])
    return y * 100 + m


# -------------------------
# 기본
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db/ping")
def db_ping(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"db": "ok"}


# -------------------------
# 1) /regions (실DB 기반 + 매핑)
# - DB에는 region_name만 있어서, region_name을 distinct로 뽑고 code를 매핑
# - 매핑에 없으면 code는 region_name 그대로 반환 (깨지지 않게)
# -------------------------
@app.get("/regions")
def regions(db: Session = Depends(get_db)):
    try:
        rows = db.execute(
            text("SELECT DISTINCT region_name FROM car_registration_stats ORDER BY region_name")
        ).mappings().all()

        result = []
        for r in rows:
            name = r["region_name"]
            code = REGION_NAME_TO_CODE.get(name, name)
            result.append({"code": code, "name": name})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"/regions DB error: {e}")


# -------------------------
# 2) /filters (실DB)
# - years: base_month(date)에서 YEAR 추출
# - car_types: vehicle_type distinct
# - usages: usage_type distinct
# -------------------------
@app.get("/filters")
def filters(db: Session = Depends(get_db)):
    try:
        years = db.execute(
            text("SELECT DISTINCT YEAR(base_month) AS y FROM car_registration_stats ORDER BY y")
        ).mappings().all()
        car_types = db.execute(
            text("SELECT DISTINCT vehicle_type AS v FROM car_registration_stats ORDER BY v")
        ).mappings().all()
        usages = db.execute(
            text("SELECT DISTINCT usage_type AS u FROM car_registration_stats ORDER BY u")
        ).mappings().all()

        return {
            "years": [row["y"] for row in years if row["y"] is not None],
            "car_types": [row["v"] for row in car_types if row["v"] is not None],
            "usages": [row["u"] for row in usages if row["u"] is not None],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"/filters DB error: {e}")


# -------------------------
# 3) /stats/registrations (실DB)
# Query:
# - year (int)  -> YEAR(base_month) 필터
# - sido_code (str) -> region_name로 변환해서 필터
# - car_type (str) -> vehicle_type
# - usage (str) -> usage_type
#
# 응답은 프론트 DTO 형태 유지:
# {
#   "filters": {...},
#   "data": [
#     {
#       "base_month": 202401,
#       "region": {"code":"11","name":"서울특별시"},
#       "vehicle_type":"EV",
#       "usage_type":"PRIVATE",
#       "registration_count": 123
#     }, ...
#   ]
# }
# -------------------------
@app.get("/stats/registrations")
def stats_registrations(
    year: int | None = None,
    sido_code: str | None = None,
    car_type: str | None = None,
    usage: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        where = []
        params = {}

        if year is not None:
            where.append("YEAR(base_month) = :year")
            params["year"] = year

        region_name = None
        if sido_code is not None:
            region_name = REGION_CODE_TO_NAME.get(sido_code, None)
            if region_name is None:
                # 혹시 프론트가 name을 code로 넣는 케이스 방어
                region_name = sido_code
            where.append("region_name = :region_name")
            params["region_name"] = region_name

        if car_type is not None:
            where.append("vehicle_type = :vehicle_type")
            params["vehicle_type"] = car_type

        if usage is not None:
            where.append("usage_type = :usage_type")
            params["usage_type"] = usage

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        # 월 단위 합(같은 월/지역/차종/용도 합산)
        sql = text(f"""
            SELECT
                DATE_FORMAT(base_month, '%Y-%m-%d') AS base_month,
                region_name,
                vehicle_type,
                usage_type,
                SUM(registration_count) AS registration_count
            FROM car_registration_stats
            {where_sql}
            GROUP BY base_month, region_name, vehicle_type, usage_type
            ORDER BY base_month, region_name, vehicle_type, usage_type
        """)

        rows = db.execute(sql, params).mappings().all()

        data = []
        for r in rows:
            name = r["region_name"]
            code = REGION_NAME_TO_CODE.get(name, name)
            base_month_yyyymm = _yyyymm_from_date_str(r["base_month"])
            data.append({
                "base_month": base_month_yyyymm,
                "region": {"code": code, "name": name},
                "vehicle_type": r["vehicle_type"],
                "usage_type": r["usage_type"],
                "registration_count": int(r["registration_count"] or 0),
            })

        return {
            "filters": {"year": year, "sido_code": sido_code, "car_type": car_type, "usage": usage},
            "data": data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"/stats/registrations DB error: {e}")


# -------------------------
# 4) /stats/air-pollution (실DB)
# air_pollution: year, region_code, pollution_degree
# region_code는 smallint라서 "11"처럼 문자열 코드로 포맷
# -------------------------
@app.get("/stats/air-pollution")
def stats_air_pollution(
    year: int | None = None,
    db: Session = Depends(get_db),
):
    try:
        where_sql = ""
        params = {}
        if year is not None:
            where_sql = "WHERE year = :year"
            params["year"] = year

        sql = text(f"""
            SELECT year, region_code, pollution_degree
            FROM air_pollution
            {where_sql}
            ORDER BY year, region_code
        """)

        rows = db.execute(sql, params).mappings().all()

        result = []
        for r in rows:
            code = str(r["region_code"]).zfill(2)  # 11, 41 같은 형태 맞추기
            name = REGION_CODE_TO_NAME.get(code, "")
            result.append({
                "year": int(r["year"]),
                "region": {"code": code, "name": name},
                "pollution_degree": int(r["pollution_degree"] or 0),
            })
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"/stats/air-pollution DB error: {e}")


# -------------------------
# 5) /faqs (실DB)
# faq_table: question, answer, company, category
# 프론트는 source 같은 필드가 있을 수 있어서 company를 source로 내림
# -------------------------
@app.get("/faqs")
def faqs(db: Session = Depends(get_db)):
    try:
        sql = text("""
            SELECT question, answer, company, category
            FROM faq_table
            ORDER BY category, id
        """)
        rows = db.execute(sql).mappings().all()

        return [
            {
                "question": r["question"],
                "answer": r["answer"],
                "source": r["company"],   # company -> source로 내려줌
                "category": r["category"],
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"/faqs DB error: {e}")


# -------------------------
# 6) /stations (실DB)
# station: name, address, latitude, longtitude(오타), type
# 응답에서는 longitude로 정리
# -------------------------
@app.get("/stations")
def get_stations(
    station_type: str | None = None,
    q: str | None = None,
    has_coord: bool = True,
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    try:
        where = []
        params = {}

        if station_type:
            where.append("type = :station_type")
            params["station_type"] = station_type

        if q:
            where.append("name LIKE :q")
            params["q"] = f"%{q}%"

        if has_coord:
            where.append("latitude IS NOT NULL AND longtitude IS NOT NULL")

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        sql = text(f"""
            SELECT id, name, address, latitude, longtitude, type
            FROM station
            {where_sql}
            ORDER BY id DESC
            LIMIT :limit
        """)
        params["limit"] = limit

        rows = db.execute(sql, params).mappings().all()

        return [
            {
                "id": r["id"],
                "name": r["name"],
                "address": r["address"],
                "latitude": r["latitude"],
                "longitude": r["longtitude"],  # DB 컬럼 오타 보정
                "type": r["type"],
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"/stations DB error: {e}")