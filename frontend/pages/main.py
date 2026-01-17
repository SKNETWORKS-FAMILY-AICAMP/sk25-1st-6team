# app.py
import json
import re
import streamlit as st
import pandas as pd
import folium
from folium.features import DivIcon
from streamlit_folium import st_folium
import os; print(">>> GEOJSON PATH:", os.path.exists("/home/playdata2/workspace/encore/korea_8do_seoul.geojson"))


st.set_page_config(page_title="Vehicle Air Insight", layout="wide")
if "sidebar_menu" not in st.session_state:
    st.session_state.sidebar_menu = "지역별 자동차 등록 현황"


# =========================
# 1) 설정: GeoJSON 경로만 수정하세요
# =========================
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KOREA_GEOJSON = os.path.join(BASE_DIR, "korea_8do_seoul.geojson")

# =========================
# 2) 더미 데이터 (연습용)
#    - region: 도/서울 이름이 GeoJSON properties name과 최대한 동일해야 매칭이 쉬움
# =========================
DATA = [
    {"year": 2023, "province": "서울", "city": "서울", "district": "강남구", "vehicle_type": "ALL", "usage": "PERSONAL",
     "registration_count": 1200000, "pollution_degree": 35, "lat": 37.5665, "lon": 126.9780},
    {"year": 2023, "province": "경기", "city": "수원", "district": "영통구", "vehicle_type": "ALL", "usage": "PERSONAL",
     "registration_count": 2300000, "pollution_degree": 28, "lat": 37.2636, "lon": 127.0286},
    {"year": 2023, "province": "부산", "city": "부산", "district": "해운대구", "vehicle_type": "ALL", "usage": "PERSONAL",
     "registration_count": 760000, "pollution_degree": 42, "lat": 35.1796, "lon": 129.0756},
    {"year": 2023, "province": "대구", "city": "대구", "district": "수성구", "vehicle_type": "ALL", "usage": "PERSONAL",
     "registration_count": 540000, "pollution_degree": 30, "lat": 35.8714, "lon": 128.6014},
    {"year": 2023, "province": "강원", "city": "춘천", "district": "춘천시", "vehicle_type": "ALL", "usage": "PERSONAL",
     "registration_count": 310000, "pollution_degree": 18, "lat": 37.8813, "lon": 127.7298},
    {"year": 2023, "province": "충북", "city": "청주", "district": "상당구", "vehicle_type": "ALL", "usage": "PERSONAL",
     "registration_count": 420000, "pollution_degree": 22, "lat": 36.6424, "lon": 127.4890},
    {"year": 2023, "province": "충남", "city": "천안", "district": "서북구", "vehicle_type": "ALL", "usage": "PERSONAL",
     "registration_count": 510000, "pollution_degree": 25, "lat": 36.8151, "lon": 127.1139},
    {"year": 2023, "province": "전북", "city": "전주", "district": "완산구", "vehicle_type": "ALL", "usage": "PERSONAL",
     "registration_count": 390000, "pollution_degree": 20, "lat": 35.8242, "lon": 127.1480},
    {"year": 2023, "province": "전남", "city": "여수", "district": "여수시", "vehicle_type": "ALL", "usage": "PERSONAL",
     "registration_count": 340000, "pollution_degree": 19, "lat": 34.7604, "lon": 127.6622},
    {"year": 2023, "province": "경북", "city": "포항", "district": "북구", "vehicle_type": "ALL", "usage": "PERSONAL",
     "registration_count": 460000, "pollution_degree": 24, "lat": 36.0190, "lon": 129.3435},
    {"year": 2023, "province": "경남", "city": "창원", "district": "성산구", "vehicle_type": "ALL", "usage": "PERSONAL",
     "registration_count": 520000, "pollution_degree": 27, "lat": 35.2279, "lon": 128.6811},
    {"year": 2023, "province": "제주", "city": "제주", "district": "제주시", "vehicle_type": "ALL", "usage": "PERSONAL",
     "registration_count": 260000, "pollution_degree": 16, "lat": 33.4996, "lon": 126.5312},
]
df = pd.DataFrame(DATA)

# =========================
# 3) CSS (오른쪽 플로팅 버튼 + 간단 스타일)
# =========================
st.markdown(
    """
<style>
.big-title{
  font-size: 46px; font-weight: 900; text-align:center; margin-top:0.2rem; margin-bottom:0.1rem;
}
.sub-title{
  text-align:center; color:#444; margin-bottom:0.8rem;
}
.fab-wrap{
  position: fixed;
  right: 26px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 9999;
  display:flex;
  flex-direction:column;
  gap: 10px;
}
.fab-btn{
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: none;
  background: #ff7a45;
  color: white;
  font-size: 18px;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(0,0,0,0.15);
}
.fab-btn:hover{ filter: brightness(0.95); }
.section-card{
  background: white;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 18px;
  padding: 18px 18px;
}
</style>

<div class="fab-wrap">
  <button class="fab-btn" onclick="window.scrollTo({top: 0, behavior: 'smooth'});">↑</button>
  <button class="fab-btn" onclick="window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});">↓</button>
</div>
""",
    unsafe_allow_html=True,
)

