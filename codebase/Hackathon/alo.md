# PRODUCT SPEC
## AI Food Recommendation Chatbot
**Nhóm HTDA · Track C — Food & Delivery · Day 06**
**Thành viên:** Đặng Sỹ Tiến · Nguyễn Minh Anh · Nguyễn Trung Dân · Trần Nhất Huy

---

## 1. Bằng chứng (Evidence)
Nỗi đau của người dùng được xác nhận qua hai loại nguồn: trải nghiệm trực tiếp của nhóm và quan sát từ bên ngoài.

### Trải nghiệm trực tiếp (Self-use)
| Quan sát | Path liên quan | Điều học được |
| :--- | :--- | :--- |
| AI gợi ý món theo tâm trạng nhưng không hỏi vị trí người dùng — kết quả không thể hành động được ngay. | Failure | AI cần thu thập location trước khi recommend. |
| App chỉ hiển thị danh sách quán dài, user phải tự lọc theo khoảng cách, ngân sách, khẩu vị. | Failure | Cơ hội để AI hỏi thêm ngữ cảnh rồi trả về 2–3 gợi ý có lọc sẵn. |
| Khi gợi ý không phù hợp, không có cách sửa tiêu chí ngay trong flow — phải bắt đầu lại từ đầu. | Correction | Cần correction flow: user sửa location / budget / preference, AI tạo lại gợi ý. |

### Nguồn bên ngoài nhóm
| Quote / Quan sát | Nguồn | User là ai? | Pain / Failure mode |
| :--- | :--- | :--- | :--- |
| "Nhiều lúc không biết ăn gì dù mở app đồ ăn cả tiếng." | Phỏng vấn nhanh 5 sinh viên trong lớp | Sinh viên | Mất quá nhiều thời gian cho câu hỏi "Hôm nay ăn gì?" |
| Video "50 quán ăn ở Hà Nội nhất định phải ăn" — 72K like, 34K lưu — comment: "xa quá", "quán này đóng rồi". | TikTok @mây (3-24) | Người tìm quán theo chủ đề | Volume lớn nhưng thiếu filter cá nhân — user không chốt được quyết định. |
| User đăng xin địa chỉ quán bún thang ngon ở HN — 118 comment nhưng chỉ ghi tên quán. Ngay trong thread, gợi ý bị phản bác: "Quán ở PĐP đóng cửa rồi" (2 người confirm), "Tuấn Minh Tô Hiến Thành hơi nhạt vị." | Facebook group (StunningLobster2943) | Người tìm quán theo món cụ thể | Dữ liệu cộng đồng nhanh lỗi thời + thiếu filter khẩu vị — user vẫn phải tự kiểm chứng từng quán. |
| User thử chatbot để chốt top 3 bún chả — chatbot trả "Bún chả Ta / Đắc Kim / Hương Liên". Comment: "nghe có Đắc Kim là thấy ko uy tín r." Author: "Con Chat Bot nó bảo vậy. Mình có đồng tình đâu." | Facebook group "Hội suốt ngày hỏi Ăn gì bây giờ nhỉ?" (Pham Huong) | Người dùng đã thử chatbot hiện tại | Chatbot gợi quán sai chất lượng, không dựa trên khẩu vị thực tế. User biết AI sai nhưng không có cách sửa hay phản hồi trong luồng. |

---

## 2. Pain Points
Từ evidence trên, nhóm xác định 4 nỗi đau chính — mỗi pain đều có bằng chứng cụ thể:

| # | Pain Point | Bằng chứng |
| :--- | :--- | :--- |
| **1** | Mất nhiều thời gian suy nghĩ ăn gì — mở app đồ ăn cả tiếng vẫn không chốt được. | "Nhiều lúc không biết ăn gì dù mở app đồ ăn cả tiếng" — phỏng vấn 5 sinh viên. |
| **2** | Khó tìm quán phù hợp với nhu cầu hiện tại — công cụ hiện tại chỉ gợi ý theo tâm trạng, không xét vị trí, ngân sách hay khẩu vị. | Self-use: AI gợi ý món theo mood nhưng không hỏi location -> kết quả không hành động được ngay. |
| **3** | Chọn lầm quán ảnh hưởng tâm lý — tin vào chatbot hoặc gợi ý trên mạng rồi thất vọng. | "Con Chat Bot nó bảo vậy. Mình có đồng tình đâu." + "nghe có Đắc Kim là thấy ko uy tín r" — Facebook group. |
| **4** | Trên mạng đề xuất nhiều quán ở nhiều vị trí khác nhau — phải tự search kiểm tra từng cái. | TikTok "50 quán ở HN" — 72K like nhưng comment: "xa quá", "quán này đóng rồi". Facebook: 118 comment gợi quán bún thang nhưng chỉ toàn tên, không kèm vị trí. |

