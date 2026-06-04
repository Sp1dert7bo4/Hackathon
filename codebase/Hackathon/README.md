# AI Food Advisor

Ứng dụng full stack prototype cho chatbot tư vấn quán ăn khu vực Hà Nội.

## Chạy ứng dụng

## Bật OpenAI cho chatbot thông minh hơn

Tạo file `.env` từ mẫu:

```powershell
copy .env.example .env
```

Mở `.env` và điền key:

```text
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.2
OPENAI_ENABLED=true
```

Sau đó cài dependency và restart backend:

```powershell
pip install -r requirements.txt
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Khi chưa có key hoặc OpenAI lỗi, app tự fallback về rule-based logic hiện tại.

### React + Tailwind UI

Chạy full stack development bằng 2 terminal:

Terminal 1:

```powershell
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
cd frontend
npm install
npm run dev
```

Mở `http://127.0.0.1:5173`.

UI **FoodFinder AI** sẽ gọi backend qua `/api/chat` và `/api/feedback`.

Sau khi build frontend, FastAPI cũng có thể serve UI React tại `http://127.0.0.1:8000`:

```powershell
cd frontend
npm run build
cd ..
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

### Streamlit demo

```powershell
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Mở `http://127.0.0.1:8501`.

Streamlit app có 3 tab: chatbot, xem dataset, và mô tả chương trình/agent workflow.

### FastAPI demo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn src.main:app --reload
```

Mở `http://127.0.0.1:8000`.

## Dữ liệu

Dataset mặc định nằm ở `data/restaurants.json`. Hiện loader hỗ trợ cả schema đầy đủ `Restaurant` và schema upload dạng Google Places:

```json
{
  "name": "Cafe ví dụ",
  "rating": "4.7",
  "reviews": "",
  "address": "Hoàn Kiếm, Hà Nội",
  "phone": "+84...",
  "hours": ""
}
```

Có thể dùng dataset riêng bằng biến môi trường:

```powershell
$env:RESTAURANT_DATA_PATH="D:\path\restaurants.json"
python -m uvicorn src.main:app --reload
```

Mỗi item nên có các trường: `id`, `name`, `address`, `district`, `distance_km`, `rating`, `price_min`, `price_max`, `cuisine_tags`, `status`, `review_count`, `image_url`, `source`, `last_updated`.
