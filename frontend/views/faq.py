# frontend/views/faq.py
import streamlit as st
import re
from api.client import MockApiClient


def _highlight_text(text: str, keyword: str) -> str:
    if not keyword:
        return text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(
        lambda m: f"<span style='background-color:#FFF3B0; font-weight:700;'>{m.group()}</span>",
        text
    )


def render():
    # -----------------------------
    # 1) 더미 FAQ 데이터 가져오기 (DB 접근 X)
    # -----------------------------
    faqs = MockApiClient.get_faqs()

    # -----------------------------
    # 2) 페이지 공통 CSS (검색바/버튼/카드 정렬 개선)
    # -----------------------------
    st.markdown(
        """
        <style>
          /* 페이지 위젯 기본 여백 줄이기 */
          .block-container { padding-top: 1.2rem; }

          /* 타이틀 카드 */
          .faq-title-card{
            background:#fff;
            padding:26px 28px;
            border-radius:14px;
            box-shadow:0 6px 18px rgba(0,0,0,0.08);
            margin-bottom:22px;
          }
          .faq-title-card h2{ margin:0; font-size:34px; font-weight:800; }

          /* 검색바 wrapper */
          .faq-search-wrap{
            display:flex;
            justify-content:center;
            margin: 10px 0 20px 0;
          }

          /* Streamlit form 내부 정렬을 위해, form 아래 첫 row(컬럼) 여백 줄이기 */
          div[data-testid="stForm"] { border: 0; padding: 0; }
          div[data-testid="stForm"] > div { padding: 0 !important; }

          /* 입력창 높이/폰트/라운드/배경 */
          div[data-testid="stTextInput"] input{
            height: 68px;
            padding: 0 18px;
            font-size: 16px;
            border-radius: 14px;
            background: #F3F5F7;
            border: 1px solid #E2E6EA;
            box-sizing: border-box;
          }

          /* input 아래 불필요한 라벨 여백 제거(라벨이 비어있어도 생기는 공간 방지) */
          div[data-testid="stTextInput"] label{ display:none; }

          /* submit 버튼(돋보기) 높이/정렬 */
          div[data-testid="stFormSubmitButton"] button{
            height: 68px;
            width: 68px;
            border-radius: 14px;
            font-size: 22px;
            padding: 0;
            border: 1px solid #E2E6EA;
            box-sizing: border-box;
            display:flex;
            align-items:center;
            justify-content:center;
          }

          /* 버튼 hover 살짝 */
          div[data-testid="stFormSubmitButton"] button:hover{
            filter: brightness(0.98);
          }

          /* FAQ 카드 */
          .faq-card{
            background:#fff;
            padding:22px 22px;
            border-radius:14px;
            box-shadow:0 4px 14px rgba(0,0,0,0.06);
            margin-bottom:16px;
          }
          .faq-q{ margin:0 0 10px 0; font-size:15px; font-weight:700; }
          .faq-a{ margin:0 0 12px 0; font-size:14px; line-height:1.6; white-space:pre-line; }
          .faq-meta{ font-size:12px; color:#6B7280; }
        </style>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------
    # 3) Title Card
    # -----------------------------
    st.markdown(
        """
        <div class="faq-title-card">
          <h2>무공해차에 대한 FAQ</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------
    # 4) Search Bar (오른쪽 돋보기 버튼 / 버튼 클릭 시 검색)
    #    - st.form을 쓰면 입력창과 버튼이 "완전히 같은 높이/정렬"로 고정됩니다.
    # -----------------------------
    if "faq_query" not in st.session_state:
        st.session_state["faq_query"] = ""
    if "faq_search" not in st.session_state:
        st.session_state["faq_search"] = ""

    # 가로 폭 줄이기: 중앙에 55% 정도만 쓰도록 컬럼 비율 조정
    _, center, _ = st.columns([3, 6, 3])

    with center:
        st.markdown('<div class="faq-search-wrap">', unsafe_allow_html=True)

        with st.form("faq_search_form", clear_on_submit=False):
            c1, c2 = st.columns([12, 2], vertical_alignment="center")

            with c1:
                st.text_input(
                    "",
                    placeholder="궁금한 내용을 검색해보세요",
                    key="faq_query"
                )

            with c2:
                submitted = st.form_submit_button("🔍")

            # 버튼을 눌렀을 때만 검색어 확정
            if submitted:
                st.session_state["faq_search"] = st.session_state["faq_query"].strip()

        st.markdown('</div>', unsafe_allow_html=True)

    search_keyword = st.session_state["faq_search"]

    # -----------------------------
    # 5) FAQ List
    # -----------------------------
    shown = 0

    for faq in faqs:
        q_text = faq.question
        a_text = faq.answer

        # 버튼으로 확정된 검색어가 있을 때만 필터링
        if search_keyword:
            haystack = f"{q_text} {a_text}".lower()
            if search_keyword.lower() not in haystack:
                continue

        q_highlight = _highlight_text(q_text, search_keyword)
        a_highlight = _highlight_text(a_text, search_keyword)

        st.markdown(
            f"""
            <div class="faq-card">
              <p class="faq-q"><strong>Q.</strong> {q_highlight}</p>
              <p class="faq-a"><strong>A.</strong> {a_highlight}</p>
              <div class="faq-meta">
                <span>출처: {faq.source}</span>
                <span style="margin-left:12px;">카테고리: {faq.category}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        shown += 1

    if search_keyword and shown == 0:
        st.info("검색 결과가 없습니다. 다른 키워드로 검색해보세요.")
