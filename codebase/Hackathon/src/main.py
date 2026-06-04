from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .conversation import build_slot_questions, describe_collected_state, has_verified_user_location, missing_required_slots, state_to_intent, update_conversation_state
from .feedback import analyze_feedback
from .intent import detect_out_of_scope_location, extract_intent
from .data_loader import load_restaurants
from .models import (
    ChatRequest,
    ChatResponse,
    ConversationState,
    DirectionsRequest,
    DirectionsResponse,
    FeedbackRequest,
    FeedbackResponse,
    Intent,
    IntentRequest,
    RankRequest,
    RankResponse,
    SearchRequest,
    SearchResponse,
)
from .openai_agent import enhance_intent_with_openai, generate_openai_explanation
from .ranking import build_explanation, rank_restaurants
from .search import search_restaurants
from .serpapi_client import geocode, haversine_km, google_maps_link


app = FastAPI(title="AI Food Advisor", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LEGACY_WEB_DIR = Path("web")
FRONTEND_DIST_DIR = Path("frontend/dist")
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"

if LEGACY_WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=LEGACY_WEB_DIR), name="static")

if FRONTEND_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS_DIR), name="frontend-assets")


def _request_from_intent(intent: Intent, simulate_failure: bool = False) -> SearchRequest:
    return SearchRequest(
        intent=intent.intent,
        cuisine=intent.cuisine,
        location=intent.location,
        budget=intent.budget,
        time=intent.time,
        people=intent.people,
        diet=intent.diet,
        simulate_failure=simulate_failure,
    )


def _request_from_state(intent: Intent, state, simulate_failure: bool = False) -> SearchRequest:
    return SearchRequest(
        intent=intent.intent,
        cuisine=state.food_type,
        location=state.location,
        budget=state.budget,
        time=state.occasion or intent.time,
        people=intent.people,
        diet=intent.diet,
        user_latitude=state.user_latitude,
        user_longitude=state.user_longitude,
        simulate_failure=simulate_failure,
    )


@app.get("/")
def index() -> FileResponse:
    react_index = FRONTEND_DIST_DIR / "index.html"
    if react_index.exists():
        return FileResponse(react_index)
    return FileResponse(LEGACY_WEB_DIR / "index.html")


@app.post("/api/intent", response_model=Intent)
def intent_endpoint(payload: IntentRequest) -> Intent:
    return extract_intent(payload.text)


@app.post("/api/search", response_model=SearchResponse)
def search_endpoint(payload: SearchRequest) -> SearchResponse:
    return search_restaurants(payload)


@app.post("/api/rank", response_model=RankResponse)
def rank_endpoint(payload: RankRequest) -> RankResponse:
    request = SearchRequest(**payload.user_profile)
    ranked = rank_restaurants(payload.restaurants, request)
    return RankResponse(ranked_restaurants=ranked, explanation=build_explanation(ranked))


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    normalized_text = detect_out_of_scope_location.__globals__["normalize_text"](payload.text)
    location_challenge = (
        ("vi tri" in normalized_text and any(term in normalized_text for term in ["toi dau", "chua cung cap", "khong cung cap", "ban biet", "sao ban"]))
        or "chua co gps" in normalized_text
        or "khong co gps" in normalized_text
    )
    if location_challenge:
        state = payload.conversation_state
        return ChatResponse(
            status="corrected",
            intent=Intent(low_confidence=True),
            conversation_state=state if state is not None else ConversationState(),
            explanation=(
                "Bạn nói đúng, mình chưa có vị trí GPS hoặc địa chỉ chính xác của bạn nên không thể tính khoảng cách. "
                "Mình sẽ chỉ gợi ý các quán theo khu vực/dữ liệu địa chỉ hiện có và không nêu khoảng cách cho tới khi có tọa độ đã xác minh."
            ),
            questions=[],
            ai_provider="rules",
            can_use_distance=False,
        )

    base_intent = extract_intent(payload.text)
    turn_intent, out_of_scope_location, used_openai = enhance_intent_with_openai(payload.text, base_intent)
    provider = "openai" if used_openai else "rules"
    state = update_conversation_state(
        payload.conversation_state,
        turn_intent,
        payload.text,
        user_latitude=payload.user_latitude,
        user_longitude=payload.user_longitude,
    )
    intent = state_to_intent(state, turn_intent)
    can_use_distance = has_verified_user_location(state)
    if state.location:
        out_of_scope_location = None
    if out_of_scope_location:
        return ChatResponse(
            status="unsupported_location",
            intent=intent,
            conversation_state=state,
            questions=[
                (
                    f"Hiện tại FoodFinder AI chỉ hỗ trợ khu vực Hà Nội, "
                    f"chưa hỗ trợ {out_of_scope_location}. Bạn vui lòng nhập yêu cầu khác trong Hà Nội."
                )
            ],
            explanation=(
                "Phạm vi dữ liệu hiện tại chỉ bao gồm Hà Nội. "
                "Bạn có thể thử lại với Hoàn Kiếm, Cầu Giấy, Ba Đình, Đống Đa hoặc Tây Hồ."
            ),
            ai_provider=provider,
            can_use_distance=can_use_distance,
        )

    missing_slots = missing_required_slots(state)
    if missing_slots:
        collected = describe_collected_state(state)
        questions = build_slot_questions(state)
        explanation = f"Mình đã ghi nhận: {collected}." if collected else None
        return ChatResponse(
            status="needs_clarification",
            intent=intent,
            conversation_state=state,
            questions=questions,
            explanation=explanation,
            ai_provider=provider,
            can_use_distance=can_use_distance,
        )

    request = _request_from_state(intent, state, payload.simulate_failure)
    search_result = search_restaurants(request)
    ranked = rank_restaurants(
        search_result.restaurants,
        request,
        excluded_ids=set(payload.preferences.get("excluded_ids", [])),
        prefer_nearer=bool(payload.preferences.get("prefer_nearer")),
        prefer_cheaper=bool(payload.preferences.get("prefer_cheaper")),
        min_rating=payload.preferences.get("min_rating"),
    )
    fallback_explanation = build_explanation(ranked)
    explanation, explanation_used_openai = generate_openai_explanation(
        payload.text,
        ranked,
        fallback_explanation,
        search_result.warning,
        can_use_distance=can_use_distance,
    )
    if explanation_used_openai:
        provider = "openai"

    return ChatResponse(
        status="ok" if ranked else "no_results",
        intent=intent,
        conversation_state=state,
        ranked_restaurants=ranked,
        explanation=explanation,
        warning=search_result.warning,
        ai_provider=provider,
        can_use_distance=can_use_distance,
    )


