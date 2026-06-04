# Workflow AI Agent Giải Quyết Vấn Đề Ăn Uống

                                    ## Luồng tổng quan

                                                        ┌──────────────┐
                                                        │    User      │
                                                        └──────┬───────┘
                                                            │
                                                            ▼
                                                    ┌─────────────────┐
                                                    │ Intent Agent    │
                                                    └──────┬──────────┘
                                                            │
                                            ┌───────────────┴───────────────┐
                                            │                               │
                                            ▼                               ▼
                                    Confidence cao                 Confidence thấp

                                            │                               │
                                            ▼                               ▼
                                    Search Agent                  Clarification Agent

                                            │                               │
                                            ▼                               ▼
                                    Restaurant Database      Hỏi thêm thông tin

                                            │                               │
                                            ▼                               ▼
                                    Restaurant Database       Nhận thông tin bổ sung
                                    / Dữ liệu review           │
                                            │                    ▼
                                            └───────────────┬───────────────┘
                                                            │
                                                            ▼
                                                    Ranking Agent

                                                            │
                                                            ▼
                                                Explanation Agent
                                                (Giải thích lựa chọn)

                                                            │
                                                            ▼
                                                    Hiển thị Top 5

                                                            │
                                            ┌───────────────┴───────────────┐
                                            │                               │
                                            ▼                               ▼
                                    Chấp nhận                    Không thích

                                            │                               │
                                            ▼                               ▼
                                        END                     Feedback Agent
                                                                        │
                                                                        ▼
                                                                    Re-ranking
                                                                        │
                                                                        ▼
                                                                    Top 5 mới

                                    ## Luồng chi tiết (kiểu khung block)

                                    ┌──────────┐
                                    │  User    │
                                    └────┬─────┘
                                        │
                                        ▼
                                    Nhập yêu cầu
                                    Ví dụ:
                                    - Ăn tối
                                    - Cầu Giấy
                                    - 150k/người
                                    - Đồ Hàn

                                        │
                                        ▼
                                    ┌─────────────────┐
                                    │ Intent Agent    │
                                    └────┬────────────┘
                                        │
                                        ▼
                                    Trích xuất thông tin
                                    ✓ Món ăn
                                    ✓ Địa điểm
                                    ✓ Ngân sách
                                    ✓ Thời gian

                                        │
                                        ▼
                                    ┌─────────────────┐
                                    │ Search Agent    │
                                    └────┬────────────┘
                                        │
                                        ▼
                                    Google Maps
                                    Foody
                                    Database

                                        │
                                        ▼
                                    Danh sách quán

                                        │
                                        ▼
                                    ┌─────────────────┐
                                    │ Ranking Agent   │
                                    └────┬────────────┘
                                        │
                                        ▼
                                    Xếp hạng
                                    - Khoảng cách
                                    - Rating
                                    - Giá
                                    - Độ phù hợp

                                        │
                                        ▼
                                    Top 5 quán

                                        │
                                        ▼
                                    ┌─────────────────┐
                                    │ Explain Agent   │
                                    └────┬────────────┘
                                        │
                                        ▼
                                    Giải thích
                                    "Tôi đề xuất quán A vì:
                                    - cách 500m
                                    - rating 4.7
                                    - giá 120k"

                                        │
                                        ▼
                                    ┌────────────────┐        ┌──────────────────┐
                                    │ User chọn quán │◄───────│ User không thích │
                                    └────┬───────────┘        └──────────────────┘
                                        │                          │
                                        ▼                          ▼
                                    END                 ┌──────────────────┐
                                                        │ Feedback Agent   │
                                                        └────┬─────────────┘
                                                                │
                                                                ▼
                                                        Sửa đề xuất / Hỏi thêm
                                                                │
                                                                ▼
                                                        Clarification
                                                                │
                                                                ▼
                                                        trở lại Search Agent

                                    ### Low Confidence Path

                                    User nhập quá mơ hồ.

                                    ```
                                    ┌──────────┐
                                    │  User    │
                                    └────┬─────┘
                                        │
                                        ▼
                                    "Tôi muốn ăn gì đó"

                                        │
                                        ▼
                                    ┌─────────────────┐
                                    │ Intent Agent    │
                                    └────┬────────────┘
                                        │
                                        ▼
                                    Confidence = 45%

                                        │
                                        ▼
                                    Không đủ thông tin

                                        │
                                        ▼
                                    AI hỏi lại

                                    - Bạn muốn ăn món gì?
                                    - Khu vực nào?
                                    - Bao nhiêu tiền?

                                        │
                                        ▼
                                    User trả lời

                                    "Đồ nướng
                                    Hoàn Kiếm
                                    200k"

                                        │
                                        ▼
                                    Search Agent

                                        │
                                        ▼
                                    Ranking Agent

                                        │
                                        ▼
                                    Kết quả
                                    ```

                                    ### Failure Path

                                    API lỗi hoặc không tìm được dữ liệu.

                                    ```
                                    ┌──────────┐
                                    │  User    │
                                    └────┬─────┘
                                        │
                                        ▼
                                    Yêu cầu tìm quán

                                        │
                                        ▼
                                    Search Agent

                                        │
                                        ▼
                                    Google Maps API

                                        │
                                        ▼
                                    API Timeout

                                        │
                                        ▼
                                    Fallback Engine

                                        │
                                        ├────► Cache
                                        │
                                        ├────► Database nội bộ
                                        │
                                        └────► Dataset dự phòng

                                        │
                                        ▼
                                    Tìm được dữ liệu

                                        │
                                        ▼
                                    Trả kết quả

                                        │
                                        ▼
                                    Thông báo

                                    "Dữ liệu có thể chưa cập nhật
                                    theo thời gian thực"
                                    ```

                                    ### Correction Path

                                    Người dùng không thích kết quả.

                                    ```
                                    ┌──────────┐
                                    │  User    │
                                    └────┬─────┘
                                        │
                                        ▼
                                    Top 5 quán

                                        │
                                        ▼
                                    User

                                    "Không thích"

                                        │
                                        ▼
                                    Feedback Agent

                                        │
                                        ▼
                                    Phân tích lý do

                                        │
                                        ├─ Quá xa
                                        │
                                        ├─ Quá đắt
                                        │
                                        ├─ Rating thấp
                                        │
                                        └─ Không hợp khẩu vị

                                        │
                                        ▼
                                    Cập nhật Preference

                                        │
                                        ▼
                                    Ranking Agent

                                        │
                                        ▼
                                    Re-rank

                                        │
                                        ▼
                                    Top 5 mới

                                        │
                                        ▼
                                    User hài lòng
```


