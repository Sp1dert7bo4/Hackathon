from __future__ import annotations

from .models import ConversationState, Intent


REQUIRED_SLOTS = ("food_type", "location", "budget")


OCCASION_ALIASES = {
    "hẹn hò": ["hen ho", "hẹn hò", "date", "date night", "ban gai", "bạn gái", "ban trai", "bạn trai", "romantic"],
    "gia đình": ["gia dinh", "gia đình", "family", "kids", "tre em", "trẻ em"],
    "học bài": ["hoc bai", "học bài", "study", "lam viec", "làm việc", "laptop", "yên tĩnh", "yen tinh", "quiet"],
    "nhóm bạn": ["nhom ban", "nhóm bạn", "ban be", "bạn bè", "groups", "tu tap", "tụ tập", "chill"],
    "chụp ảnh": ["chup anh", "chụp ảnh", "song ao", "sống ảo", "check in", "đẹp", "dep"],
}


def _normalize(text: str) -> str:
    from .intent import normalize_text

    return normalize_text(text)


def extract_occasion(text: str, intent: Intent) -> str | None:
    # Nếu Intent Agent (OpenAI) đã tìm ra time/vibe/occasion thì ưu tiên dùng
    if intent.time:
        return intent.time

    normalized = _normalize(text)
    for occasion, aliases in OCCASION_ALIASES.items():
        if any(_normalize(alias) in normalized for alias in aliases):
            return occasion
    return None


def message_mentions_location(text: str, location: str | None) -> bool:
    if not location:
        return False

    from .intent import LOCATIONS

    normalized = _normalize(text)
    target = _normalize(location)
    aliases = LOCATIONS.get(location, [])
    return target in normalized or any(_normalize(alias) in normalized for alias in aliases)


def extract_location_from_dataset(text: str) -> str | None:
    from .data_loader import load_restaurants

    normalized = _normalize(text)
    candidates: list[str] = []
    for item in load_restaurants():
        value = item.district
        normalized_value = _normalize(value)
        if value and len(normalized_value) >= 5 and normalized_value in normalized:
            candidates.append(value)
    if not candidates:
        return None
    return max(candidates, key=len)


def normalize_budget(value: int | None) -> int | None:
    if value is None:
        return None
    return value * 1000 if 0 < value < 1000 else value


def update_conversation_state(
    previous: ConversationState | None,
    intent: Intent,
    user_text: str,
    user_latitude: float | None = None,
    user_longitude: float | None = None,
) -> ConversationState:
    state = previous.model_copy() if previous else ConversationState()
    occasion = extract_occasion(user_text, intent)

    if intent.cuisine:
        state.food_type = intent.cuisine
    dataset_location = extract_location_from_dataset(user_text)
    if dataset_location:
        state.location = dataset_location
    elif intent.location and (state.location is None or message_mentions_location(user_text, intent.location)):
        state.location = intent.location
    if intent.budget:
        state.budget = normalize_budget(intent.budget)
    if occasion:
        state.occasion = occasion
    if user_latitude is not None:
        state.user_latitude = user_latitude
    if user_longitude is not None:
        state.user_longitude = user_longitude

    return state


def has_verified_user_location(state: ConversationState) -> bool:
    return state.user_latitude is not None and state.user_longitude is not None


def missing_required_slots(state: ConversationState, base_intent: Intent | None = None) -> list[str]:
    # Nếu OpenAI đánh giá là có đủ thông tin (confidence >= 0.7 và không low_confidence)
    # thì không ép buộc phải có đủ location hay budget.
    if base_intent and base_intent.confidence >= 0.7 and not base_intent.low_confidence:
        return []
    
    # Nếu có food_type hoặc occasion rõ ràng, thì cũng nới lỏng yêu cầu
    if state.food_type or state.occasion:
        missing = []
        if not state.location and not has_verified_user_location(state):
            missing.append("location")
        # Budget không bắt buộc nếu đã có food_type/occasion
        return missing

    return [slot for slot in REQUIRED_SLOTS if getattr(state, slot) in (None, "")]


def build_slot_questions(state: ConversationState, base_intent: Intent | None = None) -> list[str]:
    missing = missing_required_slots(state, base_intent)
    if not missing:
        return []

    first_missing = missing[0]
    if first_missing == "food_type":
        return ["Bạn muốn ăn món gì, kiểu địa điểm nào, hay có dịp gì đặc biệt không?"]
    if first_missing == "location":
        return ["Bạn muốn tìm quán ở khu vực nào tại Hà Nội vậy?"]
    if first_missing == "budget":
        return ["Ngân sách của bạn khoảng bao nhiêu mỗi người?"]
    return []


def state_to_intent(state: ConversationState, base_intent: Intent) -> Intent:
    missing = missing_required_slots(state, base_intent)
    
    # Nếu missing rỗng thì coi như tự tin
    confidence = base_intent.confidence if not missing else max(base_intent.confidence, 0.35)
    
    # Ghi đè time từ occasion nếu occasion có giá trị
    final_time = state.occasion or base_intent.time

    return Intent(
        intent=base_intent.intent,
        cuisine=state.food_type,
        location=state.location,
        budget=state.budget,
        time=final_time,
        people=base_intent.people,
        diet=base_intent.diet,
        confidence=confidence,
        low_confidence=bool(missing),
        missing_fields=missing,
        clarification_questions=build_slot_questions(state, base_intent),
    )


def describe_collected_state(state: ConversationState) -> str:
    parts = []
    if state.food_type:
        parts.append(f"món/loại quán: {state.food_type}")
    if state.location:
        parts.append(f"khu vực: {state.location}")
    if state.budget:
        parts.append(f"ngân sách: {state.budget:,} VND/người".replace(",", "."))
    if state.occasion:
        parts.append(f"yêu cầu đặc biệt/dịp: {state.occasion}")
    return "; ".join(parts)
