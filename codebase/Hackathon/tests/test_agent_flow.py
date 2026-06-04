from src.feedback import analyze_feedback
from src.intent import detect_out_of_scope_location, extract_intent
from src.conversation import build_slot_questions, missing_required_slots, state_to_intent, update_conversation_state
from src.models import ConversationState
from src.models import SearchRequest
from src.ranking import rank_restaurants
from src.search import search_restaurants


def test_happy_path_extracts_intent_and_ranks_results():
    intent = extract_intent("Tôi muốn tìm cà phê Hoàn Kiếm dưới 150k/người")

    assert intent.low_confidence is False
    assert intent.cuisine == "cà phê"
    assert intent.location == "Hoàn Kiếm"
    assert intent.budget == 150000

    request = SearchRequest(cuisine=intent.cuisine, location=intent.location, budget=intent.budget)
    search_result = search_restaurants(request)
    ranked = rank_restaurants(search_result.restaurants, request)

    assert len(ranked) >= 3
    assert ranked[0].restaurant.district == "Hoàn Kiếm"
    assert ranked[0].score >= ranked[-1].score


def test_low_confidence_returns_questions():
    intent = extract_intent("Tôi muốn ăn gì đó")

    assert intent.low_confidence is True
    assert "cuisine" in intent.missing_fields
    assert intent.clarification_questions


def test_failure_path_uses_fallback_warning():
    request = SearchRequest(cuisine="cà phê", location="Hoàn Kiếm", budget=150000, simulate_failure=True)
    search_result = search_restaurants(request)

    assert search_result.source == "fallback_dataset"
    assert search_result.stale_data is True
    assert search_result.warning
    assert search_result.restaurants


def test_feedback_updates_ranking_preferences():
    request = SearchRequest(cuisine="cà phê", location="Hoàn Kiếm", budget=100000)
    search_result = search_restaurants(request)
    first_rank = rank_restaurants(search_result.restaurants, request)
    preferences = analyze_feedback("Quá đắt", shown_ids=[first_rank[0].restaurant.id])
    reranked = rank_restaurants(
        search_result.restaurants,
        request,
        excluded_ids=set(preferences["excluded_ids"]),
        prefer_cheaper=preferences["prefer_cheaper"],
    )

    assert preferences["prefer_cheaper"] is True
    assert reranked
    assert reranked[0].restaurant.id != first_rank[0].restaurant.id


def test_detects_out_of_scope_location():
    location = detect_out_of_scope_location("Quán cafe để học bài ở Quận 1 Sài Gòn dưới 100k")

    assert location == "TP Hồ Chí Minh"


def test_nearby_request_is_supported_as_hanoi_scope():
    intent = extract_intent("Quán cafe gần đây dưới 100k")

    assert intent.low_confidence is False
    assert intent.cuisine == "cà phê"
    assert intent.location == "Hà Nội"
    assert intent.budget == 100000


def test_slot_filling_remembers_food_type_across_turns():
    first_intent = extract_intent("Tôi muốn ăn cơm")
    state = update_conversation_state(None, first_intent, "Tôi muốn ăn cơm")

    assert state.food_type == "cơm"
    assert "food_type" not in missing_required_slots(state)
    assert build_slot_questions(state) == ["Bạn muốn tìm quán ở khu vực nào tại Hà Nội vậy?"]

    second_intent = extract_intent("Hai Bà Trưng")
    state = update_conversation_state(state, second_intent, "Hai Bà Trưng")
    merged_intent = state_to_intent(state, second_intent)

    assert state.food_type == "cơm"
    assert state.location == "Hai Bà Trưng"
    assert merged_intent.missing_fields == []
    assert build_slot_questions(state) == []


def test_slot_filling_completes_after_budget():
    state = ConversationState(food_type="cơm", location="Hai Bà Trưng")
    budget_intent = extract_intent("khoảng 100k/người")
    state = update_conversation_state(state, budget_intent, "khoảng 100k/người")

    assert state.food_type == "cơm"
    assert state.location == "Hai Bà Trưng"
    assert state.budget == 100000
    assert missing_required_slots(state) == []


def test_budget_turn_does_not_overwrite_existing_specific_location():
    state = ConversationState(food_type="cơm", location="Hai Bà Trưng")
    noisy_intent = extract_intent("100k")
    noisy_intent.location = "Hà Nội"
    noisy_intent.budget = 100000

    state = update_conversation_state(state, noisy_intent, "100k")

    assert state.location == "Hai Bà Trưng"
    assert state.budget == 100000


def test_small_budget_number_is_treated_as_thousand_vnd():
    state = ConversationState(food_type="cơm", location="Hai Bà Trưng")
    noisy_intent = extract_intent("100k")
    noisy_intent.budget = 100

    state = update_conversation_state(state, noisy_intent, "100k")

    assert state.budget == 100000


def test_location_from_dataset_address_is_supported():
    intent = extract_intent("Cafe Hà Đông dưới 100k")
    state = update_conversation_state(None, intent, "Cafe Hà Đông dưới 100k")

    assert state.location == "Hà Đông"
    assert state.food_type == "cà phê"
    assert state.budget == 100000


def test_thuong_tin_location_is_not_rejected_as_out_of_scope():
    intent = extract_intent("Quán cafe Thường Tín dưới 100k")
    state = update_conversation_state(None, intent, "Quán cafe Thường Tín dưới 100k")

    assert detect_out_of_scope_location("Quán cafe Thường Tín dưới 100k") is None
    assert state.location == "Thường Tín"


def test_supported_dataset_location_overrides_false_out_of_scope():
    from src.main import chat_endpoint
    from src.models import ChatRequest

    response = chat_endpoint(ChatRequest(text="Quán cafe Hà Đông dưới 100k"))

    assert response.status != "unsupported_location"
    assert response.conversation_state.location == "Hà Đông"


def test_no_distance_without_verified_user_coordinates():
    from src.main import chat_endpoint
    from src.models import ChatRequest

    response = chat_endpoint(ChatRequest(text="Quán cafe Hà Đông dưới 100k"))
    reason_text = " ".join(reason for item in response.ranked_restaurants for reason in item.reasons).lower()

    assert response.can_use_distance is False
    assert "km" not in reason_text
    assert "cách bạn" not in reason_text


def test_distance_allowed_only_with_verified_user_coordinates():
    from src.main import chat_endpoint
    from src.models import ChatRequest

    response = chat_endpoint(
        ChatRequest(
            text="Quán cafe Hà Đông dưới 100k",
            user_latitude=20.9800,
            user_longitude=105.7800,
        )
    )
    reason_text = " ".join(reason for item in response.ranked_restaurants for reason in item.reasons).lower()

    assert response.can_use_distance is True
    assert "km" in reason_text


def test_user_location_challenge_gets_correction():
    from src.main import chat_endpoint
    from src.models import ChatRequest

    response = chat_endpoint(ChatRequest(text="Tôi đâu có cung cấp vị trí của tôi ở đâu đâu mà bạn biết"))

    assert response.status == "corrected"
    assert response.can_use_distance is False
    assert "không thể tính khoảng cách" in response.explanation


def test_loader_preserves_new_dataset_fields():
    from src.data_loader import load_restaurants

    restaurants = load_restaurants()
    item = next((row for row in restaurants if row.about_options or row.review_keywords or row.phone or row.hours), None)

    assert item is not None
    assert hasattr(item, "address")
    assert hasattr(item, "phone")
    assert hasattr(item, "hours")
    assert hasattr(item, "about_options")
    assert hasattr(item, "review_keywords")
