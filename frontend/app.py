import streamlit as st
from views import main, heatmap, calculator, faq  # faq가 없으면 제거하세요


st.set_page_config(
    page_title="Vehicle Air Insight",
    layout="wide"
)

# -------------------------
# popup 모드 판별
# -------------------------
params = st.query_params
is_popup = str(params.get("popup", "0")).strip() == "1"

# -------------------------
# Session State 초기화
# -------------------------
if "sidebar_menu" not in st.session_state:
    st.session_state.sidebar_menu = "지역별 자동차 등록 현황"

if "selected_province" not in st.session_state:
    st.session_state.selected_province = ""

# -------------------------
# 메뉴
# -------------------------
MENU_ITEMS = [
    "지역별 자동차 등록 현황",
    "무공해차 보조금 계산기",
    "무공해차 FAQ",
]

# -------------------------
# current_menu 결정
# - popup이면: 쿼리파라미터 menu만 믿고 사이드바는 그리지 않음
# - 일반이면: 사이드바 버튼 클릭으로 이동
# -------------------------
current_menu = params.get("menu", "지역별 자동차 등록 현황")

# -------------------------
# Sidebar (popup 모드에서는 아예 렌더링 X)
# -------------------------
if not is_popup:
    st.sidebar.title("Menu")
    for item in MENU_ITEMS:
        if st.sidebar.button(item, use_container_width=True):
            st.query_params["menu"] = item
            # popup은 일반 페이지에서는 굳이 유지할 필요 없어서 제거
            if "popup" in st.query_params:
                del st.query_params["popup"]
            st.rerun()

# -------------------------
# Page Routing
# -------------------------
if current_menu == "지역별 자동차 등록 현황":
    main.render()
elif current_menu == "무공해차 보조금 계산기":
    calculator.render()
elif current_menu == "무공해차 FAQ":
    # faq 페이지가 실제로 없다면 이 블록 자체를 지우세요.
    faq.render()
else:
    main.render()
