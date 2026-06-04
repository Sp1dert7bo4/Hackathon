from __future__ import annotations


def analyze_feedback(feedback: str, reason: str | None = None, shown_ids: list[str] | None = None) -> dict:
    text = f"{feedback} {reason or ''}".lower()
    preferences = {"excluded_ids": shown_ids or []}

    if any(term in text for term in ["xa", "quá xa", "gan", "gần hơn"]):
        preferences["prefer_nearer"] = True
    if any(term in text for term in ["đắt", "dat", "rẻ", "re", "cheap"]):
        preferences["prefer_cheaper"] = True
    if any(term in text for term in ["rating", "uy tín", "thấp", "review"]):
        preferences["min_rating"] = 4.3
    if any(term in text for term in ["không hợp", "khong hop", "khẩu vị", "khau vi"]):
        preferences["ask_more"] = True

    return preferences