### Out-of-scope Location Path

User nhập khu vực không thuộc Hà Nội.

Ví dụ:
- “Tìm quán bún bò ở Đà Nẵng”
- “Có quán ăn ngon ở TP.HCM không?”
- “Tìm quán gần biển Nha Trang”

        │
        ▼
Intent Agent trích xuất location

        │
        ▼
Location Validator kiểm tra khu vực

        │
        ▼
Nếu location ≠ Hà Nội

        │
        ▼
AI trả lời:

"Hiện tại hệ thống chỉ hỗ trợ gợi ý quán ăn trong khu vực Hà Nội.
Bạn vui lòng nhập lại khu vực/quận thuộc Hà Nội, ví dụ:
Hoàn Kiếm, Cầu Giấy, Đống Đa, Ba Đình, Hai Bà Trưng..."

        │
        ▼
User nhập lại khu vực tại Hà Nội

        │
        ▼
Quay lại Search Agent
### Ghi chú

- Bố cục khung danh sách giúp trực quan cho từng bước.
- Phần Feedback/Correction là đường lặp để đảm bảo user được recovery.
- Luồng có thể mở rộng cho các trường hợp: ăn nhanh, ăn uy tín, giao hàng.

## Flow chi tiết cho developer

### 1. Input / Output của từng agent

- Intent Agent
  - Input: câu hỏi user thô (text, voice transcript)
  - Output: object `{ intent, cuisine, location, budget, time, people, preference }`
  - Nếu confidence thấp: trả về flag `low_confidence` và các câu hỏi cần bổ sung.

- Clarification Agent
  - Input: `low_confidence` + user profile + history
  - Output: câu hỏi follow-up hoặc list option để user chọn.

