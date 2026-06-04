from __future__ import annotations

from .data_loader import load_restaurants
from .intent import normalize_text
from .models import Restaurant, SearchRequest, SearchResponse


GENERIC_FOOD_QUERIES = {"quán ăn", "nhà hàng", "restaurant", "ăn uống", "địa điểm ăn uống"}
FOOD_TAGS = {
    "quán ăn",
    "nhà hàng",
    "hàn",
    "korean",
    "bbq",
    "tokbokki",
    "đồ tây",
    "western",
    "pizza",
    "burger",
    "thái",
    "thai",
    "lẩu thái",
    "pad thai",
    "tomyum",
    "trung",
    "chinese",
    "dim sum",
    "mì",
    "lẩu",
    "nướng",
    "sushi",
    "cơm",
    "bún chả",
    "bún đậu",
    "buffet",
    "chay",
}
DRINK_OR_DESSERT_ONLY_TAGS = {"cà phê", "trà", "chè", "dessert", "món ngọt", "bar", "bakery", "study/work"}


def _tag_norms(item: Restaurant) -> set[str]:
    return {normalize_text(tag) for tag in item.cuisine_tags}


def _is_food_place(item: Restaurant) -> bool:
    tags = _tag_norms(item)
    normalized_food_tags = {normalize_text(tag) for tag in FOOD_TAGS}
    normalized_non_food_tags = {normalize_text(tag) for tag in DRINK_OR_DESSERT_ONLY_TAGS}
    return bool(tags & normalized_food_tags) and not tags.issubset(normalized_non_food_tags)


def _matches_cuisine(item: Restaurant, cuisine: str | None) -> bool:
    if not cuisine:
        return True

    target = normalize_text(cuisine)
    tags = _tag_norms(item)
    if target in {normalize_text(term) for term in GENERIC_FOOD_QUERIES}:
        return _is_food_place(item)
    return any(target in tag or tag in target for tag in tags)


def _matches_location(item: Restaurant, location: str | None) -> bool:
    if not location:
        return True
    target = normalize_text(location)
    return target in normalize_text(item.district) or target in normalize_text(item.address)


def _open_matches(restaurants: list[Restaurant], request: SearchRequest, sources: set[str] | None = None) -> list[Restaurant]:
    return [
        item
        for item in restaurants
        if item.status == "open"
        and (sources is None or item.source in sources)
        and _matches_cuisine(item, request.cuisine)
        and _matches_location(item, request.location)
    ]


def search_restaurants(request: SearchRequest, restaurants: list[Restaurant] | None = None) -> SearchResponse:
    restaurants = restaurants or load_restaurants()

    primary_error = request.simulate_failure
    if not primary_error:
        primary = _open_matches(restaurants, request, {"google_maps", "foody"})
        if len(primary) >= 3:
            return SearchResponse(restaurants=primary, source="primary", stale_data=False)
        if primary:
            primary_ids = {row.id for row in primary}
            supplemental = [item for item in _open_matches(restaurants, request) if item.id not in primary_ids]
            if supplemental:
                return SearchResponse(
                    restaurants=primary + supplemental,
                    source="primary+fallback_dataset",
                    stale_data=True,
                    warning="Một phần kết quả được bổ sung từ dataset dự phòng để đủ lựa chọn hơn.",
                )

    fallback = _open_matches(restaurants, request)
    if fallback:
        return SearchResponse(
            restaurants=fallback,
            source="fallback_dataset",
            stale_data=True,
            warning="Dữ liệu được lấy từ nguồn dự phòng, có thể chưa cập nhật theo thời gian thực.",
        )

    loose = [
        item
        for item in restaurants
        if item.status == "open" and (_matches_cuisine(item, request.cuisine) or _matches_location(item, request.location))
    ]
    return SearchResponse(
        restaurants=loose,
        source="fallback_dataset" if loose else "none",
        stale_data=bool(loose),
        warning=(
            "Chỉ tìm được một phần dữ liệu phù hợp, bạn có thể mở rộng khu vực hoặc đổi món."
            if loose
            else "Không tìm được dữ liệu phù hợp. Bạn thử thay đổi món, khu vực hoặc ngân sách nhé."
        ),
    )
