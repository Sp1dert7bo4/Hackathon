"""
SerpApi Google Maps client.
- Geocode: chuyển tên+địa chỉ quán → tọa độ (lat, lng)
- Haversine: tính khoảng cách km giữa 2 điểm GPS
- File cache: lưu tọa độ đã geocode để không gọi API lặp
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

import requests as http_client

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "geocode_cache.json"

# ── In-memory cache ──────────────────────────────────────────────
_cache: dict[str, dict[str, float]] = {}


def _load_cache() -> None:
    """Đọc cache từ file JSON khi module được import."""
    global _cache
    if CACHE_FILE.exists():
        try:
            with CACHE_FILE.open("r", encoding="utf-8") as f:
                _cache = json.load(f)
        except (json.JSONDecodeError, OSError):
            _cache = {}


def _save_cache() -> None:
    """Ghi cache ra file JSON."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_FILE.open("w", encoding="utf-8") as f:
        json.dump(_cache, f, ensure_ascii=False, indent=2)


def _cache_key(name: str, address: str) -> str:
    """Tạo key duy nhất cho mỗi quán."""
    return f"{name.strip().lower()}|||{address.strip().lower()}"


# ── Geocode ──────────────────────────────────────────────────────
def geocode(name: str, address: str) -> tuple[float, float] | None:
    """
    Trả về (latitude, longitude) của quán.
    - Ưu tiên đọc từ cache (0 credit).
    - Nếu chưa có → gọi SerpApi (1 credit) → lưu cache.
    - Nếu API lỗi hoặc không có key → trả None.
    """
    key = _cache_key(name, address)

    # Đọc cache trước
    if key in _cache:
        return _cache[key]["lat"], _cache[key]["lng"]

    # Không có key → không gọi API
    if not SERPAPI_KEY:
        return None

    try:
        resp = http_client.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google_maps",
                "q": f"{name} {address}",
                "api_key": SERPAPI_KEY,
                "hl": "vi",
            },
            timeout=10,
        )
        data = resp.json()

        # SerpApi trả tọa độ trong local_results hoặc place_results
        results = data.get("local_results", [])
        if results:
            gps = results[0].get("gps_coordinates", {})
        else:
            gps = data.get("place_results", {}).get("gps_coordinates", {})

        lat = gps.get("latitude")
        lng = gps.get("longitude")

        if lat is not None and lng is not None:
            _cache[key] = {"lat": float(lat), "lng": float(lng)}
            _save_cache()
            return float(lat), float(lng)

    except Exception:
        pass

    return None


# ── Haversine ────────────────────────────────────────────────────
def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Khoảng cách đường chim bay (km) giữa 2 điểm GPS."""
    R = 6371.0  # Bán kính Trái Đất (km)
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


# ── Google Maps link ─────────────────────────────────────────────
def google_maps_link(lat: float, lng: float) -> str:
    """Tạo link mở Google Maps tại tọa độ."""
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"


# Load cache khi module được import lần đầu
_load_cache()