- Search Agent
  - Input: thông tin đã trích xuất từ Intent Agent / Clarification
  - Output: raw result từ nguồn tìm kiếm (Google Maps, Foody, DB, dataset nội bộ).
  - Hỗ trợ fallback khi API chính thất bại.

- Ranking Agent
  - Input: raw result + user preference + constraints
  - Output: danh sách quán đã sắp xếp với score chi tiết.
  - Tiêu chí: khoảng cách, rating, giá, độ phù hợp, feedback history.

- Explain Agent
  - Input: top ranked result + score breakdown
  - Output: câu trả lời giải thích, lý do ưu tiên, warning nếu cần.

- Feedback Agent
  - Input: phản hồi user “không thích” / “cần điều chỉnh”
  - Output: nguyên nhân ưu tiên + update preference + trigger re-rank.

### 2. Các thành phần developer cần triển khai

- NLP/Intent extraction
  - Phân tách entity: món ăn, khu vực, ngân sách, thời gian, chế độ ăn.
  - Confidence scoring để xác định low-confidence.

- Data connectors
  - Google Maps API
  - Foody API / web scraping
  - Database nội bộ / cache
  - Dataset dự phòng

- Search pipeline
  - Chạy query theo input
  - Thu thập kết quả từ nhiều nguồn
  - Chuẩn hóa dữ liệu quán: tên, địa chỉ, rating, giá, ảnh, khoảng cách, tags.

- Ranking pipeline
  - Tính score cho từng quán
  - Lọc theo điều kiện bắt buộc
  - Ưu tiên quán phù hợp nhất với user context

- Feedback loop
  - Lưu lại phản hồi user
  - Cập nhật preference / blacklist
  - Re-rank ngay khi có feedback

### 3. Quy ước luồng xử lý

- Nếu `Intent Agent` low confidence:
  - Nhảy sang `Clarification Agent`
  - Sau khi user trả lời, quay lại `Intent Agent` hoặc trực tiếp vào `Search Agent`

- Nếu `Search Agent` thất bại:
  - Chạy `Fallback Engine`
  - Nếu vẫn không có dữ liệu, báo lỗi rõ: “Không tìm được dữ liệu” hoặc “Dữ liệu chưa cập nhật”

- Nếu `Top 5` không được chấp nhận:
  - Chuyển đến `Feedback Agent`
  - Phân tích nguyên nhân
  - Cập nhật preference
  - Tái xếp hạng và trả kết quả mới

### 4. Mô tả task developer theo từng bước

1. Nhận yêu cầu user
   - Xử lý tiền xử lý text.
   - Chuyển sang NLP/Intent extraction.

2. Trích xuất thông tin
   - Lấy entity chính.
   - Áp confidence threshold.

3. Tìm dữ liệu
   - Gọi API chính.
   - Nếu có lỗi, gọi fallback.
   - Chuẩn hóa kết quả.

4. Xếp hạng
   - Tính điểm từng quán.
   - Kiểm tra điều kiện lọc.
   - Chọn top N.

5. Giải thích
   - Sinh câu trả lời rõ ràng.
   - Nêu lý do ưu tiên.

6. Phản hồi
   - Nếu user đồng ý: kết thúc.
   - Nếu user không đồng ý: chạy feedback/correction.

### 5. Gợi ý cấu trúc module

- `intent/`
  - `extractor.py`
  - `confidence.py`
- `search/`
  - `google_maps.py`
  - `foody.py`
  - `fallback.py`
- `ranking/`
  - `scorer.py`
  - `filter.py`
- `explain/`
  - `formatter.py`
  - `template.py`
- `feedback/`
  - `analyzer.py`
  - `preference_updater.py`

### 6. Các điểm cần chú ý cho developer

- Giữ `intent extraction` tách rời với `search`.
- Các nguồn dữ liệu phải chuẩn hóa cùng schema.
- Luồng `low confidence` cần rõ ràng và không gây vòng lặp vô hạn.
- Feedback cần update state user ngay lập tức.
- Error handling cần báo rõ và fallback linh hoạt.

## Specification

### 1. Mục tiêu chính

