# Prototype AI Agent Tư Vấn Ăn Uống

## 1. Mục đích

Tài liệu này mô tả prototype cho ứng dụng/giao diện AI tư vấn ăn uống. File cần có:

- Mô tả mục tiêu sản phẩm
- User flow chính và các path quan trọng
- Prototype UI cơ bản dưới dạng mockup text
- Tương tác chính và hành vi của agent
- Data model, API và acceptance criteria

## 2. Phạm vi

Ứng dụng tập trung vào khu vực Hà Nội, ví dụ: Hoàn Kiếm, Cầu Giấy, Hai Bà Trưng, Gia Lâm , Ba Đình.

Ứng dụng tập trung vào:

- Tư vấn món ăn và quán ăn dựa trên yêu cầu user
- Hiển thị top 3-5 quán đề xuất
- Giải thích lý do đề xuất
- Xử lý các trường hợp thiếu dữ liệu, lỗi nguồn và feedback

## 3. Audience

- Product owner
- Developer backend/AI
- Developer frontend/UI
- UX designer

## 4. Yêu cầu chính của một prototype

1. Mô tả luồng người dùng rõ ràng
2. Hiển thị các màn hình chính và hành vi
3. Chỉ rõ inputs/outputs cho mỗi agent/module
4. Nêu ra các tình huống ưu tiên/edge cases
5. Đưa ra acceptance criteria cụ thể

## 5. User flow chính

### 5.1. Màn hình nhập yêu cầu

User nhập một câu yêu cầu ăn uống: ví dụ
- "Tôi muốn ăn lẩu Thái gần Hồ Gươm dưới 200k/người"
- "Gợi ý quán sushi uy tín Quận 1"
- "Ăn nhanh, đồ Hàn, 150k/người"

### 5.2. Backend xử lý

- `Intent Agent` trích xuất thông tin
- Nếu thiếu dữ liệu: vào `Clarification Agent`
- Nếu dữ liệu đủ: vào `Search Agent`
- `Search Agent` gọi nguồn dữ liệu
- `Ranking Agent` xếp hạng kết quả
- `Explain Agent` tạo text trả về

### 5.3. Màn hình hiển thị kết quả

Hiển thị: top 3 quán, ảnh, rating, giá, distance, nút chọn/quay lại.

### 5.4. Phản hồi sau kết quả

- Nếu user chọn quán: kết thúc
- Nếu user không thích: vào `Feedback Agent`
- Nếu user sửa yêu cầu: vào `Correction Path`

## 6. Các path quan trọng

### 6.1. Happy path

Input rõ ràng → Intent Agent → Search → Rank → Explain → Hiển thị Top 3

### 6.2. Low-confidence path

Input mơ hồ → Intent Agent confidence thấp → AI hỏi thêm → User bổ sung → Search → Rank → Hiển thị

### 6.3. Failure path

Search API lỗi/timeout → Fallback Engine (cache, DB nội bộ, dataset dự phòng) → Hiển thị với cảnh báo dữ liệu có thể chưa cập nhật

### 6.4. Correction path

User không thích → Feedback Agent phân tích lý do → Cập nhật preference → Re-rank → Hiển thị Top mới

## 7. Prototype UI mockups

### 7.1. Màn hình nhập yêu cầu

```
+-------------------------------------------------------+
| [Icon] AI Food Advisor                               |
+-------------------------------------------------------+
| Bạn muốn ăn gì hôm nay?                              |
| [ Tôi muốn ăn lẩu Thái gần Hồ Gươm dưới 200k/người ] |
| [ Gợi ý ngay ]                                       |
+-------------------------------------------------------+
| Gợi ý nhanh: Ăn tối, Đồ Hàn, Khu vực nổi tiếng         |
+-------------------------------------------------------+
```

### 7.2. Màn hình hỏi bổ sung (nếu low-confidence)

```
+-------------------------------------------------------+
| AI: Bạn muốn ăn món gì?                               |
| [ ] Lẩu  [ ] Nướng  [ ] Sushi  [ ] Khác               |
+-------------------------------------------------------+
| AI: Khu vực nào?                                      |
| [ ] Quận Hai Bà Trưng  [ ] Cầu Giấy  [ ] Hoàn Kiếm  [ ] Khác      |
+-------------------------------------------------------+
| AI: Ngân sách bao nhiêu?                              |
| [ ] <100k  [ ] 100-200k  [ ] 200-300k  [ ] Khác        |
+-------------------------------------------------------+
```

### 7.3. Màn hình kết quả top đề xuất

```
+-------------------------------------------------------+
| Top 3 quán đề xuất                                    |
+-------------------------------------------------------+
| 1. Lẩu Thái Deli          4.6 ★  | 700m | 150-200k |
|    Vì: gần Hồ Gươm, rating tốt, giá phù hợp           |
|    [Xem chi tiết] [Chọn quán]                         |
+-------------------------------------------------------+
| 2. Siam Thai Kitchen      4.5 ★  | 900m | 150-250k |
|    Vì: review mới, phong cách Thái ngon                |
|    [Xem chi tiết] [Chọn quán]                         |
+-------------------------------------------------------+
| 3. Coco Thai              4.4 ★  | 1.2km| 120-180k |
|    Vì: không gian ổn, phù hợp nhóm nhỏ                |
|    [Xem chi tiết] [Chọn quán]                         |
+-------------------------------------------------------+
| [Xem thêm 2 quán khác]                                |
+-------------------------------------------------------+
```

### 7.4. Màn hình feedback

```
+-------------------------------------------------------+
| Bạn có muốn điều chỉnh kết quả không?                 |
| [ Quá xa ] [ Quá đắt ] [ Rating thấp ] [ Không hợp ]  |
+-------------------------------------------------------+
| AI: Mình đã hiểu, mình sẽ tìm lại với tiêu chí mới.     |
+-------------------------------------------------------+
```

## 8. Specification cần có trong prototype

### 8.1. Data model

- UserRequest
  - text, intent, cuisine, location, budget, time, people, diet, confidence
- Restaurant
  - id, name, address, distance, rating, price_range, cuisine_tags, status, review_count, image_url, source, last_updated
- RankingResult
  - restaurant_id, score, components, rank
- Feedback
  - user_id, restaurant_id, reason, action

### 8.2. API endpoint

- `POST /api/intent`
- `POST /api/search`
- `POST /api/rank`
- `POST /api/feedback`

### 8.3. Acceptance criteria

- Input rõ thì trả top 3-5 quán phù hợp có giải thích.
- Input mơ hồ thì AI hỏi thêm.
- API fail thì fallback và cảnh báo.
- Feedback không thích thì tái rank.

## 9. Ghi chú prototype

- Prototype nên thể hiện rõ hành vi user/agent, không cần UI hoàn chỉnh.
- Dùng mockup text để minh hoạ màn hình.
- Tập trung vào các màn hình chính: nhập yêu cầu, hỏi bổ sung, kết quả, feedback.
- Prototype cũng nên nêu rõ dữ liệu cơ bản cần hiển thị.
