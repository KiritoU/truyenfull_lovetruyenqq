# Sử dụng tool:

## Chạy file update:

> tmux a -t update

> python update.py

## Chạy file crawl all:

> tmux a -t all

> python all.py

## Trong session tmux:

**Khi muốn dừng tool**: ấn tổ hợp phím: Ctrl C

**Khi muốn chạy lại tool**: python update.py (hoặc python all.py)

**Khi muốn ẩn session đang chạy tool**: Bấm và giữ Ctrl sau đó ấn B, sau đó nhả 2 phím và ấn D (dùng để ẩn session tmux - vẫn chạy bình thường)

# Cài đặt cần lưu ý ở file settings.py (trong trường hợp cần sửa lại hoặc chạy tool ở vps khác):

- **user, password, host, port, database:** Kết nối tới database
- **TABLE_PREFIX:** Bắt đầu tên table trong database (Hiện tại là wp\_)

- **UPLOAD_FOLDER:** Folder gốc để lưu ảnh (folder uploads của theme)

- **THUMB_SAVE_PATH:** Folder lưu ảnh covers

- **TELEGRAM_BOT_TOKEN:** Token của bot telegram (tạo trong chat với BotFather). Điền vào giữa dấu ""
- **TELEGRAM_CHAT_ID:** Telegram ID của user hoặc group nhận thông báo khi domain truyenfull có thể die. Điền vào giữa dấu ""

- **WAIT_BETWEEN_LATEST:** Thời gian đợi giữa 2 lần cào page 1 truyenfull để update: 5 \* 60 là 5 phút
- **WAIT_BETWEEN_ALL:** Thời gian đợi giữa 2 lần cào từ page 2 tới page cuối của truyenfull để cào các truyện còn lại: 1 \* 20 là 20 giây

- **TRUYENFULL_HOMEPAGE:** Domain của truyenfull (Đổi trong trường hợp truyenfull đổi)

# Trong trường hợp restart VPS cần chạy các lệnh sau sau khi ssh vào VPS

> cd truyenfull_lovetruyenqq

> tmux new -s update

> source /venv/bin/activate

> Bấm và giữ Ctrl sau đó ấn B, sau đó nhả 2 phím và ấn D (dùng để ẩn session tmux - vẫn chạy bình thường)

> tmux new -s all

> source /venv/bin/activate

> Bấm và giữ Ctrl sau đó ấn B, sau đó nhả 2 phím và ấn D

Sau đó sử dụng theo hướng dẫn trên
