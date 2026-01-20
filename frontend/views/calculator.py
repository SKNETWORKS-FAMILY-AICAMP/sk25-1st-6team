import streamlit as st
from typing import Dict, Union
from api.client import MockApiClient


# -----------------------------
# popup 모드 판별
# -----------------------------
def is_popup_mode() -> bool:
    """
    URL에 popup=1 이 붙으면 팝업(단독) 페이지로 간주
    예) ?menu=무공해차%20보조금%20계산기&popup=1
    """
    params = st.query_params
    return str(params.get("popup", "0")).strip() == "1"


def apply_popup_css():
    """
    팝업 모드에서만:
    - 왼쪽 사이드바 숨김
    - 상단 헤더(햄버거) 숨김
    - (혹시 공통 코드가 만들어낸) '메인으로' 버튼 숨김
    """
    st.markdown(
        """
        <style>
            /* 사이드바 전체 숨김 */
            [data-testid="stSidebar"] { display: none !important; }

            /* 상단 햄버거(≡) 헤더 숨김 */
            [data-testid="stHeader"] { display: none !important; }

            /* 본문 왼쪽 여백 제거 */
            [data-testid="stAppViewContainer"] { margin-left: 0 !important; }

            /*
              '메인으로' 버튼 숨김 (공통 UI에서 삽입된 경우 대비)
              - 화면 상단에 있는 첫 번째 버튼을 숨기는 방식이라,
                혹시 페이지 최상단에 다른 버튼이 있다면 위치 조정이 필요합니다.
              - 현재 스샷 기준(메인으로 버튼이 맨 위 1개)에서는 정확히 먹습니다.
            */
            [data-testid="stAppViewContainer"] [data-testid="stButton"]:first-of-type {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Constants / Options
# -----------------------------
YEARS = list(range(2026, 2031))  # 2026 ~ 2030

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


def calc_subsidy(year: int, do_name: str, si_name: str, car_kind: str) -> Dict[str, str]:
    do_selected = do_name != "- 선택 -"
    si_selected = si_name != "- 선택 -"

    if not (do_selected or si_selected):
        return {
            "status": "need_region",
            "message": "지역(도 또는 시)을 선택하면 보조금 금액을 확인할 수 있습니다.",
            "applied_region": ""
        }

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


def render():
    """
    ✅ 요구사항
    - 팝업(popup=1)에서는: 사이드바/메인으로 버튼 숨김
    - 메인 사이드바로 들어오면: 사이드바 정상 노출
    """
    if is_popup_mode():
        apply_popup_css()

    regions = MockApiClient.get_regions()
    region_names = [r.name for r in regions]

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

    st.markdown(
        """
        <h2 style="text-align:center; margin-bottom:6px;">내 지자체 보조금 알아보기</h2>
        <p style="text-align:center; margin-top:0; color:rgba(49,51,63,.75);">
            구매 조건을 선택하면 예상 보조금을 확인할 수 있습니다.
        </p>
        """,
        unsafe_allow_html=True
    )

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

            r1 = st.columns([1, 1, 1])
            with r1[0]:
                st.selectbox(
                    "구매연도",
                    options=YEARS,
                    index=YEARS.index(st.session_state["year"]),
                    key="year"
                )

            r2 = st.columns(2)
            with r2[0]:
                st.selectbox("도", options=DO_OPTIONS, index=DO_OPTIONS.index(st.session_state["do"]), key="do")
            with r2[1]:
                st.selectbox("시", options=SI_OPTIONS, index=SI_OPTIONS.index(st.session_state["si"]), key="si")

            r3 = st.columns([2, 1])
            with r3[0]:
                st.radio(
                    "차량 구분",
                    options=CAR_KIND_OPTIONS,
                    index=CAR_KIND_OPTIONS.index(st.session_state["car_kind"]),
                    horizontal=True,
                    key="car_kind"
                )

            b1, b2, _b3 = st.columns([1, 1, 6])
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

    result = calc_subsidy(
        year=st.session_state["year"],
        do_name=st.session_state["do"],
        si_name=st.session_state["si"],
        car_kind=st.session_state["car_kind"]
    )

    both_selected = (st.session_state["do"] != "- 선택 -") and (st.session_state["si"] != "- 선택 -")
    if both_selected:
        st.info("도와 시를 모두 선택하셨습니다. **시 선택을 우선 적용**하여 보조금을 계산합니다.")

    st.caption(f"참고: MockApiClient 지역 데이터 {len(region_names)}개 로드됨")

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
            {result["message"]}
        </div>
        """,
        unsafe_allow_html=True
    )
