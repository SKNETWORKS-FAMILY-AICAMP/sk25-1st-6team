import streamlit as st
from views import main

st.set_page_config(
    page_title="Vehicle Air Insight",
    layout="wide"
)

# -------------------------
# Session State 초기화
# -------------------------
if "sidebar_menu" not in st.session_state:
    st.session_state.sidebar_menu = "지역별 자동차 등록 현황"

if "selected_province" not in st.session_state:
    st.session_state.selected_province = ""

# -------------------------
# Sidebar (라우팅 역할)
# -------------------------
params = st.query_params
current_menu = params.get("menu", "지역별 자동차 등록 현황")

MENU_ITEMS = [
    "지역별 자동차 등록 현황",
    "무공해차 보조금 계산기",
    "무공해차 FAQ",
]

st.sidebar.title("Menu")

for item in MENU_ITEMS:
    if st.sidebar.button(item, use_container_width=True):
        st.query_params["menu"] = item
        st.rerun()

# -------------------------
# Page Routing
# -------------------------
if current_menu == "지역별 자동차 등록 현황":
    main.render()
else:
    st.info("아직 구현되지 않은 페이지입니다.")