> **Pain được chọn để giải trong prototype:** Pain #1 và #2 là gốc rễ — nếu AI hỏi đúng ngữ cảnh và trả kết quả có map pin + rating thật, pain #3 và #4 cũng được giảm theo.

---

## 3. Lát cắt để Build (Scope)
Cho sinh viên / người đi làm đang phân vân không biết ăn gì, prototype dùng AI để hỏi mood, vị trí và ngân sách, sau đó gợi ý 3 món / quán phù hợp kèm lý do ngắn, map pin và rating thật. Giải quyết 4 pain points: mất thời gian suy nghĩ, khó tìm quán phù hợp, chọn lầm quán, và phải tự tra vị trí từng nơi. Nếu thiếu vị trí hoặc thông tin quá mơ hồ, AI hỏi lại trước khi recommend.

**Những thứ KHÔNG build trong Day 06:**
* Đặt món / thanh toán trong app
* Crawl dữ liệu quán ăn real-time
* Cá nhân hóa dài hạn theo lịch sử ăn uống

---

## 4. AI Product Canvas

| Ô thành phần | Câu hỏi | Câu trả lời của nhóm |
| :--- | :--- | :--- |
| **Value — Giá trị** | Sản phẩm dành cho ai, đau ở đâu, AI giải được điều gì? | Sinh viên, dân văn phòng, khách du lịch tại Hà Nội — gặp 4 pain points: (1) mất nhiều thời gian suy nghĩ ăn gì, (2) khó tìm quán phù hợp với nhu cầu hiện tại, (3) chọn lầm quán ảnh hưởng tâm lý, (4) trên mạng đề xuất nhiều quán ở nhiều vị trí khác nhau — phải tự search kiểm tra từng cái. AI giải bằng cách hỏi đúng tiêu chí (mood + location + budget) rồi trả 3 gợi ý có map pin + rating thật — có thể hành động ngay, không cần lọc thủ công. |
| **Trust — Niềm tin** | Khi AI sai, user nhận ra thế nào và sửa ra sao? | Evidence thực tế: user đã biết chatbot sai ("Con Chat Bot nó bảo vậy. Mình có đồng tình đâu") nhưng không có cách sửa trong luồng — phải ra hỏi cộng đồng. Prototype xử lý bằng cách trả kết quả kèm lý do ngắn + rating Google Maps để user tự kiểm chứng, và cho phép nhập lại tiêu chí ngay trong chat mà không cần bắt đầu lại. |
| **Feasibility — Tính khả thi** | Chi phí, độ trễ, rủi ro lớn nhất? | Chi phí mỗi lượt gọi API thấp (gợi ý 3 quán ~ 1K token). Rủi ro lớn nhất: dữ liệu quán ăn không cập nhật (quán đóng, sai giờ). Ngưỡng dừng: nếu >30% test case trả quán sai vị trí, cần thêm validation bước. |
| **Tín hiệu học** | Khi user chỉnh sửa, dữ liệu đi về đâu? | Mỗi lần user từ chối gợi ý và nhập lại tiêu chí -> ghi log câu chỉnh sửa. Dữ liệu này dùng để cập nhật tập kiểm thử và tinh chỉnh prompt sau Day 06. |

---

## 5. Tăng năng lực hay Tự động hóa
* **Quyết định:** Augmentation — AI gợi ý, user quyết cuối.
* **Lý do chọn:**
  1. Hậu quả của gợi ý sai còn ở mức chịu được (mất thời gian di chuyển, ăn không ngon) nhưng chưa đủ nghiêm trọng để tự động hóa hoàn toàn.
  2. User muốn cảm giác kiểm soát — họ cần thấy lý do gợi ý trước khi quyết định đi.
  3. Dễ hoàn tác: user chỉ cần gõ lại tiêu chí, không mất gì cả.
* **Human role:** Reviewer & Decider — user đọc 3 gợi ý, chọn hoặc yêu cầu AI thay đổi tiêu chí. AI không tự đặt món hay điều hướng thay user.

---

