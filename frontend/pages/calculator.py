import streamlit as st
from typing import List, Dict, Optional, Union

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="내 지자체 보조금 알아보기", layout="wide")

# -----------------------------
# Constants / Options
# -----------------------------
YEARS = list(range(2026, 2031))  # 2026 ~ 2030 (5개 이상)

DO_OPTIONS = [
    "- 선택 -",
    "경기도", "강원특별자치도", "경상남도", "경상북도",
    "전라남도", "전북특별자치도", "충청남도", "충청북도", "제주특별자치도"
]

SI_OPTIONS = [
    "- 선택 -",
    "서울특별시", "부산광역시", "대구광역시", "인천광역시",
    "광주광역시", "대전광역시", "울산광역시", "세종특별자치시"
]

CAR_KIND_OPTIONS = ["전기차", "수소차"]

# -----------------------------
# Subsidy Table (예시 더미)
# - 실제로는 '첨부 표' 기반으로 이 dict를 교체/확장하시면 됩니다.
# - 값이 범위인 경우: 문자열로 "200~484" 형태 유지
# -----------------------------
# 정책(범위값): "당신의 예상 보조금은 200~484만원입니다." 처럼 범위 그대로 표시합니다.
SUBSIDY_MAP: Dict[str, Dict[str, Union[int, str]]] = {
    "서울특별시": {"전기차": "200~484", "수소차": 300},
    "부산광역시": {"전기차": 260, "수소차": 320},
    "대구광역시": {"전기차": 240, "수소차": 310},
    "인천광역시": {"전기차": 250, "수소차": 330},
    "광주광역시": {"전기차": 230, "수소차": 305},
    "대전광역시": {"전기차": 245, "수소차": 315},
    "울산광역시": {"전기차": 255, "수소차": 325},
    "세종특별자치시": {"전기차": 235, "수소차": 308},
    "경기도": {"전기차": "210~450", "수소차": "280~380"},
    "강원특별자치도": {"전기차": 220, "수소차": 300},
    "경상남도": {"전기차": 225, "수소차": 305},
    "경상북도": {"전기차": 215, "수소차": 302},
    "전라남도": {"전기차": 230, "수소차": 310},
    "전북특별자치도": {"전기차": 228, "수소차": 309},
    "충청남도": {"전기차": 222, "수소차": 304},
    "충청북도": {"전기차": 221, "수소차": 303},
    "제주특별자치도": {"전기차": "250~500", "수소차": "300~420"},
}

# -----------------------------
# Helpers
# -----------------------------
def format_distance(distance_m: int) -> str:
    if distance_m < 1000:
        return f"{distance_m}m"
    return f"{distance_m/1000:.1f}km"

def calc_subsidy(
    year: int,
    do_name: str,
    si_name: str,
    car_kind: str
) -> Dict[str, str]:
    """
    반환:
      {
        "status": "ok" | "need_region" | "not_found",
        "message": str,
        "applied_region": str  # 실제 적용된 지역(시 우선)
      }
    """
    do_selected = do_name != "- 선택 -"
    si_selected = si_name != "- 선택 -"

    if not (do_selected or si_selected):
        return {
            "status": "need_region",
            "message": "지역(도 또는 시)을 선택하면 보조금 금액을 확인할 수 있습니다.",
            "applied_region": ""
        }

    # 정책: 시 선택이 있으면 시를 우선 적용하고, 도는 무시
    applied_region = si_name if si_selected else do_name

    region_row = SUBSIDY_MAP.get(applied_region)
    if not region_row or car_kind not in region_row:
        return {
            "status": "not_found",
            "message": "선택한 지역의 보조금 정보가 준비되지 않았습니다.",
            "applied_region": applied_region
        }

    value = region_row[car_kind]
    if isinstance(value, str) and "~" in value:
        msg = f"당신의 예상 보조금은 {value}만원입니다."
    else:
        msg = f"당신의 보조금은 {value}만원입니다."

    return {"status": "ok", "message": msg, "applied_region": applied_region}

def get_dummy_stations(car_kind: str, n: int = 12) -> List[Dict]:
    # DB 컬럼 참고: id, name, address, latitude, longitude, type
    # 현재는 더미(distance_m 포함)로 내부 스크롤 확인용
    base = "전기차" if car_kind == "전기차" else "수소차"
    return [
        {
            "id": i + 1,
            "name": f"{base} 충전소 {i+1}",
            "address": f"서울특별시 강남구 테헤란로 {123 + i*7}",
            "distance_m": 120 + i * 180,
            "type": "EV" if car_kind == "전기차" else "H2",
            "latitude": None,
            "longitude": None,
        }
        for i in range(n)
    ]

import streamlit.components.v1 as components
from typing import List, Dict


def render_stations(stations: List[Dict], max_height_px: int = 320) -> None:
    cards = []
    for s in stations:
        title = f"{s['name']}"
        addr = f"{s['address']}"

        distance_m = int(s["distance_m"])
        if distance_m < 1000:
            dist = f"{distance_m}m"
        else:
            dist = f"{distance_m/1000:.1f}km"

        cards.append(
            f"""
<div style="background:#ffffff;border:1px solid rgba(49,51,63,.2);border-radius:12px;padding:14px 16px;margin-bottom:12px;box-shadow:0 1px 2px rgba(0,0,0,.04);">
  <div style="font-size:16px;font-weight:700;margin-bottom:6px;">{title}</div>
  <div style="font-size:13px;color:rgba(49,51,63,.75);margin-bottom:2px;">주소: {addr}</div>
  <div style="font-size:13px;color:rgba(49,51,63,.75);">거리: {dist}</div>
</div>
"""
        )

    html = f"""
<div style="max-height:{max_height_px}px;overflow-y:auto;padding-right:6px;">
  {''.join(cards)}
</div>
"""

    components.html(html, height=max_height_px + 20, scrolling=False)