- Hướng dẫn AI đưa ra gợi ý ăn uống theo input user.
- Xử lý các trường hợp: đủ dữ liệu, không rõ dữ liệu, lỗi nguồn, phản hồi không thích.
- Trả về kết quả top quán với lý do, ưu tiên uy tín và phù hợp.

### 2. Functional requirements

- Nhận input user bằng text/voice và trích xuất intent.
- Phân biệt 3 trạng thái:
  - `Happy path`: đủ thông tin, trả kết quả.
  - `Low-confidence path`: hỏi thêm.
  - `Failure path`: fallback dữ liệu.
- Tìm quán từ các nguồn chính và dự phòng.
- Xếp hạng quán theo tiêu chí cố định.
- Sinh explanations rõ ràng, ngắn gọn.
- Nhận feedback user và tái cân nhắc kết quả.

### 3. Non-functional requirements

- Thời gian trả lời: < 1-2 giây cho response chính, < 3 giây với fallback.
- Độ tin cậy: chỉ trả kết quả khi confidence đủ cao hoặc khi user xác nhận.
- Tính mở rộng: dễ thêm nguồn dữ liệu mới và tiêu chí xếp hạng.
- Bảo trì: các rule feedback và preference phải có thể cập nhật.

### 4. Agent behaviour specification

- Intent Agent:
  - Input: câu user
  - Output: object intent với các field
  - Nếu thiếu field quan trọng, trả `low_confidence`.

- Clarification Agent:
  - Input: low confidence state
  - Output: câu hỏi hoặc lựa chọn chi tiết
  - Điều kiện dừng: user bổ sung đủ thông tin hoặc user từ chối trả lời.

- Search Agent:
  - Input: intent đã xác định
  - Output: raw list quán
  - Nếu API chính thất bại: bật fallback. Nếu fallback thành công thì kèm flag `stale_data`.

- Ranking Agent:
  - Input: raw list + user constraints
  - Output: ranked list với score breakdown
  - Score components: `distance`, `rating`, `price`, `fit_score`, `freshness`.

- Explain Agent:
  - Input: top kết quả và score breakdown
  - Output: text giải thích cùng với 2-3 bullet.

- Feedback Agent:
  - Input: user phản hồi tiêu cực
  - Output: nguyên nhân ưu tiên và action `re-rank` hoặc `ask_more`.

### 5. Data model specification

- `UserRequest`
  - `text`
  - `intent`
  - `cuisine`
  - `location`
  - `budget`
  - `time`
  - `people`
  - `diet`
  - `confidence`

- `Restaurant`
  - `id`
  - `name`
  - `address`
  - `distance`
  - `rating`
  - `price_range`
  - `cuisine_tags`
  - `status`
  - `review_count`
  - `image_url`
  - `source`
  - `last_updated`

- `RankingResult`
  - `restaurant_id`
  - `score`
  - `components`: {distance, rating, price, fit}
  - `rank`

- `Feedback`
  - `user_id`
  - `restaurant_id`
  - `reason`
  - `action`

### 6. API / endpoint spec (nếu cần)

- `POST /api/intent`
  - request: `{ text }`
  - response: `{ intent, entities, confidence }`

- `POST /api/search`
  - request: `{ intent, location, budget, cuisine, time }`
  - response: `{ restaurants, source, stale_data? }`

- `POST /api/rank`
  - request: `{ restaurants, user_profile }`
  - response: `{ ranked_restaurants, explanation }`

- `POST /api/feedback`
  - request: `{ user_id, feedback, reasons }`
  - response: `{ updated_preferences, next_action }`

### 7. Acceptance criteria

- User hỏi rõ thì nhận top 3-5 quán phù hợp với giải thích.
- User hỏi mơ hồ thì AI phải hỏi lại.
- Khi API fail, có fallback và báo “có thể chưa cập nhật”.
- Khi user không thích, hệ thống tái rank và trả top mới.

## C?p nh?t m?i (Day 06)
- T�n ?ng d?ng du?c d?i th�nh **Mom oi an g� :> ??**.
- Giao di?n (UI) chuy?n sang tone m�u Cam hi?n d?i, xo� b? c�c n�t b?m du th?a.
- AI Explanation Agent du?c tinh gi?n d? ch? tr? l?i duy nh?t 1 c�u ng?n g?n, t?i uu tr?i nghi?m d?c.