@app.post("/api/feedback", response_model=FeedbackResponse)
def feedback_endpoint(payload: FeedbackRequest) -> FeedbackResponse:
    preferences = analyze_feedback(payload.feedback, payload.reason, payload.shown_restaurant_ids)
    request = _request_from_intent(payload.last_intent, simulate_failure=True)
    search_result = search_restaurants(request)
    ranked = rank_restaurants(
        search_result.restaurants,
        request,
        excluded_ids=set(preferences.get("excluded_ids", [])),
        prefer_nearer=bool(preferences.get("prefer_nearer")),
        prefer_cheaper=bool(preferences.get("prefer_cheaper")),
        min_rating=preferences.get("min_rating"),
    )
    action = "ask_more" if preferences.get("ask_more") else "re-rank"
    return FeedbackResponse(
        updated_preferences=preferences,
        next_action=action,
        ranked_restaurants=ranked,
        explanation=build_explanation(ranked),
    )


@app.post("/api/directions", response_model=DirectionsResponse)
def directions_endpoint(payload: DirectionsRequest) -> DirectionsResponse:
    """
    Bước 3: User đã chọn quán -> geocode + tính khoảng cách + link Google Maps.
    Chỉ tốn 1 SerpApi credit (hoặc 0 nếu quán đã nằm trong cache).
    """
    restaurants = load_restaurants()
    target = next((r for r in restaurants if r.id == payload.restaurant_id), None)

    if not target:
        return DirectionsResponse(
            restaurant_name="Không tìm thấy",
            restaurant_address="",
            error="Không tìm thấy quán với ID này. Vui lòng thử lại.",
        )

    coords = None
    if target.latitude and target.longitude:
        coords = (target.latitude, target.longitude)
    else:
        coords = geocode(target.name, target.address)

    if not coords:
        return DirectionsResponse(
            restaurant_name=target.name,
            restaurant_address=target.address,
            restaurant_phone=target.phone,
            restaurant_hours=target.hours,
            error=(
                "Không thể xác định tọa độ quán lúc này. "
                f"Bạn có thể tìm trên Google Maps: "
                f"https://www.google.com/maps/search/?api=1&query={target.name}+{target.address}"
            ),
        )

    dist = haversine_km(
        payload.user_latitude, payload.user_longitude,
        coords[0], coords[1],
    )
    maps_url = google_maps_link(coords[0], coords[1])

    return DirectionsResponse(
        restaurant_name=target.name,
        restaurant_address=target.address,
        restaurant_phone=target.phone,
        restaurant_hours=target.hours,
        distance_km=dist,
        google_maps_link=maps_url,
    )