## 6. Bốn đường đi của trải nghiệm (User Paths)
* **Đường thuận (Happy):** User cung cấp đủ mood + vị trí + ngân sách. AI trả 3 gợi ý quán kèm lý do ngắn, rating từ Google Maps, và map pin để user hình dung vị trí ngay — không cần tra địa chỉ thủ công. User chấp nhận bằng một thao tác.
* **Khi AI không chắc (Low-confidence):** User nhập mơ hồ: "Hôm nay buồn quá" hoặc "Tôi không biết ăn gì". AI nhận biết thiếu ngữ cảnh -> hỏi thêm 2–3 câu: vị trí ở đâu? ngân sách bao nhiêu? thích ăn gì?
* **Khi AI sai (Failure):** AI không tìm được quán phù hợp hoặc dữ liệu thiếu cho khu vực yêu cầu. AI thông báo rõ lý do -> đề xuất mở rộng phạm vi tìm kiếm hoặc thay đổi tiêu chí.
* **Khi user sửa (Correction):** User phản hồi: "quán này xa quá", "đắt quá", "tôi không thích đồ cay". AI tiếp nhận phản hồi -> tạo lại danh sách gợi ý mới phù hợp hơn ngay trong luồng chat.

---

## 7. Những kiểu lỗi đáng lo nhất

### Lỗi #1 — Gợi ý không hành động được vì thiếu vị trí
* **Xuất hiện khi:** User không nhập vị trí hoặc nhập quá mơ hồ ("gần đây", "ở Hà Nội").
* **Ai chịu thiệt / Nặng đến đâu:** User di chuyển đến quán xa hoặc quán không tồn tại -> mất thời gian, mất niềm tin vào hệ thống.
* **Prototype xử lý bằng cách nào:** AI bắt buộc hỏi lại vị trí cụ thể trước khi recommend. Nếu user vẫn mơ hồ, AI hỏi thêm lần 2 rồi mới đưa ra gợi ý có disclaimer.

### Lỗi #2 — Gợi ý sai khẩu vị / chất lượng
* **Xuất hiện khi:** User nhập yêu cầu không có ràng buộc rõ ràng về khẩu vị hoặc chất lượng. Evidence: chatbot gợi Đắc Kim, cộng đồng phản bác ngay "nghe có Đắc Kim là thấy ko uy tín r" — gợi ý sai chất lượng thực tế.
* **Ai chịu thiệt / Nặng đến đâu:** User mất niềm tin vào hệ thống, phải ra hỏi cộng đồng thay vì dùng tiếp chatbot.
* **Prototype xử lý bằng cách nào:** AI hỏi loại món ưa thích và ưu tiên (ngon nổi tiếng / gần / giá rẻ) trước khi recommend. Kết quả kèm rating Google Maps để user tự kiểm chứng.

---

## 8. Kế hoạch kiểm thử và bằng chứng Demo

### Hai đầu vào chuẩn bị sẵn cho Demo
* **Đầu vào 1:** "Tôi đang ở Cầu Giấy, ngân sách 60k, muốn ăn gì đó ấm và no bụng."
  * *Loại:* Happy path — đủ thông tin.
  * *Kết quả kỳ vọng:* AI trả 3 quán kèm tên, lý do, khoảng giá, rating Google Maps và map pin — demo trong <30 giây.
* **Đầu vào 2:** "Hôm nay buồn quá, muốn ăn gì đó ngon."
  * *Loại:* Low-confidence — thiếu location & budget.
  * *Kết quả kỳ vọng:* AI hỏi lại vị trí và ngân sách trước khi recommend — demo recovery path.

### Bằng chứng giữ lại trong repo
* Ảnh chụp màn hình tất cả lần test (cả happy và failure path)
* Nhật ký prompt: các phiên bản prompt đã thử và lý do thay đổi
* Danh sách test case đã chạy kèm kết quả thực tế vs kỳ vọng
* Ghi chú về những đánh đổi nhóm đã cân nhắc (ví dụ: hỏi 2 hay 3 câu khi thiếu thông tin?)

---

## 9. Tổng hợp Phân công & Tiến độ chi tiết (Theo dữ liệu thực tế image_4f4402.png)

Bảng tổng hợp vai trò của từng thành viên gắn liền với tracking đầu việc cụ thể và trạng thái vận hành trong ngày:

