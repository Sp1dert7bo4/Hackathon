# Test / Failure Path

> Phạm vi: khu vực Hà Nội

## 1. Mục đích

File này mô tả các trường hợp kiểm thử, kịch bản lỗi và hành vi dự phòng cho AI agent tư vấn ăn uống.

## 2. Phạm vi

- Các tình huống lỗi khi tìm dữ liệu
- Hành vi fallback khi API chính không khả dụng
- Cách thông báo với user khi dữ liệu không hoàn toàn tin cậy
- Các tiêu chí hoàn thành cho failure path

## 3. Kịch bản chính

### 3.1. Tìm kiếm thất bại vì API timeout

1. User gửi yêu cầu rõ ràng.
2. Search Agent gọi Google Maps API / Foody API.
3. API trả về error timeout hoặc không phản hồi.
4. Hệ thống chuyển sang `Fallback Engine`.
5. Fallback thử các nguồn:
   - Cache nội bộ
   - Database nội bộ
   - Dataset dự phòng
6. Nếu tìm được dữ liệu từ fallback, trả kết quả cho user.
7. Hiển thị thông báo:
   - "Dữ liệu có thể chưa cập nhật theo thời gian thực"

### 3.2. Tìm kiếm thất bại hoàn toàn

1. API chính error.
2. Fallback Engine không tìm được dữ liệu.
3. Trả về message rõ ràng cho user.
4. Đề xuất giải pháp tiếp theo:
   - "Xin lỗi, hiện tại mình chưa tìm được quán phù hợp. Bạn thử lại sau hoặc thay đổi yêu cầu?"

### 3.3. Dữ liệu trả về không đầy đủ / stale

1. API chính thành công nhưng kết quả ít.
2. Fallback Engine cung cấp dữ liệu phụ.
3. Trả kết quả kèm tag `stale_data`.
4. Thông báo user:
   - "Kết quả hiện tại được lấy từ nguồn dự phòng, có thể chưa cập nhật đầy đủ."

## 4. Hành vi hệ thống

- Nếu API chính fail thì luôn thử nguồn dự phòng.
- Nếu fallback thành công, system vẫn trả kết quả nhưng kèm cảnh báo.
- Nếu không có nguồn nào, user nhận được thông báo lỗi thân thiện.
- Nếu user tiếp tục yêu cầu thay đổi, hệ thống giữ trạng thái và tiếp tục tìm lại.

## 5. Test cases

### 5.1. TC1: API timeout + fallback thành công

- Input: "Quán sushi Quận 1"
- Mock: Google Maps API timeout.
- Expect:
  - Gọi fallback
  - Trả list quán từ cache/DB
  - Hiển thị warning về dữ liệu

### 5.2. TC2: API timeout + fallback thất bại

- Input: "Quán buffet giá rẻ"
- Mock: Google Maps API timeout, fallback không có dữ liệu.
- Expect:
  - Thông báo "Không tìm được dữ liệu"
  - Gợi ý user thay đổi yêu cầu

### 5.3. TC3: Dữ liệu fallback stale

- Input: "Lẩu Thái gần Hồ Gươm"
- Mock: API chính fail, fallback trả kết quả cũ.
- Expect:
  - Kết quả trả về
  - Thông báo "Dữ liệu có thể chưa cập nhật theo thời gian thực"

### 5.4. TC4: Nguồn thứ hai thành công khi nguồn chính lỗi

- Input: "Đồ Hàn Cầu Giấy"
- Mock: Foody lỗi, Google Maps thành công.
- Expect:
  - System vẫn trả kết quả từ nguồn thành công.
  - Không cảnh báo fallback.

### 5.5. TC5: API trả về kết quả quá ít

- Input: "Bún chả Hà Nội"
- Mock: API thành công nhưng chỉ trả 1 quán.
- Expect:
  - Trả kết quả với số lượng ít
  - Hiển thị thông báo "Chỉ tìm được 1 quán phù hợp, bạn có muốn mở rộng phạm vi?"

### 5.6. TC6: Lỗi mạng trong quá trình gọi API

- Input: "Cà phê gần Hồ Gươm"
- Mock: kết nối mạng bị mất khi gọi Search Agent.
- Expect:
  - Retry tự động 1 lần
  - Nếu vẫn lỗi, chuyển sang fallback và hiển thị cảnh báo

### 5.7. TC7: API trả về dữ liệu không hợp lệ

- Input: "Đồ ăn chay quận 1"
- Mock: response thiếu fields `rating` hoặc `price_range`.
- Expect:
  - Xử lý lỗi dữ liệu đầu vào
  - Loại bỏ item không hợp lệ hoặc fallback sang nguồn khác

### 5.8. TC8: Cache trả về dữ liệu cũ nhưng API hoàn toàn thất bại

- Input: "Sushi Quận 7"
- Mock: API chính fail, cache có dữ liệu 3 ngày trước.
- Expect:
  - Trả kết quả cache với tag `fallback` và warning stale.
  - Không báo lỗi nếu dữ liệu có thể dùng được.

### 5.9. TC9: Nguồn phụ hoạt động nhưng chất lượng thấp

- Input: "Lẩu Thái giá rẻ"
- Mock: Google Maps timeout, fallback nội bộ có 2 quán rating thấp (<3.5).
- Expect:
  - Trả kết quả kèm cảnh báo chất lượng
  - Gợi ý user thử lại sau hoặc mở rộng yêu cầu

### 5.10. TC10: User nhận dữ liệu fallback nhưng vẫn muốn thử lại

- Input: "Bún đậu mắm tôm"
- Mock: API chính timeout, fallback trả kết quả.
- User tiếp tục: "Bạn thử lại nguồn chính giúp mình"
- Expect:
  - Hệ thống retry API chính nếu có thể
  - Nếu vẫn fail, giữ kết quả fallback và thông báo nguyên do

## 6. Acceptance criteria

- Failure path phải nhận diện và xử lý lỗi API chính.
- Fallback Engine phải được gọi khi cần.
- Nếu fallback thành công, user vẫn nhận kết quả.
- Nếu không có kết quả, user nhận thông báo rõ ràng và gợi ý tiếp.
- User không bị dừng tại lỗi khó hiểu.

## 7. Ghi chú

- Trong prototype, cần thể hiện rõ behavior này ở phần `Failure Path`.
- Với sản phẩm thật, nên có logging chi tiết cho mỗi nguồn lỗi.
- Trường hợp này cũng nên làm test tự động để đảm bảo tính ổn định.
