from __future__ import annotations

import re
import unicodedata

from .models import Intent


CUISINES = {
    "lẩu thái": ["lau thai", "lẩu thái", "thai hotpot"],
    "lẩu": ["lau", "lẩu", "hotpot"],
    "sushi": ["sushi", "nhật", "nhat"],
    "hàn": ["han", "hàn", "korean", "tokbokki", "tteokbokki"],
    "nướng": ["nuong", "nướng", "bbq"],
    "bún chả": ["bun cha", "bún chả"],
    "bún đậu": ["bun dau", "bún đậu"],
    "cơm": ["com", "cơm", "rice"],
    "quán ăn": ["quan an", "quán ăn", "an uong", "ăn uống", "restaurant", "nha hang", "nhà hàng"],
    "chay": ["chay", "vegetarian", "vegan"],
    "cà phê": ["ca phe", "cà phê", "coffee", "cafe", "café"],
    "trà": ["tra", "trà", "tea", "matcha"],
    "bakery": ["bakery", "banh", "bánh"],
    "buffet": ["buffet"],
}

CUISINES.update(
    {
        "chè": ["che", "chè", "tao pho", "tào phớ", "khuc bach", "khúc bạch", "mon ngot", "món ngọt", "dessert"],
        "hàn": ["han quoc", "hàn quốc", "do han", "đồ hàn", "quan han", "quán hàn", "korean", "bbq", "tokbokki", "tteokbokki"],
        "thái": ["thai", "thái", "do thai", "đồ thái", "quan thai", "quán thái", "pad thai", "tomyum", "tom yum"],
        "trung": ["trung quoc", "trung quốc", "do trung", "đồ trung", "mon trung", "món trung", "quan trung", "quán trung", "chinese", "dim sum", "dimsum", "mi trung", "mì trung"],
        "đồ tây": ["do tay", "đồ tây", "mon tay", "món tây", "western", "pizza", "burger", "pasta", "steak"],
        "nhà hàng": ["nha hang", "nhà hàng", "restaurant"],
    }
)

LOCATIONS = {
    "Hà Nội": ["ha noi", "hà nội", "gan day", "gần đây", "gan toi", "gần tôi", "near me", "quanh day", "quanh đây"],
    "Hoàn Kiếm": ["hoan kiem", "hoàn kiếm", "hồ gươm", "ho guom"],
    "Cầu Giấy": ["cau giay", "cầu giấy"],
    "Ba Đình": ["ba dinh", "ba đình"],
    "Đống Đa": ["dong da", "đống đa"],
    "Hai Bà Trưng": ["hai ba trung", "hai bà trưng"],
    "Tây Hồ": ["tay ho", "tây hồ"],
    "Thanh Xuân": ["thanh xuan", "thanh xuân"],
    "Hà Đông": ["ha dong", "hà đông"],
    "Thường Tín": ["thuong tin", "thường tín"],
    "Long Biên": ["long bien", "long biên"],
    "Nam Từ Liêm": ["nam tu liem", "nam từ liêm"],
    "Bắc Từ Liêm": ["bac tu liem", "bắc từ liêm"],
    "Hoàng Mai": ["hoang mai", "hoàng mai"],
    "Thanh Trì": ["thanh tri", "thanh trì"],
    "Đông Anh": ["dong anh", "đông anh"],
    "Gia Lâm": ["gia lam", "gia lâm"],
    "Sóc Sơn": ["soc son", "sóc sơn"],
    "Hoài Đức": ["hoai duc", "hoài đức"],
    "Đan Phượng": ["dan phuong", "đan phượng"],
    "Chương Mỹ": ["chuong my", "chương mỹ"],
    "Thanh Oai": ["thanh oai"],
    "Phú Xuyên": ["phu xuyen", "phú xuyên"],
    "Mê Linh": ["me linh", "mê linh"],
    "Sơn Tây": ["son tay", "sơn tây"],
}

TIME_KEYWORDS = {
    "breakfast": ["ăn sáng", "sang", "breakfast"],
    "lunch": ["ăn trưa", "trua", "lunch"],
    "dinner": ["ăn tối", "toi", "dinner"],
    "quick": ["ăn nhanh", "nhanh", "quick"],
}

OUT_OF_SCOPE_LOCATIONS = {
    "TP Hồ Chí Minh": ["ho chi minh", "hcm", "sai gon", "sài gòn", "quan 1", "quận 1", "quan 3", "quận 3", "q1", "q3"],
    "Đà Nẵng": ["da nang", "đà nẵng"],
    "Hải Phòng": ["hai phong", "hải phòng"],
    "Nha Trang": ["nha trang"],
    "Đà Lạt": ["da lat", "đà lạt"],
    "Huế": ["hue", "huế"],
    "Cần Thơ": ["can tho", "cần thơ"],
}


def normalize_text(text: str) -> str:
    try:
        text = text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    text = text.strip().lower()
    decomposed = unicodedata.normalize("NFD", text)
    normalized = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return normalized.replace("đ", "d")


def _find_from_aliases(raw: str, normalized: str, aliases: dict[str, list[str]]) -> str | None:
    for value, terms in aliases.items():
        for term in terms:
            term_norm = normalize_text(term)
            if term.lower() in raw or term_norm in normalized:
                return value
    return None


def _extract_budget(normalized: str) -> int | None:
    patterns = [
        r"duoi\s*(\d+)\s*k",
        r"toi da\s*(\d+)\s*k",
        r"(\d+)\s*k\s*/?\s*(nguoi|người)?",
        r"(\d+)\s*000",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if not match:
            continue
        amount = int(match.group(1))
        if amount < 1000:
            amount *= 1000
        return amount
    return None


def _extract_people(normalized: str) -> int | None:
    match = re.search(r"(\d+)\s*(nguoi|người|ban|bạn)", normalized)
    return int(match.group(1)) if match else None


def detect_out_of_scope_location(text: str) -> str | None:
    normalized = normalize_text(text)
    for location, aliases in OUT_OF_SCOPE_LOCATIONS.items():
        if any(normalize_text(alias) in normalized for alias in aliases):
            return location
    return None


def extract_intent(text: str) -> Intent:
    raw = text.strip().lower()
    normalized = normalize_text(text)
    cuisine = _find_from_aliases(raw, normalized, CUISINES)
    location = _find_from_aliases(raw, normalized, LOCATIONS)
    time = _find_from_aliases(raw, normalized, TIME_KEYWORDS)
    budget = _extract_budget(normalized)
    people = _extract_people(normalized)
    diet = "chay" if any(term in normalized for term in ["chay", "vegan", "vegetarian"]) else None

    missing = []
    if not cuisine:
        missing.append("cuisine")
    if not location:
        missing.append("location")
    if not budget:
        missing.append("budget")

    score = 0.25
    score += 0.25 if cuisine else 0
    score += 0.25 if location else 0
    score += 0.2 if budget else 0
    score += 0.05 if time or people or diet else 0
    confidence = min(score, 1.0)

    questions = []
    if "cuisine" in missing:
        questions.append("Bạn muốn ăn món hoặc kiểu ẩm thực nào?")
    if "location" in missing:
        questions.append("Bạn muốn tìm quanh khu vực nào ở Hà Nội?")
    if "budget" in missing:
        questions.append("Ngân sách khoảng bao nhiêu mỗi người?")

    return Intent(
        cuisine=cuisine,
        location=location,
        budget=budget,
        time=time,
        people=people,
        diet=diet,
        confidence=round(confidence, 2),
        low_confidence=confidence < 0.7,
        missing_fields=missing,
        clarification_questions=questions,
    )