| Thành viên | Vai trò chính | Đầu việc cụ thể phụ trách | Trạng thái thực tế | Bằng chứng bàn giao trong repo |
| :--- | :--- | :--- | :--- | :--- |
| **Đặng Sỹ Tiến** | Prototype + Demo Script | Tìm và gom data | 🟢 Done | Link prototype, video/ảnh demo chạy được |
| **Nguyễn Trung Dân** | Research + Repo | Tìm API phù hợp để dùng Google Map | 🟢 Done | Ảnh chụp màn hình evidence, README repo |
| **Trần Nhất Huy** | Engineer + SPEC Lead | Chuẩn bị Mockup | 🟢 Done | Nhật ký prompt, ảnh test failure path |
| **Trần Nhất Huy** | Engineer + SPEC Lead | Chuẩn bị prototype | 🔵 In progress | Nhật ký prompt, ảnh test failure path |
| **Nguyễn Minh Anh** | SPEC + Tester | Hình dung và thiết kế UXUI | 🟢 Done | Test case log, ảnh correction path |
| **Nguyễn Minh Anh** | SPEC + Tester | Chuẩn bị test cases | 🟢 Done | Test case log, ảnh correction path |
| **Nguyễn Minh Anh** | SPEC + Tester | Viết tài liệu | 🔵 In progress | Test case log, ảnh correction path |

---

## 10. Đề xuất bổ sung cải tiến hệ thống

### A. Chỉ số đo lường thành công (Success Metrics)
* **Thời gian ra quyết định (Time-to-Decision):** Giảm thời gian trung bình user chốt được quán ăn từ 60 phút xuống dưới 1.5 phút.
* **Tỷ lệ hoàn thành luồng (Completion Rate):** >80% người dùng chọn được 1 trong 3 quán được gợi ý ở lượt phản hồi đầu tiên của Happy Path.
* **Số lượt chỉnh sửa trung bình (Average Correction Turns):** Số lần user phải gõ lại tiêu chí điều chỉnh (Correction Path) không quá 2 lần trước khi chốt quán.

### B. Nguồn dữ liệu tĩnh cho Prototype Day 06
* **Nguồn gốc dữ liệu:** Toàn bộ cơ sở dữ liệu đóng (Mock-database) gồm 50 - 100 quán ăn phục vụ cho Prototype được trích xuất trực tiếp từ danh sách "Saved Places" (Địa điểm đã lưu) do người dùng thực tế chia sẻ công khai trên các nền t hạn mạng xã hội và cộng đồng ẩm thực để làm bộ dữ liệu thử nghiệm chuẩn.

### C. Kịch bản xử lý rủi ro hệ thống và độ trễ API Google Maps
* **Phía Giao diện (UI/UX):** Khi gọi API gặp độ trễ lớn (>5 giây), trạng thái Loading hiển thị các câu thoại tương tác thông minh (Ví dụ: "AI đang chạy đi hỏi xem quán nào còn bàn quanh bạn nhé...").
* **Cơ chế Fallback:** Nếu API thất bại hoàn toàn, AI tự động chuyển sang sử dụng dữ liệu địa chỉ văn bản thô từ danh sách Saved Places của mock-database kèm dòng cảnh báo: "Hệ thống mất kết nối bản đồ tạm thời, bạn có thể tự tra cứu nhanh địa chỉ này nhé!".

### D. Chính sách bảo mật vị trí và quyền riêng tư (Privacy & Consent)
* **Cơ chế hiển thị:** Chatbot hiển thị thông báo ngắn gọn trước khi nhận vị trí: "Chúng tôi chỉ sử dụng vị trí của bạn để tìm kiếm các quán ăn trong phạm vi gần nhất và cam kết không lưu trữ lịch sử định vị sau khi phiên chat kết thúc". Người dùng có quyền nhập thủ công khu vực (Ví dụ: "Cầu Giấy") thay vì chia sẻ định vị GPS trực tiếp.

---

**Câu chốt build:** Dựa trên evidence rằng app hiện tại gợi ý món ăn chưa xét đến vị trí và chỉ phản hồi theo tâm trạng, nhóm HTDA sẽ build prototype AI gợi ý 3 món/quán phù hợp cho sinh viên và người đi làm đang phân vân không biết ăn gì, để giải quyết pain phải tự lọc quá nhiều lựa chọn, bằng cách AI hỏi thêm mood, location, budget rồi recommend có lý do, và sẽ test failure path khi user không nhập vị trí hoặc nhập nhu cầu quá mơ hồ.