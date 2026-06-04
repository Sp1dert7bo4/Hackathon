from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import Restaurant


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DATASET = DATA_DIR / "restaurants.json"
DEFAULT_DATASETS = [
    DEFAULT_DATASET,
    DATA_DIR / "places_data_chehanoi.json",
    DATA_DIR / "places_data_quanhan.json",
    DATA_DIR / "places_data_quantay.json",
    DATA_DIR / "places_data_quanthai.json",
    DATA_DIR / "places_data_quantrung.json",
]

DATASET_CATEGORY_TAGS = {
    "restaurants.json": ["cà phê", "cafe", "coffee"],
    "places_data_chehanoi.json": ["chè", "dessert", "món ngọt"],
    "places_data_quanhan.json": ["hàn", "korean", "bbq", "tokbokki", "quán ăn", "nhà hàng"],
    "places_data_quantay.json": ["đồ tây", "western", "pizza", "burger", "quán ăn", "nhà hàng"],
    "places_data_quanthai.json": ["thái", "thai", "lẩu thái", "pad thai", "tomyum", "quán ăn", "nhà hàng"],
    "places_data_quantrung.json": ["trung", "chinese", "dim sum", "mì", "quán ăn", "nhà hàng"],
}

DISTRICTS = [
    "Ba Đình",
    "Ba Vì",
    "Bắc Từ Liêm",
    "Cầu Giấy",
    "Chương Mỹ",
    "Đan Phượng",
    "Đông Anh",
    "Đống Đa",
    "Gia Lâm",
    "Hà Đông",
    "Hai Bà Trưng",
    "Hoài Đức",
    "Hoàn Kiếm",
    "Hoàng Mai",
    "Long Biên",
    "Mê Linh",
    "Mỹ Đức",
    "Nam Từ Liêm",
    "Phú Xuyên",
    "Phúc Thọ",
    "Quốc Oai",
    "Sóc Sơn",
    "Sơn Tây",
    "Tây Hồ",
    "Thạch Thất",
    "Thanh Oai",
    "Thanh Trì",
    "Thanh Xuân",
    "Thường Tín",
    "Ứng Hòa",
]


def _fix_mojibake(value: str) -> str:
    if not isinstance(value, str):
        return value
    if "Ã" not in value and "Ä" not in value and "áº" not in value:
        return value
    try:
        repaired = value.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value
    return repaired if repaired.count("�") <= value.count("�") else value


def _slug(value: str, index: int) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return cleaned[:42] or f"place-{index}"


def _float(value: Any, default: float) -> float:
    try:
        if value in ("", None):
            return default
        return float(str(value).replace(",", "."))
    except ValueError:
        return default


def _int(value: Any, default: int = 0) -> int:
    if value in ("", None):
        return default
    match = re.search(r"\d+", str(value).replace(",", ""))
    return int(match.group(0)) if match else default


def _district_from_address(address: str) -> str:
    lower = address.lower()
    for district in DISTRICTS:
        if district.lower() in lower:
            return district
    parts = [part.strip() for part in address.split(",") if part.strip()]
    return parts[-3] if len(parts) >= 3 else "Hà Nội"


def _combined_text(row: dict[str, Any]) -> str:
    values = [
        row.get("name", ""),
        row.get("address", ""),
        " ".join(str(value) for value in row.get("review_keywords") or []),
        " ".join(str(value) for value in row.get("about_options") or []),
    ]
    return " ".join(values).lower()


def _tags_from_place(row: dict[str, Any], dataset_name: str | None = None) -> list[str]:
    text = _combined_text(row)
    base_tags = list(DATASET_CATEGORY_TAGS.get(dataset_name or "", []))
    dynamic_tags = set()

    if any(term in text for term in ["cafe", "café", "coffee", "cà phê", "caphe"]):
        dynamic_tags.add("cà phê")
    if any(term in text for term in ["tea", "trà", "matcha", "chè", "tào phớ"]):
        dynamic_tags.add("chè" if "chè" in text or "tào phớ" in text else "trà")
    if any(term in text for term in ["bakery", "bread", "bánh", "patisserie", "sourdough"]):
        dynamic_tags.add("bakery")
    if any(term in text for term in ["bar", "beer", "wine", "cocktail"]):
        dynamic_tags.add("bar")
    if any(term in text for term in ["work", "study", "workspace", "co-working", "coworking", "space"]):
        dynamic_tags.add("study/work")
    if any(
        term in text
        for term in [
            "restaurant",
            "nhà hàng",
            "quán ăn",
            "bbq",
            "lẩu",
            "pizza",
            "burger",
            "dim sum",
            "mì",
            "tomyum",
            "pad thai",
        ]
    ):
        dynamic_tags.add("quán ăn")

    for dt in sorted(dynamic_tags):
        if dt not in base_tags:
            base_tags.append(dt)

    if not base_tags:
        base_tags.append("địa điểm ăn uống")
    return base_tags


