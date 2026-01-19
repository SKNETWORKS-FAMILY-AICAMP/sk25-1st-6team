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


# -------------------------
# 2. 충전소 카드 렌더링
# -------------------------
def render_stations(stations, max_height_px: int = 320):
    cards = []
    for s in stations:
        dist_m = int(s.get("distance_m", 0) or 0)
        dist = f"{dist_m}m" if dist_m < 1000 else f"{dist_m / 1000:.1f}km"

        lat = s.get("latitude")
        lng = s.get("longitude")

        coord_text = ""
        if lat is not None and lng is not None:
            coord_text = f"<div style='font-size:12px;color:#777;'>위도/경도: {lat}, {lng}</div>"

        cards.append(
            f"""
            <div style="background:#fff;border:1px solid #ddd;border-radius:10px;
                        padding:12px;margin-bottom:10px;">
              <div style="font-weight:700;">{s.get('name','')}</div>
              <div style="font-size:13px;color:#555;">주소: {s.get('address','')}</div>
              <div style="font-size:13px;color:#555;">거리: {dist}</div>
              {coord_text}
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
    x = re.sub(r"\s+", "", str(x).strip())
    return re.sub(r"(특별시|광역시|특별자치시|특별자치도|도|시)$", "", x)


def set_korean_font():
    """Matplotlib 한글 깨짐 방지 설정"""
    os_name = platform.system()
    if os_name == "Windows":
        plt.rc("font", family="Malgun Gothic")
    elif os_name == "Darwin":
        plt.rc("font", family="AppleGothic")
    else:
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

    reg_df = pd.DataFrame(
        [{"province": s.region.name, "reg_count": s.registration_count} for s in reg_stats]
    )
    air_df = pd.DataFrame(
        [{"province": s.region.name, "poll_degree": s.pollution_degree} for s in air_stats]
    )

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
    menu_value = "무공해차 보조금 계산기"
    popup_url = f"?menu={quote(menu_value)}&popup=1"

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
# 3. GPS 관련 함수
# -------------------------
def sync_location_from_query_params():
    """
    URL 쿼리파라미터(gps_lat,gps_lng)가 있으면 session_state에 저장합니다.
    예: ?menu=...&gps_lat=37.1&gps_lng=127.1
    """
    params = st.query_params
    lat = params.get("gps_lat") or params.get("lat")
    lng = params.get("gps_lng") or params.get("lng")

    if lat and lng:
        try:
            st.session_state["user_lat"] = float(lat)
            st.session_state["user_lng"] = float(lng)

            # ✅ 한 번 저장했으면 URL 정리
            for k in ["gps_lat", "gps_lng", "gps_ts", "lat", "lng"]:
                if k in st.query_params:
                    del st.query_params[k]

        except ValueError:
            st.session_state.pop("user_lat", None)
            st.session_state.pop("user_lng", None)


def render_gps_buttons():
    col1, col2 = st.columns([1, 1])

    with col1:
        use_now = st.button("📍 현재 위치 사용", use_container_width=True)

    with col2:
        reset = st.button("🧹 위치 초기화", use_container_width=True)

    if reset:
        st.session_state["user_lat"] = None
        st.session_state["user_lng"] = None
        st.toast("위치를 초기화했어요.")
        st.rerun()

    if use_now:
        components.html(
            """
            <script>
            (function() {
              function go(lat, lng) {
                const url = new URL(window.location.href);
                url.searchParams.set("gps_lat", String(lat));
                url.searchParams.set("gps_lng", String(lng));
                url.searchParams.set("gps_ts", String(Date.now()));
                window.location.href = url.toString();
              }

              if (!navigator.geolocation) {
                alert("이 브라우저는 위치(GPS)를 지원하지 않아요.");
                return;
              }

              navigator.geolocation.getCurrentPosition(
                (pos) => { go(pos.coords.latitude, pos.coords.longitude); },
                (err) => {
                  alert("위치 권한이 거부되었거나, 위치를 가져오지 못했어요.\\n"
                        + "브라우저 주소창 왼쪽 자물쇠(사이트 설정)에서 위치를 '허용'으로 바꿔주세요.");
                  console.log(err);
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
              );
            })();
            </script>
            """,
            height=0,
        )


# -------------------------
# 4. 메인 렌더링 함수
# -------------------------
def render():
    # ✅ car_kind 기본값
    if "car_kind" not in st.session_state:
        st.session_state["car_kind"] = "전기차"

    # ✅ URL gps_lat/gps_lng -> session_state 동기화
    sync_location_from_query_params()

    # CSS 설정
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

    merged_df = get_processed_data()
    raw_geo = load_geojson()
    if not raw_geo:
        st.error("GeoJSON 파일을 찾지 못했습니다. korea_8do_seoul.geojson 경로를 확인해주세요.")
        return

    geo = get_enriched_geojson(raw_geo, merged_df)

    if "selected_province" not in st.session_state:
        st.session_state.selected_province = ""

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

    map_out = st_folium(
        m,
        key="korea_map_dashboard",
        height=550,
        use_container_width=True,
        returned_objects=["last_active_drawing"],
    )

    clicked = map_out.get("last_active_drawing")
    if clicked:
        new_sel = _clean_name(clicked.get("properties", {}).get("name", ""))
        if new_sel and st.session_state.selected_province != new_sel:
            st.session_state.selected_province = new_sel
            st.rerun()

    st.divider()
    sel_name = st.session_state.selected_province

    if sel_name:
        col1, col2 = st.columns([0.8, 0.2])
        col1.subheader(f"📍 {sel_name} 상세 현황")
        if col2.button("전체 보기", use_container_width=True, key="btn_show_all"):
            st.session_state.selected_province = ""
            st.rerun()
        display_df = merged_df[merged_df["p_clean"] == _clean_name(sel_name)]
    else:
        st.subheader("전국 통계 현황 (지도를 클릭하여 지역을 선택하세요)")
        display_df = merged_df

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

    # =========================
    # CTA + 보조금 팝업 버튼
    # =========================
    render_cta()
    render_subsidy_popup_button()

    # -------------------------
    # 전기차 / 수소차 선택
    # -------------------------
    car_kind = st.radio(
        "차종 선택",
        ["전기차", "수소차"],
        index=0 if st.session_state.get("car_kind", "전기차") == "전기차" else 1,
        horizontal=True,
        key="car_kind_radio",
    )
    st.session_state["car_kind"] = car_kind

    # -------------------------
    # GPS 버튼
    # -------------------------
    render_gps_buttons()

    # -------------------------
    # 충전소 섹션
    # -------------------------
    user_lat = st.session_state.get("user_lat")
    user_lng = st.session_state.get("user_lng")

    section_title = "전기차 충전소 정보" if car_kind == "전기차" else "수소차 충전소 정보"
    st.subheader(section_title)

    if user_lat is None or user_lng is None:
        st.caption(
            "현재 위치(GPS)를 아직 받지 못했어요. "
            "위의 **'현재 위치 사용'** 버튼을 눌러 위치 권한을 허용하면, "
            "내 위치 기준으로 더 정확한 주변 충전소를 안내할 수 있어요."
        )
    else:
        st.caption(f"내 위치 기준으로 가까운 충전소를 보여드려요. (위도 {user_lat:.5f}, 경도 {user_lng:.5f})")

    stations = MockApiClient.get_stations(
        car_kind=car_kind,
        n=12,
        user_lat=user_lat,
        user_lng=user_lng,
    )
    stations = sorted(stations, key=lambda x: int(x.get("distance_m", 0) or 0))
    render_stations(stations, max_height_px=320)
