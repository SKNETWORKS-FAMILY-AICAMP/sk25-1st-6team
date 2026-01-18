import json
import re
import os
import streamlit as st
import pandas as pd
import folium
from folium.features import DivIcon
from streamlit_folium import st_folium
from api.client import MockApiClient

# -------------------------
# 1. 상수 및 유틸리티 설정
# -------------------------
PROVINCE_CENTERS = {
    "서울": [37.5665, 126.9780], "경기": [37.4138, 127.5183], "인천": [37.4563, 126.7052],
    "강원": [37.8228, 128.1555], "충북": [36.6357, 127.4912], "충남": [36.6588, 126.6728],
    "대전": [36.3504, 127.3845], "세종": [36.4800, 127.2890], "경북": [36.4919, 128.8889],
    "경남": [35.4606, 128.2132], "대구": [35.8714, 128.6014], "울산": [35.5389, 129.3114],
    "부산": [35.1796, 129.0756], "전북": [35.7175, 127.1530], "전남": [34.8679, 126.9910],
    "광주": [35.1595, 126.8526], "제주": [33.4996, 126.5312],
}


def _clean_name(x: str) -> str:
    if not x: return ""
    x = re.sub(r"\s+", "", x.strip())
    return re.sub(r"(특별시|광역시|특별자치시|특별자치도|도|시)$", "", x)


@st.cache_data
def load_geojson():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    geojson_path = os.path.join(base_dir, "korea_8do_seoul.geojson")
    try:
        with open(geojson_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


@st.cache_data
def get_processed_data():
    reg_stats = MockApiClient.get_registration_stats()
    air_stats = MockApiClient.get_air_pollution_stats()

    reg_df = pd.DataFrame([{"province": s.region.name, "reg_count": s.registration_count} for s in reg_stats])
    air_df = pd.DataFrame([{"province": s.region.name, "poll_degree": s.pollution_degree} for s in air_stats])

    merged = pd.merge(reg_df, air_df, on="province", how="outer").fillna(0)
    merged['p_clean'] = merged['province'].apply(_clean_name)
    return merged


@st.cache_data
def get_enriched_geojson(_geo, _df):
    geo_copy = json.loads(json.dumps(_geo))
    for feature in geo_copy['features']:
        p_name = _clean_name(feature['properties'].get('name', ''))
        row = _df[_df['p_clean'] == p_name]
        if not row.empty:
            feature['properties']['reg_val'] = f"{int(row.iloc[0]['reg_count']):,}대"
            feature['properties']['poll_val'] = f"{int(row.iloc[0]['poll_degree'])} μg/m³"
        else:
            feature['properties']['reg_val'] = "데이터 없음"
            feature['properties']['poll_val'] = "-"
    return geo_copy


# -------------------------
# 2. 메인 렌더링 함수
# -------------------------
def render():
    # CSS 설정 (마커 간섭 방지 및 포커스 박스 제거)
    st.markdown("""
        <style>
            .leaflet-marker-icon { pointer-events: none !important; }
            iframe { border: none !important; }
            div[data-testid="stFolium"] { border: none !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align:center;'>Nationwide Vehicle Registration & Air Quality</h1>",
                unsafe_allow_html=True)

    # 데이터 준비 (캐시 활용)
    merged_df = get_processed_data()
    raw_geo = load_geojson()
    if not raw_geo: return

    # 데이터가 주입된 GeoJSON 가져오기 (캐시 활용)
    geo = get_enriched_geojson(raw_geo, merged_df)

    if "selected_province" not in st.session_state:
        st.session_state.selected_province = ""

    # 3. 지도 객체 생성
    m = folium.Map(
        location=[36.3, 127.8], zoom_start=7, tiles="cartodbpositron",
        dragging=False, zoom_control=False, scrollWheelZoom=False,
        doubleClickZoom=False, touchZoom=False
    )

    # '박스 제거' 및 '포커스 해제' JS 주입
    m.get_root().header.add_child(folium.Element("""
        <style>
            path.leaflet-interactive:focus, .leaflet-container:focus { 
                outline: none !important; 
                box-shadow: none !important; 
            }
        </style>
        <script>
            document.addEventListener('click', function(e) {
                if (e.target.classList.contains('leaflet-interactive')) {
                    e.target.blur(); 
                }
            });
        </script>
    """))

    def style_fn(feature):
        selected = _clean_name(st.session_state.selected_province)
        is_selected = (_clean_name(feature["properties"].get("name", "")) == selected)
        return {
            "fillColor": "#318ce7" if is_selected else "#ffffff",
            "color": "#0047ab" if is_selected else "#cccccc",
            "weight": 3 if is_selected else 1,
            "fillOpacity": 0.6 if is_selected else 0.1,
        }

    folium.GeoJson(
        geo,
        style_function=style_fn,
        highlight_function=lambda x: {"fillColor": "#b2d8ff", "fillOpacity": 0.8},
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "reg_val", "poll_val"],
            aliases=["📍 지역:", "🚗 자동차:", "🌫 오염도:"],
            style="background-color: white; border: 1px solid grey; border-radius: 5px; padding: 10px;"
        )
    ).add_to(m)

    # 시도 이름 마커 추가
    for name, coords in PROVINCE_CENTERS.items():
        folium.Marker(
            location=coords,
            icon=DivIcon(
                icon_size=(0, 0), icon_anchor=(0, 0),
                html=f"""<div style="position: relative; left: -25px; top: -10px; width: 50px; font-size: 11pt; 
                            font-weight: bold; color: #333; text-align: center; pointer-events: none;
                            text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;
                            white-space: nowrap;">{name}</div>"""
            )
        ).add_to(m)

    # 4. 지도 렌더링
    map_out = st_folium(
        m, key="korea_map_dashboard", height=550, use_container_width=True,
        returned_objects=["last_active_drawing"]
    )

    # 클릭 이벤트 처리 최적화
    clicked = map_out.get("last_active_drawing")
    if clicked:
        new_sel = _clean_name(clicked.get("properties", {}).get("name", ""))
        if new_sel and st.session_state.selected_province != new_sel:
            st.session_state.selected_province = new_sel
            st.rerun()

    # 5. 하단 데이터 대시보드
    st.divider()
    sel_name = st.session_state.selected_province

    if sel_name:
        col1, col2 = st.columns([0.8, 0.2])
        col1.subheader(f"📍 {sel_name} 상세 현황")
        if col2.button("전체 보기", use_container_width=True):
            st.session_state.selected_province = ""
            st.rerun()
        display_df = merged_df[merged_df['p_clean'] == _clean_name(sel_name)]
    else:
        st.subheader("전국 통계 현황 (지도를 클릭하여 지역을 선택하세요)")
        display_df = merged_df

    # 테이블 가공 및 표시
    styled_df = display_df.rename(columns={
        "province": "시/도",
        "poll_degree": "대기질 오염도",
        "reg_count": "차량등록대수"
    })[["시/도", "대기질 오염도", "차량등록대수"]]

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "차량등록대수": st.column_config.NumberColumn(format="%d 대"),
            "대기질 오염도": st.column_config.NumberColumn(format="%d μg/m³")
        }
    )