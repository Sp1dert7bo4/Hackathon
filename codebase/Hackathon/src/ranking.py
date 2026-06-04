from __future__ import annotations

from statistics import mean

from .intent import normalize_text
from .models import RankedRestaurant, Restaurant, SearchRequest
from .serpapi_client import geocode, haversine_km


def _price_score(item: Restaurant, budget: int | None) -> float:
    if not budget:
        return 0.7
    if item.price_max <= budget:
        return 1.0
    if item.price_min <= budget:
        return 0.72
    over = min((item.price_min - budget) / max(budget, 1), 1)
    return max(0.2, 0.65 - over)


def _fit_score(item: Restaurant, request: SearchRequest, penalties: set[str]) -> float:
    score = 0.55
    tags = [normalize_text(tag) for tag in item.cuisine_tags]
    cuisine = request.cuisine
    diet = request.diet
    vibe = request.time # time is used to store vibe/occasion

    # Khớp món ăn
    if cuisine and any(normalize_text(cuisine) in tag or tag in normalize_text(cuisine) for tag in tags):
        score += 0.35
    
    # Khớp diet
    if diet and normalize_text(diet) in tags:
        score += 0.1

    # Khớp vibe/occasion với keywords hoặc about_options
    if vibe:
        vibe_norm = normalize_text(vibe)
        if any(vibe_norm in normalize_text(kw) for kw in item.review_keywords):
            score += 0.2
        if item.about_options:
            if any(vibe_norm in normalize_text(str(opt)) for opt in item.about_options):
                score += 0.15

    if item.id in penalties:
        score -= 0.45
    return max(0.0, min(score, 1.0))


def _has_verified_user_location(request: SearchRequest) -> bool:
    return request.user_latitude is not None and request.user_longitude is not None


def _reason_text(item: Restaurant, request: SearchRequest, components: dict[str, float]) -> list[str]:
    reasons = []
    
    # Ưu tiên các lý do khớp với nhu cầu đặc biệt (vibe, occasion, món ăn)
    vibe = request.time
    if vibe:
        vibe_norm = normalize_text(vibe)
        matched_kw = [kw for kw in item.review_keywords if vibe_norm in normalize_text(kw)]
        if matched_kw:
            reasons.append(f"Khách hàng nhận xét quán '{matched_kw[0]}', rất hợp với '{vibe}' của bạn.")
        elif item.about_options and any(vibe_norm in normalize_text(str(opt)) for opt in item.about_options):
            reasons.append(f"Có tiện ích phù hợp với nhu cầu '{vibe}'.")

    if request.cuisine and components["fit"] > 0.7:
        reasons.append(f"Đúng món/kiểu quán '{request.cuisine}' bạn đang tìm.")

    if request.location:
        reasons.append(f"Nằm ở khu vực {request.location}.")
        
    # Khoảng cách chỉ hiển thị ở bước "Chỉ đường" (endpoint /api/directions)

    if request.budget and item.price_min <= request.budget:
        reasons.append(f"Giá hợp lý ({item.price_range}).")
        
    # Nếu không đủ 3 lý do, bổ sung các lý do chung
    if len(reasons) < 3 and item.rating >= 4.5:
        reasons.append(f"Đánh giá rất cao ({item.rating:g}/5).")
        
    if len(reasons) < 3 and item.review_keywords:
        reasons.append(f"Đặc trưng: {', '.join(item.review_keywords[:2])}.")

    return reasons[:3]


def rank_restaurants(
    restaurants: list[Restaurant],
    request: SearchRequest,
    excluded_ids: set[str] | None = None,
    prefer_nearer: bool = False,
    prefer_cheaper: bool = False,
    min_rating: float | None = None,
    limit: int = 10,
) -> list[RankedRestaurant]:
    excluded_ids = excluded_ids or set()
    ranked = []

    for item in restaurants:
        if item.id in excluded_ids:
            continue
        if min_rating and item.rating < min_rating:
            continue
        distance_score = 0.5  # Không dùng khoảng cách ở bước gợi ý
        rating_score = max(0.0, min(item.rating / 5, 1))
        price_score = _price_score(item, request.budget)
        fit_score = _fit_score(item, request, excluded_ids)
        freshness = 1.0 if item.source in {"google_maps", "foody"} else 0.72

        distance_weight = 0.0  # Khoảng cách chỉ dùng ở bước "Chỉ đường"
        price_weight = 0.21 + (0.08 if prefer_cheaper else 0)
        rating_weight = 0.28  # Tăng từ 0.23 -> 0.28 (bù distance)
        fit_weight = 0.35     # Tăng từ 0.27 -> 0.35 (bù distance)
        fresh_weight = 0.05
        normalizer = distance_weight + price_weight + rating_weight + fit_weight + fresh_weight

        score = (
            distance_score * distance_weight
            + rating_score * rating_weight
            + price_score * price_weight
            + fit_score * fit_weight
            + freshness * fresh_weight
        ) / normalizer
        components = {
            "distance": round(distance_score, 3),
            "rating": round(rating_score, 3),
            "price": round(price_score, 3),
            "fit": round(fit_score, 3),
            "freshness": round(freshness, 3),
        }
        ranked.append((score, item, components))

    ranked.sort(key=lambda row: row[0], reverse=True)
    top_results = []
    for index, (score, item, components) in enumerate(ranked[:limit]):
        if not item.latitude or not item.longitude:
            coords = geocode(item.name, item.address)
            if coords:
                item.latitude, item.longitude = coords
        
        # Cập nhật distance_km nếu có location user
        if item.latitude and item.longitude and _has_verified_user_location(request):
            item.distance_km = haversine_km(
                request.user_latitude, request.user_longitude,
                item.latitude, item.longitude
            )
            
        top_results.append(
            RankedRestaurant(
                restaurant=item,
                rank=index + 1,
                score=round(score, 3),
                components=components,
                reasons=_reason_text(item, request, components),
            )
        )
    return top_results


def build_explanation(ranked: list[RankedRestaurant]) -> str:
    if not ranked:
        return "Mình chưa tìm được quán phù hợp. Bạn thử nới khu vực, đổi món hoặc bỏ bớt yêu cầu xem sao nhé."
    avg_score = mean(item.score for item in ranked)
    top = ranked[0].restaurant
    return f"Mình ưu tiên {top.name} vì phù hợp yêu cầu nhất; top {len(ranked)} có điểm trung bình {avg_score:.2f}."
