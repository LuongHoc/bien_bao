# Biển Báo AI – Hệ thống học và nhận dạng biển báo giao thông Việt Nam

> Đồ án xây dựng ứng dụng web hỗ trợ tra cứu, ôn luyện và nhận dạng biển báo giao thông Việt Nam bằng trí tuệ nhân tạo.

**Website:** [bienbao.luongvanhoc.io.vn](https://bienbao.luongvanhoc.io.vn/)  
**Mã nguồn:** [github.com/LuongHoc/bien_bao](https://github.com/LuongHoc/bien_bao)

<!-- ẢNH CẦN CHÈN: Ảnh chụp Landing Page toàn màn hình, có logo, tiêu đề và ảnh nền.
Lưu ảnh tại docs/images/landing-page.png, sau đó bỏ dấu chú thích ở dòng dưới. -->
<!-- ![Landing Page Biển Báo AI](docs/images/landing-page.png) -->

## 1. Giới thiệu

**Biển Báo AI** là ứng dụng web hỗ trợ người học nhận biết biển báo giao thông qua thư viện tra cứu, bài tập trắc nghiệm và chức năng nhận dạng bằng AI. Ứng dụng cũng hỗ trợ lưu tiến độ học tập, xem kết quả, gửi khảo sát và quản lý người dùng.

Thư viện cung cấp thông tin tra cứu **352 biển báo**. **Lưu ý:** số lượng biển báo có thể tra cứu không đồng nghĩa với số lớp mà mô hình AI nhận dạng được.

## 2. Chức năng chính

| Chức năng | Mô tả |
|---|---|
| Trang giới thiệu | Landing Page giới thiệu đề tài và các tính năng |
| Học biển báo | Tra cứu biển báo theo danh mục, tên hoặc mã |
| Nhận dạng AI | Nhận dạng biển báo từ ảnh; hỗ trợ luồng camera/video theo chức năng của ứng dụng |
| Bài tập | Làm trắc nghiệm, xem kết quả và lịch sử bài làm |
| Thống kê | Theo dõi điểm số, tiến độ và lịch sử học tập |
| Tài khoản | Đăng ký, đăng nhập bằng tài khoản hoặc Google; liên kết và xác minh email |
| Khôi phục mật khẩu | Xác minh mã gửi qua email trước khi đặt mật khẩu mới |
| Khảo sát | Ghi nhận đánh giá, góp ý của người học |
| Quản trị | Phân quyền Admin và quản lý hệ thống theo quyền được cấp |

### Giao diện ứng dụng

<!-- ẢNH CẦN CHÈN: Ảnh trang chủ bên trong ứng dụng, thể hiện slideshow và các nút chức năng. -->
<!-- ![Trang chủ ứng dụng](docs/images/trang-chu.png) -->

<!-- ẢNH CẦN CHÈN: Ảnh trang học biển báo, có danh sách và bộ lọc. -->
<!-- ![Thư viện biển báo](docs/images/thu-vien-bien-bao.png) -->

<!-- ẢNH CẦN CHÈN: Ảnh trang bài tập đang làm, thể hiện câu hỏi và bảng theo dõi câu trả lời. -->
<!-- ![Giao diện bài tập](docs/images/bai-tap.png) -->

<!-- ẢNH CẦN CHÈN: Ảnh kết quả nhận dạng từ một ảnh thử nghiệm thực tế; không dùng kết quả minh họa giả. -->
<!-- ![Kết quả nhận dạng AI](docs/images/nhan-dang-ai.png) -->

<!-- ẢNH CẦN CHÈN: Ảnh trang thống kê có dữ liệu thử nghiệm được phép công khai. -->
<!-- ![Thống kê học tập](docs/images/thong-ke.png) -->

<!-- ẢNH CẦN CHÈN: Ảnh giao diện đăng nhập/đăng ký, che mọi thông tin cá nhân. -->
<!-- ![Đăng nhập và đăng ký](docs/images/dang-nhap.png) -->

<!-- ẢNH CẦN CHÈN: Ảnh trang quản trị, che email, thông tin tài khoản và dữ liệu nhạy cảm. -->
<!-- ![Trang quản trị](docs/images/admin.png) -->

## 3. Công nghệ sử dụng

- **Backend:** Python, Flask.
- **Frontend:** HTML, CSS, JavaScript.
- **Cơ sở dữ liệu:** SQLite.
- **Nhận dạng biển báo:** YOLO11n kết hợp CNN trong quy trình nhận dạng của dự án.
- **Xác thực:** tài khoản/mật khẩu, Google OAuth, xác minh email.
- **Triển khai:** Ubuntu, Gunicorn, systemd và Cloudflare Tunnel; truy cập công khai qua HTTPS.

## 4. Cấu trúc mã nguồn

Repository có thể chứa cả tài liệu/nghiên cứu và ứng dụng. **Thư mục chạy ứng dụng chính** là `6_ung_dung/`.

```text
bien_bao/
├── 6_ung_dung/
│   ├── app.py                 # Điểm vào Flask
│   ├── auth.py                # Xác thực
│   ├── admin.py               # Chức năng quản trị
│   ├── admin_cli.py           # Công cụ quản trị dòng lệnh
│   ├── database.py            # Cơ sở dữ liệu
│   ├── learning.py            # Tiến độ học tập
│   ├── quiz.py                # Bài tập
│   ├── survey.py              # Khảo sát
│   ├── survey_db.py           # Lưu dữ liệu khảo sát
│   ├── email_sender.py        # Gửi email
│   ├── security.py            # Tiện ích bảo mật
│   ├── static/                # HTML, CSS, JS và ảnh giao diện
│   ├── instance/              # SQLite tại máy chạy (không commit)
│   └── requirements.txt       # Các thư viện Python (nếu có)
└── README.md
```

*Cấu trúc trên là bản rút gọn; một số thư mục dữ liệu, mô hình và cấu hình có thể nằm ở các vị trí khác trong dự án.*

## 5. Chạy ứng dụng trên máy cá nhân

Yêu cầu: Python tương thích với phiên bản dự án và các tệp mô hình/dữ liệu cần thiết.

```powershell
# Mở PowerShell tại thư mục gốc repository
cd 6_ung_dung

# Tạo môi trường ảo
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Cài thư viện (nếu có requirements.txt)
python -m pip install -r requirements.txt

# Khởi chạy
python app.py
```

Mở địa chỉ do Flask hiển thị trong terminal (thường là `http://127.0.0.1:5000`).

### Cấu hình môi trường

Ứng dụng sử dụng biến môi trường cho khóa phiên đăng nhập, Google OAuth và email. Tạo file `6_ung_dung/.env` theo cấu hình mà phiên bản mã nguồn yêu cầu. Ví dụ biến quan trọng:

```dotenv
FLASK_SECRET_KEY=<tao-khoa-ngau-nhien-du-manh>
GOOGLE_CLIENT_ID=<google-client-id-neu-dung>
GOOGLE_CLIENT_SECRET=<google-client-secret-neu-dung>
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<tai-khoan-gui-email>
SMTP_PASSWORD=<mat-khau-ung-dung>
```

> **Không commit `.env`, mật khẩu, token, cơ sở dữ liệu người dùng hoặc bản sao lưu lên GitHub.** Một số chức năng như Google OAuth và gửi OTP cần cấu hình hợp lệ mới hoạt động. Cần kiểm tra các biến bắt buộc trong mã nguồn trước khi khởi chạy.

## 6. Triển khai công khai

Phiên bản public được triển khai trên Ubuntu bằng Gunicorn và dịch vụ systemd, kết nối tên miền qua Cloudflare Tunnel.

```text
Người dùng → HTTPS / Cloudflare Tunnel → Gunicorn → Flask
                                               ├── SQLite
                                               └── Mô hình AI
```

<!-- ẢNH CẦN CHÈN: Sơ đồ kiến trúc triển khai đơn giản, đen trắng. -->
<!-- ![Sơ đồ triển khai](docs/images/kien-truc-trien-khai.png) -->

Không đưa file `.env` hoặc `instance/users.db` của máy chủ lên GitHub. Việc cập nhật code phải kiểm tra tính tương thích của cơ sở dữ liệu trước khi khởi động lại dịch vụ.

## 7. Lưu ý và giới hạn

- Kết quả AI phụ thuộc vào chất lượng ảnh, góc chụp, ánh sáng và các lớp biển báo mà mô hình đã được huấn luyện.
- Thư viện tra cứu có thể bao gồm nhiều biển báo hơn số lớp được hỗ trợ nhận dạng tự động.
- Không sử dụng kết quả nhận dạng như nguồn quyết định duy nhất khi tham gia giao thông.
- Không công khai thông tin người dùng hoặc ảnh chụp màn hình chứa email, token, khóa bí mật.

## 8. Tác giả và mục đích

Dự án được xây dựng phục vụ học tập, nghiên cứu và đồ án về nhận dạng biển báo giao thông Việt Nam.

---

**Gợi ý ảnh cần chuẩn bị:** `landing-page.png`, `trang-chu.png`, `thu-vien-bien-bao.png`, `bai-tap.png`, `nhan-dang-ai.png`, `thong-ke.png`, `dang-nhap.png`, `admin.png`, `kien-truc-trien-khai.png`. Đặt trong `docs/images/` ở **gốc repository**, sau đó bỏ `<!--` và `-->` ở dòng Markdown ảnh tương ứng để hiển thị trên GitHub.
