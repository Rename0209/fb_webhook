# Facebook Webhook API

Ứng dụng API xử lý webhook từ Facebook, lưu trữ dữ liệu vào MongoDB.

## Cấu trúc dự án

```
facebook_webhook/
├── main.py               # Điểm vào chính của ứng dụng
├── routes.py             # Định nghĩa các route API
├── database.py           # Kết nối và thao tác với MongoDB
├── facebook_api.py       # Các hàm gọi API Facebook
├── check_db.py           # Tiện ích kiểm tra dữ liệu trong DB
├── utils/                # Các module tiện ích
│   ├── __init__.py       # Biến thư mục thành package Python
│   ├── config.py         # Cấu hình ứng dụng
│   ├── error_handler.py  # Xử lý lỗi
│   └── webhook_parser.py # Phân tích dữ liệu webhook
└── README.md             # Tài liệu dự án
```

## Cài đặt

1. Cài đặt các gói phụ thuộc:

```bash
pip install -r requirements.txt
```

2. Cấu hình biến môi trường trong file `.env`:

```
VERIFY_TOKEN=your_verify_token_here
PAGE_ACCESS_TOKEN=your_page_access_token
PAGE_ID=your_page_id
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=facebook_webhook
MONGODB_COLLECTION_LOGS=webhook_logs
MONGODB_COLLECTION_PAGES=pages
PORT=8000
```

## Khởi chạy server

```bash
python main.py
```

Server sẽ chạy tại http://0.0.0.0:8000

## API Endpoints

- `GET /qawh` hoặc `GET /fqawh`: Xác thực webhook từ Facebook
- `POST /qawh` hoặc `POST /fqawh`: Nhận sự kiện webhook từ Facebook

## Xử lý sự kiện

Ứng dụng xử lý các loại sự kiện sau từ Facebook:

1. **Tin nhắn (Messages)**: Khi người dùng nhắn tin đến Page
2. **Bình luận (Comments)**: Khi người dùng bình luận vào bài đăng của Page
3. **Cảm xúc (Reactions)**: Khi người dùng thả cảm xúc (like, love, v.v.) vào bài đăng
4. **Lượt thích (Likes)**: Khi người dùng like bài đăng

## Cấu trúc dữ liệu

Dữ liệu được lưu trữ trong MongoDB với các trường:

- `time_id`: Thời gian nhận sự kiện
- `page_id`: ID của trang Facebook
- `event_type`: Loại sự kiện (message, comment, reaction, like)
- `data`: Dữ liệu chi tiết về sự kiện
- `type`: Loại log (`fb_event_in`, `fb_event_confirm`, `fb_event_force_confirm`)

## Kiểm tra dữ liệu

Chạy script `check_db.py` để xem dữ liệu mới nhất trong MongoDB:

```bash
python check_db.py 