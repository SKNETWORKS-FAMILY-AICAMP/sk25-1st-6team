import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from urllib.parse import quote

from api.client import MockApiClient


# -----------------------------
# Helpers
# -----------------------------
def _safe_label(value, fallback: str = "전체") -> str:
    if value is None:
        return fallback
    s = str(value).strip()
    if s == "" or s.lower() in {"none", "null"}:
        return fallback
    return s


def get_filters_from_session_or_defaults():
    """
    메인 페이지에서 넘어온 값을 session_state로 받는 것을 가정.
    값이 없으면 데모 기본값을 사용.
    """
    defaults = {
        "sido": "제주특별자치도",
        "sigungu": "제주시",
        "year": 2026,
        "vehicle_type": "승용",
        "usage": "자가용",
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    return {
        "sido": st.session_state.get("sido"),
        "sigungu": st.session_state.get("sigungu"),
        "year": st.session_state.get("year"),
        "vehicle_type": st.session_state.get("vehicle_type"),
        "usage": st.session_state.get("usage"),
    }


def render_filter_summary(filters: dict):
    sido = _safe_label(filters.get("sido"), "전체")
    sigungu = _safe_label(filters.get("sigungu"), "전체")
    year = _safe_label(filters.get("year"), "전체")
    vehicle_type = _safe_label(filters.get("vehicle_type"), "전체")
    usage = _safe_label(filters.get("usage"), "전체")

    region_label = sido if sigungu == "전체" else sigungu

    st.markdown(
        f"""
        <div style="
            width: 100%;
            border: 1px solid rgba(0,0,0,0.12);
            border-radius: 16px;
            padding: 18px 18px;
            background: rgba(0,0,0,0.02);
            margin: 14px 0 18px 0;
        ">
          <div style="text-align:center; color:#666; font-weight:600; font-size:14px;">
            Data Visualization Detail Page
          </div>

          <div style="text-align:center; font-weight:900; font-size:32px; margin-top:10px;">
            사용자 선택 조건
          </div>

          <div style="display:flex; justify-content:center; gap:10px; flex-wrap:wrap; margin-top:14px;">
            <span style="padding:7px 16px; border-radius:999px; background:#eef2ff; color:#3730a3; font-weight:800;">
              📍 {region_label}
            </span>
            <span style="padding:7px 16px; border-radius:999px; background:#ecfeff; color:#155e75; font-weight:800;">
              📅 {year}년
            </span>
            <span style="padding:7px 16px; border-radius:999px; background:#f0fdf4; color:#166534; font-weight:800;">
              🚗 {vehicle_type}
            </span>
            <span style="padding:7px 16px; border-radius:999px; background:#fff7ed; color:#9a3412; font-weight:800;">
              🧾 {usage}
            </span>
          </div>

          <div style="text-align:center; margin-top:10px; color:#555; font-size:14px; font-weight:600;">
            현재 선택한 조건을 기준으로 시각화된 결과입니다.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def make_dummy_heatmap_matrix(seed: int, size: int = 120) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = np.linspace(-2.5, 2.5, size)
    y = np.linspace(-2.5, 2.5, size)
    X, Y = np.meshgrid(x, y)

    cx, cy = rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8)
    sx, sy = rng.uniform(0.6, 1.2), rng.uniform(0.6, 1.2)

    Z = np.exp(-(((X - cx) ** 2) / (2 * sx**2) + ((Y - cy) ** 2) / (2 * sy**2)))
    Z += 0.35 * np.exp(-(((X + cx) ** 2) / (2 * (sx * 1.2) ** 2) + ((Y + cy) ** 2) / (2 * (sy * 1.2) ** 2)))
    Z += rng.normal(0, 0.06, size=(size, size))
    Z = np.clip(Z, 0, None)
    return Z


def render_heatmaps(filters: dict):
    st.write("")
    col1, col2 = st.columns(2, gap="medium")

    seed_base = abs(
        hash(
            f"{filters.get('sido')}_{filters.get('sigungu')}_{filters.get('year')}_{filters.get('vehicle_type')}_{filters.get('usage')}"
        )
    ) % (2**31)

    with col1:
        Z_reg = make_dummy_heatmap_matrix(seed=seed_base + 1)
        fig = plt.figure(figsize=(4, 3))
        plt.imshow(Z_reg, aspect="auto")
        plt.axis("off")
        st.pyplot(fig, use_container_width=False)

        st.markdown(
            "<div style='text-align:center; font-weight:700; margin-top:6px;'>Vehicle Registration Heatmap</div>",
            unsafe_allow_html=True,
        )

    with col2:
        Z_air = make_dummy_heatmap_matrix(seed=seed_base + 2)
        fig = plt.figure(figsize=(4, 3))
        plt.imshow(Z_air, aspect="auto")
        plt.axis("off")
        st.pyplot(fig, use_container_width=False)

        st.markdown(
            "<div style='text-align:center; font-weight:700; margin-top:6px;'>Air Quality Heatmap</div>",
            unsafe_allow_html=True,
        )

    return Z_reg, Z_air


def render_analysis_text(Z_reg: np.ndarray, Z_air: np.ndarray):
    r = np.corrcoef(Z_reg.flatten(), Z_air.flatten())[0, 1]
    r = float(r)

    st.markdown("### 데이터 해석")

    st.markdown(
        """
        <div style="
            text-align:center;
            font-size: 28px;
            font-weight: 800;
            line-height: 1.6;
            margin-top: 10px;
            margin-bottom: 10px;
        ">
            <div>자동차 등록 밀집 구역과 대기질 악화 구역이 일부 겹쳐 나타납니다.</div>
            <div>이는 차량 통행·등록 집중이 대기질에 영향을 줄 수 있음을 시사합니다.</div>
            <div>해당 결과는 참고용이며, 기상·산업·지형 등 다양한 요인도 함께 고려해야 합니다.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size: 18px;
            font-weight: 700;
            color: #444;
            margin-bottom: 10px;
        ">
            (참고) 두 지표 간 상관계수: {r:.2f}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")


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
    - Streamlit 내부 모달로 다른 .py 페이지를 띄우는 건 불가하므로,
      브라우저 window.open()으로 새 창을 여는 방식입니다.
    - 팝업 차단이 켜져 있으면 새 창이 막힐 수 있습니다.
    """

    # app.py 라우팅에서 사용하는 메뉴 값과 반드시 동일해야 합니다.
    menu_value = "무공해차 보조금 계산기"
    popup_url = f"?menu={quote(menu_value)}"

    # 버튼을 가운데 정렬 + 기존 스타일 유지
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
        // 팝업(새 창) 옵션: 너비/높이/스크롤 등
        const features = "width=1100,height=800,scrollbars=yes,resizable=yes";
        window.open("{popup_url}", "_blank", features);
      }});
    </script>
    """

    # height는 HTML 영역 높이
    components.html(html, height=90)


def render():
    """
    app.py 라우팅에서 호출되는 Heatmap 페이지 렌더 함수
    - DB 직접 접근 금지
    - MockApiClient(더미) 기반 흐름 유지
    """
    st.markdown("## 히트맵 분석 (상세 페이지)")

    reg_stats = MockApiClient.get_registration_stats()
    air_stats = MockApiClient.get_air_pollution_stats()
    st.caption(f"더미 데이터 기반: 등록통계 {len(reg_stats)}건, 대기질 {len(air_stats)}건")

    with st.expander("데모용 입력(메인 페이지에서 넘어온 필터 값을 흉내냄)", expanded=False):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.session_state["sido"] = st.text_input(
                "sido(시/도)", value=st.session_state.get("sido", "제주특별자치도")
            )
        with c2:
            st.session_state["sigungu"] = st.text_input(
                "sigungu(시/군/구)", value=st.session_state.get("sigungu", "제주시")
            )
        with c3:
            st.session_state["year"] = st.number_input(
                "year(연도)", min_value=2000, max_value=2100,
                value=int(st.session_state.get("year", 2026))
            )
        with c4:
            st.session_state["vehicle_type"] = st.text_input(
                "vehicle_type(차종)", value=st.session_state.get("vehicle_type", "승용")
            )
        with c5:
            st.session_state["usage"] = st.text_input(
                "usage(용도)", value=st.session_state.get("usage", "자가용")
            )

    filters = get_filters_from_session_or_defaults()

    render_filter_summary(filters)
    Z_reg, Z_air = render_heatmaps(filters)
    render_analysis_text(Z_reg, Z_air)
    render_cta()

    # ✅ 여기서 팝업 버튼 렌더
    render_subsidy_popup_button()
