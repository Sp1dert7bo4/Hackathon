from __future__ import annotations

import json

import streamlit as st

from src.data_loader import load_restaurants, normalize_restaurant_rows
from src.feedback import analyze_feedback
from src.intent import extract_intent
from src.models import SearchRequest
from src.ranking import build_explanation, rank_restaurants
from src.search import search_restaurants


st.set_page_config(page_title="AI Food Advisor", page_icon="🍽️", layout="wide")


@st.cache_data(show_spinner=False)
def default_dataset():
    return load_restaurants()


def load_uploaded_dataset(uploaded_file):
    payload = json.load(uploaded_file)
    rows = payload.get("restaurants", payload) if isinstance(payload, dict) else payload
    return normalize_restaurant_rows(rows)


def run_pipeline(text: str, restaurants, simulate_failure: bool = False, preferences: dict | None = None):
    intent = extract_intent(text)
    if intent.low_confidence:
        return intent, [], "Cần hỏi thêm thông tin trước khi tìm quán.", None

    request = SearchRequest(
        cuisine=intent.cuisine,
        location=intent.location,
        budget=intent.budget,
        time=intent.time,
        people=intent.people,
        diet=intent.diet,
        simulate_failure=simulate_failure,
    )
    search_result = search_restaurants(request, restaurants=restaurants)
    preferences = preferences or {}
    ranked = rank_restaurants(
        search_result.restaurants,
        request,
        excluded_ids=set(preferences.get("excluded_ids", [])),
        prefer_nearer=bool(preferences.get("prefer_nearer")),
        prefer_cheaper=bool(preferences.get("prefer_cheaper")),
        min_rating=preferences.get("min_rating"),
    )
    return intent, ranked, build_explanation(ranked), search_result.warning


if "last_intent" not in st.session_state:
    st.session_state.last_intent = None
if "shown_ids" not in st.session_state:
    st.session_state.shown_ids = []
if "preferences" not in st.session_state:
    st.session_state.preferences = {}

st.title("AI Food Advisor")
st.caption("Prototype Streamlit mô tả luồng AI Agent tư vấn địa điểm ăn uống/cafe tại Hà Nội.")

with st.sidebar:
    st.header("Dữ liệu")
    uploaded = st.file_uploader("Upload JSON địa điểm", type=["json"])
    simulate_failure = st.toggle("Giả lập API fail để chạy fallback", value=False)
    st.divider()
    st.header("Workflow")
    st.markdown(
        """
        1. Intent Agent: tách món/khu vực/ngân sách.
        2. Clarification Agent: hỏi thêm nếu thiếu dữ liệu.
        3. Search Agent: tìm trong nguồn chính và dataset.
        4. Ranking Agent: chấm điểm theo rating, giá, khoảng cách, độ khớp.
        5. Explain Agent: giải thích top kết quả.
        6. Feedback Agent: cập nhật preference và re-rank.
        """
    )

restaurants = load_uploaded_dataset(uploaded) if uploaded else default_dataset()

metric_cols = st.columns(4)
metric_cols[0].metric("Số địa điểm", len(restaurants))
metric_cols[1].metric("Rating TB", f"{sum(r.rating for r in restaurants) / max(len(restaurants), 1):.2f}")
metric_cols[2].metric("Quận/khu", len({r.district for r in restaurants}))
metric_cols[3].metric("Nguồn", restaurants[0].source if restaurants else "none")

tab_chat, tab_data, tab_spec = st.tabs(["Chatbot", "Dataset", "Mô tả chương trình"])

with tab_chat:
    examples = [
        "Tôi muốn tìm cà phê Hoàn Kiếm dưới 150k/người",
        "Cafe để học bài Cầu Giấy 100k",
        "Trà matcha Ba Đình dưới 120k",
        "Tôi muốn ăn gì đó",
    ]
    prompt = st.text_area("Nhập yêu cầu", value=examples[0], height=100)
    picked = st.selectbox("Gợi ý nhanh", examples)
    if st.button("Dùng gợi ý"):
        prompt = picked

    if st.button("Gợi ý ngay", type="primary"):
        intent, ranked, explanation, warning = run_pipeline(
            prompt,
            restaurants,
            simulate_failure=simulate_failure,
            preferences=st.session_state.preferences,
        )
        st.session_state.last_intent = intent
        st.session_state.ranked = ranked
        st.session_state.shown_ids = [item.restaurant.id for item in ranked]
        st.session_state.explanation = explanation
        st.session_state.warning = warning

    if st.session_state.last_intent:
        st.subheader("Intent Agent")
        st.json(st.session_state.last_intent.model_dump())

        if st.session_state.last_intent.low_confidence:
            st.warning("Yêu cầu còn mơ hồ. Agent cần hỏi thêm:")
            for question in st.session_state.last_intent.clarification_questions:
                st.write(f"- {question}")
        else:
            if st.session_state.get("warning"):
                st.warning(st.session_state.warning)
            st.info(st.session_state.get("explanation", ""))

            for item in st.session_state.get("ranked", []):
                restaurant = item.restaurant
                with st.container(border=True):
                    left, right = st.columns([3, 1])
                    left.subheader(f"{item.rank}. {restaurant.name}")
                    left.write(restaurant.address)
                    left.write(" · ".join(item.reasons))
                    right.metric("Score", f"{item.score:.2f}")
                    right.write(f"⭐ {restaurant.rating}")
                    right.write(f"{restaurant.price_range}")

            feedback = st.radio("Không thích vì lý do gì?", ["Quá xa", "Quá đắt", "Rating thấp", "Không hợp khẩu vị"], horizontal=True)
            if st.button("Re-rank theo feedback"):
                st.session_state.preferences = analyze_feedback(feedback, feedback, st.session_state.shown_ids)
                intent = st.session_state.last_intent
                query_text = " ".join(str(value) for value in [intent.cuisine, intent.location, intent.budget] if value)
                _, ranked, explanation, warning = run_pipeline(query_text, restaurants, True, st.session_state.preferences)
                st.session_state.ranked = ranked
                st.session_state.explanation = explanation
                st.session_state.warning = warning
                st.rerun()

with tab_data:
    st.dataframe(
        [
            {
                "name": item.name,
                "district": item.district,
                "rating": item.rating,
                "price": item.price_range,
                "tags": ", ".join(item.cuisine_tags),
                "address": item.address,
            }
            for item in restaurants
        ],
        use_container_width=True,
    )

with tab_spec:
    st.markdown(
        """
        ### Input / Output chính
        - Input: câu hỏi tự nhiên của người dùng và dataset JSON.
        - Output: top địa điểm phù hợp, score, lý do đề xuất, cảnh báo fallback nếu có.

        ### API nội bộ đang dùng lại
        - `extract_intent`: trích xuất cuisine, location, budget, confidence.
        - `search_restaurants`: lọc nguồn chính/dataset dự phòng.
        - `rank_restaurants`: tính score theo distance, rating, price, fit, freshness.
        - `analyze_feedback`: biến phản hồi xấu thành preference để re-rank.

        ### Dataset upload
        File `places_data.json` dạng `name/rating/reviews/address/phone/hours` được tự động chuẩn hóa thành schema `Restaurant`.
        """
    )
