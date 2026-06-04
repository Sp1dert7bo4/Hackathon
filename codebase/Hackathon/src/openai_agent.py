from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from .intent import detect_out_of_scope_location
from .models import Intent, RankedRestaurant


load_dotenv()

SUPPORTED_HANOI_AREAS = [
    "Hà Nội",
    "Hoàn Kiếm",
    "Cầu Giấy",
    "Ba Đình",
    "Đống Đa",
    "Hai Bà Trưng",
    "Tây Hồ",
    "Thanh Xuân",
    "Hà Đông",
    "Thường Tín",
    "Long Biên",
    "Hoàng Mai",
    "Nam Từ Liêm",
    "Bắc Từ Liêm",
]


def openai_available() -> bool:
    enabled = os.getenv("OPENAI_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    key = os.getenv("OPENAI_API_KEY", "")
    return enabled and bool(key) and key != "your_openai_api_key_here"


def _client() -> OpenAI:
    return OpenAI()


def _model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _json_from_response_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _choose_cuisine(openai_cuisine: str | None, fallback_cuisine: str | None) -> str | None:
    generic_values = {"quán ăn", "nhà hàng", "địa điểm ăn uống", "restaurant"}
    if fallback_cuisine and (not openai_cuisine or openai_cuisine.lower() in generic_values):
        return fallback_cuisine
    return openai_cuisine or fallback_cuisine


def _normalize_budget(value: Any, fallback: int | None) -> int | None:
    budget = value or fallback
    if budget is None:
        return None
    budget = int(budget)
    return budget * 1000 if 0 < budget < 1000 else budget


def _compact_place(item: RankedRestaurant, index: int, can_use_distance: bool) -> dict[str, Any]:
    """Chuyển RankedRestaurant thành dict gọn gàng để truyền vào prompt."""
    r = item.restaurant
    place: dict[str, Any] = {
        "rank": index + 1,
        "name": r.name,
        "address": r.address or None,
        "district": r.district or None,
        "rating": r.rating if r.rating else None,
        "phone": r.phone or None,
        "hours": r.hours if r.hours else None,
        "review_keywords": r.review_keywords[:12] if r.review_keywords else [],
        "about_options": r.about_options if r.about_options else [],
    }
    if can_use_distance and r.distance_km:
        place["verified_distance_km"] = r.distance_km
    # Chỉ giữ các key có giá trị
    return {k: v for k, v in place.items() if v not in (None, [], {})}


# ─────────────────────────────────────────────────────────────────────────────
# INTENT AGENT PROMPT
# Nhiệm vụ: trích xuất ý định người dùng từ câu chat tiếng Việt/Anh,
# hiểu được vibe, occasion ngoài các slot cứng cuisine/location/budget.
# ─────────────────────────────────────────────────────────────────────────────
_INTENT_SYSTEM_PROMPT = f"""Bạn là Intent Agent của FoodFinder AI – hệ thống tư vấn cafe và địa điểm ăn uống tại Hà Nội.

=== PHẠM VI HỖ TRỢ ===
Chỉ hỗ trợ Hà Nội. Khu vực hợp lệ: {", ".join(SUPPORTED_HANOI_AREAS)}.

=== NHIỆM VỤ ===
Đọc câu của người dùng rồi trả về JSON thuần (không markdown, không giải thích) theo schema sau:
{{
  "cuisine": string|null,
  "location": string|null,
  "budget": integer|null,
  "time": string|null,
  "people": integer|null,
  "diet": string|null,
  "vibe": string|null,
  "occasion": string|null,
  "confidence": number,
  "missing_fields": string[],
  "clarification_questions": string[],
  "unsupported_location": string|null
}}

=== HƯỚNG DẪN TỪNG TRƯỜNG ===
- **cuisine**: Thể loại ẩm thực/địa điểm. Ví dụ: "cà phê", "lẩu", "sushi", "đồ Hàn", "buffet", "trà sữa", "bar", "bakery", "đồ chay". Ưu tiên cụ thể hơn chung chung.
- **location**: Quận/khu vực cụ thể tại Hà Nội. Nếu user nói "gần đây/gần tôi/quanh đây/near me" → "Hà Nội".
- **budget**: Ngân sách tối đa mỗi người (VND). "100k" → 100000; "dưới 200k" → 200000.
- **time**: Thời điểm ăn: "breakfast", "lunch", "dinner", "quick", "late-night".
- **people**: Số người đi (nếu nhắc đến).
- **diet**: Chế độ ăn: "vegan", "vegetarian", "chay".
- **vibe**: Không khí/phong cách mong muốn. Ví dụ: "yên tĩnh", "chill", "trendy", "ấm cúng", "sống ảo", "sang trọng", "rooftop", "ngoài trời", "vintage", "artistic", "study", "làm việc", "live music", "thú cưng".
- **occasion**: Dịp đặc biệt: "hẹn hò", "sinh nhật", "gia đình", "nhóm bạn", "họp", "làm việc", "tự học".
- **confidence**: 0.0–1.0. Ngưỡng để tìm kiếm là ≥ 0.7. Đạt 0.7 khi có ĐỦ INFO để lọc địa điểm, dù chỉ cần một trong: cuisine, vibe, occasion, hoặc cả 3 slot cổ điển.
- **missing_fields**: Chỉ liệt kê khi thực sự THIẾU thông tin không thể suy ra. Nếu câu đủ để tìm → để rỗng [].
- **clarification_questions**: Hỏi TỐI ĐA 1 câu quan trọng nhất bằng tiếng Việt thân thiện. Chỉ hỏi khi cần thiết.
- **unsupported_location**: Chỉ set khi user nêu địa điểm RÕ RÀNG ngoài Hà Nội (TP.HCM, Đà Nẵng...).

=== NGUYÊN TẮC CONFIDENCE ===
- ≥ 0.9: Có cuisine + location + budget rõ ràng
- ≥ 0.7: Có cuisine cụ thể (dù không có location/budget) HOẶC có vibe/occasion rõ ràng (ví dụ "học bài", "hẹn hò", "yên tĩnh")
- 0.5–0.69: Câu mơ hồ chung chung như "ăn gì đó", "quán nào ngon", không rõ muốn gì
- < 0.5: Hoàn toàn không rõ ý định

=== LƯU Ý ===
- Hiểu cả tiếng Anh lẫn tiếng Việt.
- Không yêu cầu thêm thông tin khi câu đã đủ để tìm kiếm.
- Đừng nhầm giữa vibe và cuisine (VD: "không gian yên tĩnh" là vibe, không phải cuisine).
"""


# ─────────────────────────────────────────────────────────────────────────────
# ADVISOR / EXPLANATION PROMPT
# Nhiệm vụ: Dựa vào data địa điểm đã được ranked, sinh câu trả lời tự nhiên,
# thân thiện, khai thác triệt để review_keywords, about_options, hours, phone.
# ─────────────────────────────────────────────────────────────────────────────
_ADVISOR_SYSTEM_PROMPT = """Bạn là trợ lý ảo FoodFinder AI.
Nhiệm vụ của bạn là đưa ra MỘT CÂU DUY NHẤT để giới thiệu danh sách các quán ăn/cafe mà hệ thống đã tìm được.

**Độ dài**: RẤT NGẮN, tối đa 1-2 câu (khoảng 10-20 từ).
Ví dụ: "Mình đã tìm thấy vài quán cực kỳ phù hợp với bạn, xem chi tiết ở thẻ bên dưới nhé!"

=== XỬ LÝ TRƯỜNG HỢP ĐẶC BIỆT ===
- Nếu `note` có "Không có GPS" → nói: "Mình tìm theo khu vực vì chưa có vị trí của bạn nhé."
- Nếu `data_warning` không rỗng → thêm: "Dữ liệu có thể chưa cập nhật, bạn nhớ gọi xác nhận nhé!"
- TUYỆT ĐỐI KHÔNG review quán, KHÔNG liệt kê tên quán, KHÔNG giải thích lý do chọn quán. Danh sách quán đã được hiển thị trên giao diện thẻ (Card) rồi.
"""


def enhance_intent_with_openai(text: str, fallback_intent: Intent) -> tuple[Intent, str | None, bool]:
    if not openai_available():
        return fallback_intent, detect_out_of_scope_location(text), False

    try:
        response = _client().responses.create(
            model=_model(),
            instructions=_INTENT_SYSTEM_PROMPT,
            input=text,
        )
        payload = _json_from_response_text(response.output_text)
    except Exception:
        return fallback_intent, detect_out_of_scope_location(text), False

    unsupported_location = payload.get("unsupported_location") or detect_out_of_scope_location(text)
    missing_fields = payload.get("missing_fields") or []
    confidence = float(payload.get("confidence") or fallback_intent.confidence)

    # Merge vibe/occasion vào time để tương thích với ConversationState hiện tại
    vibe = payload.get("vibe") or ""
    occasion = payload.get("occasion") or ""
    time_val = payload.get("time") or fallback_intent.time
    if not time_val:
        time_val = occasion or vibe or None

    intent = Intent(
        cuisine=_choose_cuisine(payload.get("cuisine"), fallback_intent.cuisine),
        location=payload.get("location") or fallback_intent.location,
        budget=_normalize_budget(payload.get("budget"), fallback_intent.budget),
        time=time_val,
        people=payload.get("people") or fallback_intent.people,
        diet=payload.get("diet") or fallback_intent.diet,
        confidence=round(max(0.0, min(confidence, 1.0)), 2),
        low_confidence=confidence < 0.7 or bool(missing_fields),
        missing_fields=missing_fields,
        clarification_questions=payload.get("clarification_questions") or fallback_intent.clarification_questions,
    )
    return intent, unsupported_location, True


def generate_openai_explanation(
    user_text: str,
    ranked: list[RankedRestaurant],
    fallback_explanation: str,
    warning: str | None = None,
    can_use_distance: bool = False,
) -> tuple[str, bool]:
    if not openai_available() or not ranked:
        return fallback_explanation, False

    # Xây dựng payload dữ liệu địa điểm chi tiết
    places = [_compact_place(item, i, can_use_distance) for i, item in enumerate(ranked[:5])]

    prompt_payload: dict[str, Any] = {
        "user_request": user_text,
        "places": places,
    }
    if warning:
        prompt_payload["data_warning"] = warning
    if not can_use_distance:
        prompt_payload["note"] = "Không có GPS của user – không được đề cập khoảng cách hay thời gian di chuyển."

    try:
        response = _client().responses.create(
            model=_model(),
            instructions=_ADVISOR_SYSTEM_PROMPT,
            input=json.dumps(prompt_payload, ensure_ascii=False),
        )
        result = response.output_text.strip()
        return result or fallback_explanation, True
    except Exception:
        return fallback_explanation, False
