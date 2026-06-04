import json
from src.models import SearchRequest
from src.search import search_restaurants
from src.ranking import rank_restaurants
from src.serpapi_client import geocode, haversine_km

# Giả lập Step 1: User request
req = SearchRequest(
    cuisine="thái",
    location="Đống Đa",
    user_latitude=21.0285,
    user_longitude=105.8542
)

print(f"👉 Yêu cầu: Tìm món '{req.cuisine}' ở khu vực '{req.location}'\n")

# Giả lập Step 2: Tìm và gợi ý quán offline (Pha 1)
search_res = search_restaurants(req)
ranked = rank_restaurants(search_res.restaurants, req, limit=3)

print("✅ Đã tìm được Top 3 quán (Offline, 0 API credit):")
for r in ranked:
    print(f"  {r.rank}. {r.restaurant.name} | Rating: {r.restaurant.rating}⭐ | Lĩnh vực: {', '.join(r.restaurant.cuisine_tags[:2])}")
    print(f"     📍 {r.restaurant.address}")
    for reason in r.reasons:
        print(f"     💬 {reason}")
    print()

# Giả lập Step 3: User chọn quán Top 1 để xin chỉ đường (Pha 2)
if ranked:
    top1 = ranked[0].restaurant
    print(f"\n🗺️ User bấm nút 'Chỉ đường' cho quán '{top1.name}':")
    
    # Geocode online
    coords = geocode(top1.name, top1.address)
    if coords:
        print(f"  > Đã gọi SerpApi lấy tọa độ: {coords}")
        dist = haversine_km(req.user_latitude, req.user_longitude, coords[0], coords[1])
        print(f"  > Tính khoảng cách Haversine: {dist} km")
        print(f"\n🚗 Cách bạn khoảng {dist} km.")
        print(f"🔗 Xem trên bản đồ: https://www.google.com/maps/search/?api=1&query={coords[0]},{coords[1]}")
    else:
        print("  > Lỗi không thể lấy tọa độ từ SerpApi.")
