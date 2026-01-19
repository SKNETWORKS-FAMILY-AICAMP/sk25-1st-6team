import json
import platform
import re
import os

import streamlit as st
import pandas as pd
import folium
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from urllib.parse import quote

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


def get_dummy_stations(car_kind: str, n: int = 12):
    base = "전기차" if car_kind == "전기차" else "수소차"
    return [
        {
            "id": i + 1,
            "name": f"{base} 충전소 {i+1}",
            "address": f"서울특별시 강남구 테헤란로 {123 + i*7}",
            "distance_m": 120 + i * 180,
        }
        for i in range(n)
    ]


def render_stations(stations, max_height_px: int = 320):
    cards = []
    for s in stations:
        dist = f"{s['distance_m']}m" if s["distance_m"] < 1000 else f"{s['distance_m']/1000:.1f}km"
        cards.append(
            f"""
            <div style="background:#fff;border:1px solid #ddd;border-radius:10px;
                        padding:12px;margin-bottom:10px;">
              <div style="font-weight:700;">{s['name']}</div>
              <div style="font-size:13px;color:#555;">주소: {s['address']}</div>
              <div style="font-size:13px;color:#555;">거리: {dist}</div>
            </div>
            """
        )

    html = f"""
    <div style="max-height:{max_height_px}px;overflow-y:auto;">
        {''.join(cards)}
    </div>
    """
    components.html(html, height=max_height_px + 20)


def _clean_name(x: str) -> str:
    if not x:
        return ""
    x = re.sub(r"\s+", "", x.strip())
    return re.sub(r"(특별시|광역시|특별자치시|특별자치도|도|시)$", "", x)


def set_korean_font():
    """Matplotlib 한글 깨짐 방지 설정"""
    os_name = platform.system()
    if os_name == "Windows":
        plt.rc("font", family="Malgun Gothic")
    elif os_name == "Darwin":  # Mac
        plt.rc("font", family="AppleGothic")
    else:  # Linux
        plt.rc("font", family="NanumGothic")
    plt.rc("axes", unicode_minus=False)


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
    merged["p_clean"] = merged["province"].apply(_clean_name)
    return merged


@st.cache_data
def get_enriched_geojson(_geo, _df):
    geo_copy = json.loads(json.dumps(_geo))
    for feature in geo_copy["features"]:
        p_name = _clean_name(feature["properties"].get("name", ""))
        row = _df[_df["p_clean"] == p_name]
        if not row.empty:
            feature["properties"]["reg_val"] = f"{int(row.iloc[0]['reg_count']):,}대"
            feature["properties"]["poll_val"] = f"{int(row.iloc[0]['poll_degree'])} μg/m³"
        else:
            feature["properties"]["reg_val"] = "데이터 없음"
            feature["properties"]["poll_val"] = "-"
    return geo_copy