def _status_from_hours(hours: Any) -> str:
    if isinstance(hours, dict):
        text = " ".join(str(value) for value in hours.values()).lower()
    else:
        text = str(hours or "").lower()
    if "closed" in text:
        return "closed"
    return "open"


def _get_fallback_image(dataset_name: str | None) -> str:
    if not dataset_name:
        return "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80"
    
    name = dataset_name.lower()
    if "cafe" in name or "cà phê" in name:
        return "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=900&q=80"
    if "nhật" in name or "japanese" in name:
        return "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=900&q=80"
    if "thái" in name or "thai" in name:
        return "https://images.unsplash.com/photo-1559314809-0d155014e29e?auto=format&fit=crop&w=900&q=80"
    if "hàn" in name or "korean" in name or "gà rán" in name:
        return "https://images.unsplash.com/photo-1580651315530-69c8e0026377?auto=format&fit=crop&w=900&q=80"
    if "tây" in name or "steak" in name:
        return "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=900&q=80"
    if "phở" in name or "vietnamese" in name:
        return "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?auto=format&fit=crop&w=900&q=80"
    if "trung" in name or "chinese" in name:
        return "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=900&q=80"
    if "chè" in name or "dessert" in name:
        return "https://images.unsplash.com/photo-1551024601-bec78aea704b?auto=format&fit=crop&w=900&q=80"
        
    return "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80"


def _base_item(row: dict[str, Any], index: int, place_id: str, name: str, address: str, dataset_name: str | None = None) -> dict[str, Any]:
    return {
        "id": place_id,
        "name": name,
        "address": address,
        "district": row.get("district") or _district_from_address(address),
        "distance_km": _float(row.get("distance_km"), 1.0 + (index % 12) * 0.2),
        "rating": _float(row.get("rating"), 4.0),
        "review_count": _int(row.get("review_count") or row.get("reviews")),
        "source": row.get("source") or "google_maps",
        "last_updated": row.get("last_updated") or "2026-06-04",
        "image_url": row.get("image_url") or _get_fallback_image(dataset_name),
        "status": row.get("status") or _status_from_hours(row.get("hours", "")),
        "phone": row.get("phone") or None,
        "hours": row.get("hours") or None,
        "about_options": row.get("about_options"),
        "review_keywords": row.get("review_keywords") or [],
        "latitude": row.get("latitude") or None,
        "longitude": row.get("longitude") or None,
    }


def normalize_restaurant_rows(rows: list[dict[str, Any]], dataset_name: str | None = None) -> list[Restaurant]:
    restaurants = []
    seen_ids: set[str] = set()

    for index, raw in enumerate(rows, start=1):
        row = {key: _fix_mojibake(value) if isinstance(value, str) else value for key, value in raw.items()}
        name = row.get("name") or f"Địa điểm {index}"
        address = row.get("address") or "Hà Nội"
        place_id = row.get("id") or _slug(f"{name}-{address}", index)
        if place_id in seen_ids:
            place_id = f"{place_id}-{index}"
        seen_ids.add(place_id)

        item = _base_item(row, index, place_id, name, address, dataset_name)
        if "price_min" in row or "cuisine_tags" in row:
            item.update(
                {
                    **row,
                    "id": place_id,
                    "name": name,
                    "address": address,
                    "district": row.get("district") or _district_from_address(address),
                    "distance_km": _float(row.get("distance_km"), item["distance_km"]),
                    "rating": _float(row.get("rating"), 4.0),
                    "review_count": _int(row.get("review_count") or row.get("reviews")),
                    "source": row.get("source") or "google_maps",
                    "last_updated": row.get("last_updated") or "2026-06-04",
                    "status": row.get("status") or _status_from_hours(row.get("hours", "")),
                    "review_keywords": row.get("review_keywords") or [],
                }
            )
        else:
            item.update(
                {
                    "price_min": 35000,
                    "price_max": 150000,
                    "cuisine_tags": _tags_from_place(row, dataset_name),
                }
            )
        restaurants.append(Restaurant.model_validate(item))

    return restaurants


def _load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return payload["restaurants"] if isinstance(payload, dict) else payload


def _dataset_paths(dataset_path: str | None) -> list[Path]:
    configured = dataset_path or os.getenv("RESTAURANT_DATA_PATH")
    if configured:
        return [Path(part.strip()) for part in configured.split(os.pathsep) if part.strip()]
    return [path for path in DEFAULT_DATASETS if path.exists()]


@lru_cache(maxsize=4)
def load_restaurants(dataset_path: str | None = None) -> list[Restaurant]:
    restaurants: list[Restaurant] = []
    seen_keys: set[tuple[str, str]] = set()

    for path in _dataset_paths(dataset_path):
        for row in _load_rows(path):
            key = ((row.get("name") or "").strip().lower(), (row.get("address") or "").strip().lower())
            if key in seen_keys and any(key):
                continue
            seen_keys.add(key)
            restaurants.extend(normalize_restaurant_rows([row], dataset_name=path.name))

    return restaurants