# -----------------------------
# Session State Defaults / Reset
# -----------------------------
DEFAULTS = {
    "year": 2026,
    "do": "- 선택 -",
    "si": "- 선택 -",
    "car_kind": "전기차",
    "submitted": False,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

def reset_filters():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v

# -----------------------------
# UI: Title
# -----------------------------
st.markdown(
    """
    <h2 style="text-align:center; margin-bottom:6px;">내 지자체 보조금 알아보기</h2>
    <p style="text-align:center; margin-top:0; color:rgba(49,51,63,.75);">
        구매 조건을 선택하면 예상 보조금과 주변 충전소 정보를 확인할 수 있습니다.
    </p>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# UI: Filters (Form)
# -----------------------------
def on_change_do():
    # 도를 선택하면 시는 자동으로 '- 선택 -'으로 되돌림
    if st.session_state["do"] != "- 선택 -":
        st.session_state["si"] = "- 선택 -"

def on_change_si():
    # 시를 선택하면 도는 자동으로 '- 선택 -'으로 되돌림
    if st.session_state["si"] != "- 선택 -":
        st.session_state["do"] = "- 선택 -"


with st.container():
    with st.form("subsidy_form", clear_on_submit=False):
        st.markdown(
            """
            <div style="
                border:1px solid rgba(49,51,63,.2);
                border-radius:14px;
                padding:16px 18px 6px 18px;
                background:rgba(250,250,252,1);
                margin-bottom:6px;
            ">
            """,
            unsafe_allow_html=True
        )

        # 1st row: Year
        r1 = st.columns([1, 1, 1])
        with r1[0]:
            year = st.selectbox(
                "구매연도",
                options=YEARS,
                index=YEARS.index(st.session_state["year"]),
                key="year"
            )
        with r1[1]:
            st.empty()
        with r1[2]:
            st.empty()

        # 2nd row: Region (Do / Si)
        r2 = st.columns(2)
        with r2[0]:
            do_name = st.selectbox("도", options=DO_OPTIONS, index=DO_OPTIONS.index(st.session_state["do"]), key="do")
        with r2[1]:
            si_name = st.selectbox("시", options=SI_OPTIONS, index=SI_OPTIONS.index(st.session_state["si"]), key="si")

        # 3rd row: Car kind
        r3 = st.columns([2, 1])
        with r3[0]:
            car_kind = st.radio(
                "차량 구분",
                options=CAR_KIND_OPTIONS,
                index=CAR_KIND_OPTIONS.index(st.session_state["car_kind"]),
                horizontal=True,
                key="car_kind"
            )
        with r3[1]:
            st.empty()

        # Buttons
        b1, b2, b3 = st.columns([1, 1, 6])
        with b1:
            submitted = st.form_submit_button("검색", use_container_width=True)
        with b2:
            reset_clicked = st.form_submit_button("초기화", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    if reset_clicked:
        reset_filters()
        st.session_state["submitted"] = False
        st.rerun()

    if submitted:
        st.session_state["submitted"] = True

# -----------------------------
# Result: Subsidy
# -----------------------------
result = calc_subsidy(
    year=st.session_state["year"],
    do_name=st.session_state["do"],
    si_name=st.session_state["si"],
    car_kind=st.session_state["car_kind"]
)

# 시/도 둘 다 선택 시 안내(시 우선 정책)
both_selected = (st.session_state["do"] != "- 선택 -") and (st.session_state["si"] != "- 선택 -")
if both_selected:
    st.info("도와 시를 모두 선택하셨습니다. **시 선택을 우선 적용**하여 보조금을 계산합니다.")

# 강조 박스(결과/안내)
box_text = result["message"]
st.markdown(
    f"""
    <div style="
        border:2px solid rgba(0,123,255,.35);
        background:rgba(0,123,255,.06);
        border-radius:12px;
        padding:18px 14px;
        text-align:center;
        font-size:20px;
        font-weight:800;
        margin-top:10px;
        margin-bottom:18px;
    ">
        {box_text}
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Stations Section
# -----------------------------
section_title = "전기차 충전소 정보" if st.session_state["car_kind"] == "전기차" else "수소차 충전소 정보"
st.subheader(section_title)

# 위치 확인 실패 안내 문구 (현재는 항상 표시; 실제 위치 연동 시 조건부로 바꾸시면 됩니다)
st.caption(
    "현재 위치 정보를 확인할 수 없어, 선택한 지역 기준의 충전소 예시 목록을 보여드리고 있어요. "
    "위치 권한을 허용하면 더 정확한 주변 충전소를 안내해드릴 수 있습니다."
)

stations = get_dummy_stations(st.session_state["car_kind"], n=12)
# 거리 기준 오름차순 정렬(예시)
stations = sorted(stations, key=lambda x: x["distance_m"])


render_stations(stations, max_height_px=320)