# =========================
# 4) 상태값 (지도 클릭 결과 저장)
# =========================
if "selected_province" not in st.session_state:
    st.session_state.selected_province = ""

# =========================
# 5) 사이드바 메뉴 (아이콘 + 텍스트 항상 표시, hover 아님)
# =========================
# 현재 선택 메뉴를 URL 쿼리로 저장/복원 (새로고침해도 유지됨)
params = st.query_params
current = params.get("menu", "지역별 자동차 등록 현황")

MENU_ITEMS = [
    ("지역별 자동차 등록 현황", "🗺️"),
    ("무공해차 보조금 계산기", "🧮"),
    ("무공해차 FAQ", "❓"),
]

st.sidebar.markdown(
    """
    <style>
    /* 사이드바 기본 여백 조금 정리 */
    section[data-testid="stSidebar"] > div { padding-top: 18px; }

    .sb-title{
      font-size: 22px;
      font-weight: 900;
      margin: 4px 0 14px 8px;
    }

    /* 메뉴 전체 */
    .nav {
      display:flex;
      flex-direction:column;
      gap:10px;
      padding: 0 8px;
    }

    /* 메뉴 아이템(링크) */
    .nav a{
      text-decoration:none !important;
      color: #111 !important;
    }

    .item{
      display:flex;
      align-items:center;
      gap:12px;
      padding: 12px 12px;
      border-radius: 14px;
      border: 1px solid rgba(0,0,0,0.10);
      background: #ffffff;
      transition: all 0.12s ease;
    }
    .item:hover{ background:#f3f4f6; }  /* hover는 단순 밝기만 (말풍선/툴팁 없음) */

    .icon{
      width: 38px;
      height: 38px;
      border-radius: 12px;
      display:flex;
      align-items:center;
      justify-content:center;
      font-size: 20px;
      background: rgba(0,0,0,0.04);
    }

    .label{
      font-size: 15px;
      font-weight: 800;
      white-space: nowrap;
    }

    /* 선택된 메뉴 (항상 고정 강조) */
    .active{
      border-color: rgba(59,130,246,0.55);
      background: rgba(59,130,246,0.08);
      box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    }
    .active .icon{
      background: rgba(59,130,246,0.20);
    }
    .active .label{
      color: #1d4ed8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown('<div class="sb-title">Menu</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="nav">', unsafe_allow_html=True)

for label, icon in MENU_ITEMS:
    active_class = "active" if label == current else ""
    # 클릭하면 URL에 ?menu=... 로 저장 (항상 유지)
    st.sidebar.markdown(
        f"""
        <a href='?menu={label}'>
          <div class='item {active_class}'>
            <div class='icon'>{icon}</div>
            <div class='label'>{label}</div>
          </div>
        </a>
        """,
        unsafe_allow_html=True
    )

st.sidebar.markdown("</div>", unsafe_allow_html=True)

menu = current


params = st.query_params
current = params.get("menu", "지역별 자동차 등록 현황")
menu = current




# =========================
# 6) 상단 타이틀
# =========================
st.markdown('<div class="big-title">Nationwide Vehicle Registration & Air Quality Data</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Explore comprehensive data on vehicle registration and its impact on air quality across South Korea.</div>',
    unsafe_allow_html=True
)



# =========================
# 7) 지도 그리기 (GeoJSON + Hover + Click)
# =========================
def load_geojson(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _clean_name(x: str) -> str:
    x = (x or "").strip()
    x = re.sub(r"\s+", "", x)
    return x

geo = load_geojson(KOREA_GEOJSON)

# 지도 중심 (대략 대한민국)
m = folium.Map(location=[36.5, 127.8], zoom_start=7, tiles="CartoDB positron")

def style_fn(feature):
    # 선택된 도는 조금 강조
    name = feature.get("properties", {}).get("name") or feature.get("properties", {}).get("region") or ""
    name = _clean_name(name)
    selected = _clean_name(st.session_state.selected_province)
    is_selected = selected and (name == selected)
    return {
        "fillColor": "#7fc97f" if is_selected else "#ffffff",
        "color": "#222222",
        "weight": 2.5,
        "fillOpacity": 0.35 if is_selected else 0.05,
    }

tooltip = folium.GeoJsonTooltip(
    fields=["name"],
    aliases=["지역"],
    sticky=True
)

gj = folium.GeoJson(
    geo,
    name="korea",
    style_function=style_fn,
    tooltip=tooltip,
)

gj.add_to(m)

# 지도 위 아이콘(등록대수 + 대기질) : DivIcon + marker
for _, r in df.groupby("province", as_index=False).first().iterrows():
    # 작은 카드 형태로 표시
    html_box = f"""
    <div style="
        background: rgba(40,40,40,0.82);
        color: white;
        padding: 6px 8px;
        border-radius: 8px;
        font-size: 12px;
        line-height: 1.2;
        white-space: nowrap;
    ">
      🚗 {int(r['registration_count']):,}<br/>
      🌫 {int(r['pollution_degree'])}
    </div>
    """
    folium.Marker(
        location=[r["lat"], r["lon"]],
        icon=DivIcon(html=html_box),
        tooltip=r["province"]
    ).add_to(m)

# streamlit에 지도 출력 + 클릭 이벤트 받기
map_out = st_folium(m, height=520, use_container_width=True)

# 클릭된 GeoJSON feature 이름 받아서 '도'에 반영
# (folium 클릭 이벤트는 st_folium의 last_active_drawing / last_object_clicked 등을 케이스별로 활용)
clicked = map_out.get("last_active_drawing") or map_out.get("last_object_clicked")
if isinstance(clicked, dict):
    props = clicked.get("properties") or {}
    clicked_name = props.get("name") or props.get("region")
    if clicked_name:
        st.session_state.selected_province = _clean_name(clicked_name)

# =========================
# 8) 필터 영역 (요구사항대로 2줄 구성)
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Filters")

# 1줄: 도 / 시 / 군구
c1, c2, c3 = st.columns(3)

provinces = [""] + sorted(df["province"].unique().tolist())
cities = [""] + sorted(df[df["province"] == st.session_state.selected_province]["city"].unique().tolist()) \
    if st.session_state.selected_province else [""]

districts = [""] + sorted(
    df[(df["province"] == st.session_state.selected_province) & (df["city"] == (cities[1] if len(cities) > 1 else ""))]["district"].unique().tolist()
) if st.session_state.selected_province else [""]

with c1:
    province = st.selectbox(
        "도(Province)",
        provinces,
        index=(provinces.index(st.session_state.selected_province) if st.session_state.selected_province in provinces else 0),
        key="province_filter",
    )

with c2:
    city = st.selectbox("시(City)", cities if cities else ["Select Province first"], key="city_filter")

with c3:
    district = st.selectbox("군/구(District)", ["Select City first"] if (not city or "Select" in city) else [""] + sorted(
        df[(df["province"] == province) & (df["city"] == city)]["district"].unique().tolist()
    ), key="district_filter")

# 2줄: 연도 / 자동차타입 / 자동차 용도
c4, c5, c6 = st.columns(3)

with c4:
    year = st.selectbox("연도(Year)", sorted(df["year"].unique().tolist()), index=0, key="year_filter")

with c5:
    vehicle_type = st.selectbox("자동차 타입(Vehicle Type)", ["ALL", "EV", "HYBRID", "HYDROGEN", "ICE"], index=0, key="type_filter")

with c6:
    usage = st.selectbox("자동차 용도(Vehicle Usage)", ["PERSONAL", "BUSINESS", "ALL"], index=0, key="usage_filter")

btn_left, btn_right = st.columns([1, 1])
with btn_left:
    do_search = st.button("Search", use_container_width=True)
with btn_right:
    do_reset = st.button("Reset", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# Reset 동작
if do_reset:
    st.session_state.selected_province = ""
    st.session_state.province_filter = ""
    st.session_state.city_filter = ""
    st.session_state.district_filter = ""
    st.session_state.year_filter = df["year"].min()
    st.session_state.type_filter = "ALL"
    st.session_state.usage_filter = "PERSONAL"
    st.rerun()

# Search 결과 표시(연습용)
if do_search:
    cond = (df["year"] == year)
    if province:
        cond &= (df["province"] == province)
    if city and "Select" not in city:
        cond &= (df["city"] == city)
    if district and "Select" not in district and district != "":
        cond &= (df["district"] == district)
    if vehicle_type != "ALL":
        cond &= (df["vehicle_type"].isin([vehicle_type, "ALL"]))
    if usage != "ALL":
        cond &= (df["usage"].isin([usage, "ALL"]))

    out = df[cond].copy()

    st.markdown("### Search Result")
    if out.empty:
        st.info("조건에 맞는 데이터가 없습니다.")
    else:
        st.dataframe(
            out[["year", "province", "city", "district", "registration_count", "pollution_degree"]],
            use_container_width=True
        )