def render_cta():
    st.markdown(
        """
        <div style="
            background: rgba(0,0,0,0.03);
            border-radius: 18px;
            padding: 20px 22px;
            text-align: center;
            margin-top: 14px;
            margin-bottom: 16px;
            border: 1px solid rgba(0,0,0,0.10);
        ">
          <div style="
              font-weight: 900;
              font-size: 28px;
              line-height: 1.35;
              margin-bottom: 10px;
          ">
            깨끗한 공기를 위한 작은 선택, 무공해차(전기·수소차)로 전환을 고려해보세요.
          </div>

          <div style="
              font-weight: 900;
              font-size: 28px;
              line-height: 1.35;
          ">
            대기질 개선을 위해 친환경 이동수단(무공해차) 구매 혜택을 확인해보세요.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_subsidy_popup_button():
    """
    ✅ '내 보조금 계산하기' 클릭 시 calculator 페이지를 "팝업(새 창)"으로 엽니다.
    """
    menu_value = "무공해차 보조금 계산기"  # app.py 라우팅 MENU_ITEMS와 동일해야 함
    popup_url = f"?menu={quote(menu_value)}"

    html = f"""
    <div style="display:flex; justify-content:center; margin-top: 6px; margin-bottom: 10px;">
      <button
        id="subsidyPopupBtn"
        style="
          width: 420px;
          background-color: #2563eb;
          color: white;
          font-weight: 900;
          font-size: 20px;
          padding: 12px 16px;
          border-radius: 14px;
          border: none;
          cursor: pointer;
        "
        onmouseover="this.style.backgroundColor='#1d4ed8'"
        onmouseout="this.style.backgroundColor='#2563eb'"
      >
        내 보조금 계산하기
      </button>
    </div>

    <script>
      const btn = document.getElementById("subsidyPopupBtn");
      btn.addEventListener("click", () => {{
        const features = "width=1100,height=800,scrollbars=yes,resizable=yes";
        window.open("{popup_url}", "_blank", features);
      }});
    </script>
    """
    components.html(html, height=90)


# -------------------------
# 2. 메인 렌더링 함수
# -------------------------
def render():
    # ✅ car_kind 기본값 보장
    if "car_kind" not in st.session_state:
        st.session_state["car_kind"] = "전기차"

    # CSS 설정 (마커 간섭 방지 및 포커스 박스 제거)
    st.markdown(
        """
        <style>
            .leaflet-marker-icon { pointer-events: none !important; }
            iframe { border: none !important; }
            div[data-testid="stFolium"] { border: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<h1 style='text-align:center;'>Nationwide Vehicle Registration & Air Quality</h1>",
        unsafe_allow_html=True,
    )

    # 데이터 준비 (캐시 활용)
    merged_df = get_processed_data()
    raw_geo = load_geojson()
    if not raw_geo:
        return

    # 데이터가 주입된 GeoJSON 가져오기 (캐시 활용)
    geo = get_enriched_geojson(raw_geo, merged_df)

    if "selected_province" not in st.session_state:
        st.session_state.selected_province = ""

    # 3. 지도 객체 생성
    m = folium.Map(
        location=[36.3, 127.8],
        zoom_start=7,
        tiles="cartodbpositron",
        dragging=False,
        zoom_control=False,
        scrollWheelZoom=False,
        doubleClickZoom=False,
        touchZoom=False,
    )

    # '박스 제거' 및 '포커스 해제' JS 주입
    m.get_root().header.add_child(
        folium.Element(
            """
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
            """
        )
    )

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
            style="background-color: white; border: 1px solid grey; border-radius: 5px; padding: 10px;",
        ),
    ).add_to(m)

    # 시도 이름 마커 추가
    for name, coords in PROVINCE_CENTERS.items():
        folium.Marker(
            location=coords,
            icon=DivIcon(
                icon_size=(0, 0),
                icon_anchor=(0, 0),
                html=f"""<div style="position: relative; left: -25px; top: -10px; width: 50px; font-size: 11pt;
                            font-weight: bold; color: #333; text-align: center; pointer-events: none;
                            text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;
                            white-space: nowrap;">{name}</div>""",
            ),
        ).add_to(m)

    # 4. 지도 렌더링
    map_out = st_folium(
        m,
        key="korea_map_dashboard",
        height=550,
        use_container_width=True,
        returned_objects=["last_active_drawing"],
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
        display_df = merged_df[merged_df["p_clean"] == _clean_name(sel_name)]
    else:
        st.subheader("전국 통계 현황 (지도를 클릭하여 지역을 선택하세요)")
        display_df = merged_df

    # 테이블 가공 및 표시
    styled_df = display_df.rename(
        columns={"province": "시/도", "poll_degree": "대기질 오염도", "reg_count": "차량등록대수"}
    )[["시/도", "대기질 오염도", "차량등록대수"]]

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "차량등록대수": st.column_config.NumberColumn(format="%d 대"),
            "대기질 오염도": st.column_config.NumberColumn(format="%d μg/m³"),
        },
    )


    # F. 정규화 통합 라인 차트 표시 (Matplotlib 고정형)
    target_name = st.session_state.selected_province

    if not target_name:
        st.info("💡 분석할 지역을 선택하면 조작이 불가능한 정적 추이 그래프가 나타납니다.")
    else:
        st.markdown(f"### 📈 {target_name} 지표별 변화 추이 (Scale Normalized)")

        years = [2022, 2023, 2024, 2025, 2026]
        region_data = merged_df[merged_df["p_clean"] == _clean_name(target_name)].iloc[0]
        base_reg = region_data["reg_count"]
        base_poll = region_data["poll_degree"]

        df_trend = pd.DataFrame(
            {
                "연도": years,
                "자동차 등록대수": [int(base_reg * (0.9 + (i * 0.025))) for i in range(len(years))],
                "대기질 오염도": [base_poll + (i * 1.5) - (i % 2 * 3) for i in range(len(years))],
            }
        )

        def normalize(series):
            if series.max() == series.min():
                return series * 0
            return (series - series.min()) / (series.max() - series.min()) * 100

        reg_norm = normalize(df_trend["자동차 등록대수"])
        poll_norm = normalize(df_trend["대기질 오염도"])

        set_korean_font()
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(years, reg_norm, label="자동차 등록대수", color="#318ce7", marker="o", linewidth=2)
        ax.plot(years, poll_norm, label="대기질 오염도", color="#ff4b4b", marker="s", linewidth=2)

        ax.set_title(f"{target_name} 지표별 상관관계 분석", fontsize=14)
        ax.set_ylim(-10, 110)
        ax.set_xticks(years)
        ax.set_ylabel("상대적 변화율 (0-100)")
        ax.legend(loc="upper left")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        st.pyplot(fig)
        plt.close(fig)

        st.caption(
            "**💡 그래프 설명:** 연도별 자동차 등록대수 증가와 대기질 오염도의 상관관계를 분석하기 위해, "
            "서로 다른 단위의 두 지표를 0~100 사이의 상대적 수치로 정규화(Normalization)하여 나타낸 분석 차트입니다."
        )

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("최종 자동차 등록대수", f"{int(df_trend['자동차 등록대수'].iloc[-1]):,} 대")
        m2.metric("최종 대기질 오염도", f"{df_trend['대기질 오염도'].iloc[-1]:.1f} μg/m³")
        m3.metric("5개년 등록 증가 추세", "+10.0%")

    # =========================
    # 8) CTA + 보조금 계산기 팝업 버튼 + 충전소 정보 (페이지 맨 아래)
    # =========================
    render_cta()
    render_subsidy_popup_button()

    section_title = (
        "전기차 충전소 정보"
        if st.session_state["car_kind"] == "전기차"
        else "수소차 충전소 정보"
    )
    st.subheader(section_title)

    st.caption(
        "현재 위치 정보를 확인할 수 없어, 선택한 지역 기준의 충전소 예시 목록을 보여드리고 있어요. "
        "위치 권한을 허용하면 더 정확한 주변 충전소를 안내해드릴 수 있습니다."
    )

    stations = get_dummy_stations(st.session_state["car_kind"], n=12)
    stations = sorted(stations, key=lambda x: x["distance_m"])
    render_stations(stations, max_height_px=320)
