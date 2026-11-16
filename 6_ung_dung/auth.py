# -*- coding: utf-8 -*-
"""
auth.py - Hệ thống xác thực đa phương thức cho Biển Báo AI.

Hỗ trợ:
1. Đăng ký & Đăng nhập bằng Email và Mật khẩu (scrypt băm an toàn).
2. Đăng nhập qua Google OAuth 2.0 / OpenID Connect.
3. Xác minh email qua token một lần (băm SHA-256).
4. Gửi lại email xác minh với rate limit an toàn.
5. Đăng xuất thống nhất có bảo vệ CSRF.
"""

import os
import re
import secrets
import time
from datetime import datetime, timezone

from flask import (
    abort,
    current_app,
    jsonify,
    redirect,
    render_template_string,
    request,
    send_from_directory,
    session,
    url_for,
)
from authlib.integrations.flask_client import OAuth

import database
import email_sender
from email_sender import (
    gui_email_xac_minh,
    gui_email_otp_xac_minh,
    gui_email_otp_xac_minh_chi_tiet,
    gui_email_dat_lai_mat_khau,
    gui_email_otp_dat_lai_mat_khau,
    gui_email_otp_dat_lai_mat_khau_chi_tiet,
    gui_email_thong_bao_doi_mat_khau,
)
from security import (
    bam_mat_khau,
    bam_otp,
    bam_token,
    da_het_han_utc,
    kiem_tra_chuan_mat_khau,
    kiem_tra_chuan_username,
    sinh_ma_otp,
    sinh_token_bi_mat,
    tinh_thoi_gian_het_han_utc,
    xac_thuc_otp_hash,
    xac_thuc_mat_khau,
)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Giới hạn tần suất trong bộ nhớ (In-Memory Rate Limiter)
_LOGIN_FAILURES = {}      # key -> [timestamps]
_REGISTER_RATE = {}       # ip -> [timestamps]
_RESEND_RATE = {}         # email -> timestamp
_FORGOT_RATE = {}         # ip:email -> [timestamps]
_RESEND_OTP_RATE = {}     # ip:email -> [timestamps]
_OTP_COOLDOWN = {}        # email -> timestamp


def _kiem_tra_rate_limit(store, key, max_requests, window_seconds):
    """Kiểm tra xem key có bị vượt quá max_requests trong window_seconds hay không.
    Trả về: True nếu hợp lệ, False nếu bị chặn do quá tần suất.
    """
    now = time.monotonic()
    records = [t for t in store.get(key, []) if now - t < window_seconds]
    if len(records) >= max_requests:
        store[key] = records
        return False
    records.append(now)
    store[key] = records
    return True


def che_email(email: str) -> str:
    """Che bớt ký tự email để hiển thị an toàn trên giao diện (ví dụ ng***@gmail.com)."""
    if not email or "@" not in email:
        return email or ""
    parts = email.split("@", 1)
    name_part = parts[0]
    domain_part = parts[1]
    if len(name_part) <= 2:
        masked_name = name_part[:1] + "***"
    else:
        masked_name = name_part[:2] + "***"
    return f"{masked_name}@{domain_part}"


def cau_hinh_dang_nhap(app):
    """Đăng ký các route xác thực cho Flask (Google + Email/Password)."""

    # 1. Khởi tạo cơ sở dữ liệu SQLite
    database.khoi_tao_db()

    # 2. Khởi tạo OAuth cho Google
    oauth = OAuth(app)
    google_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    if google_client_id and google_client_secret:
        google = oauth.register(
            name="google",
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    else:
        google = None

    # =========================================================================
    # GIAO DIỆN XÁC THỰC (HTML VIEWS)
    # =========================================================================

    @app.route("/login", methods=["GET"])
    def trang_dang_nhap():
        user_id = session.get("user_id")
        if user_id and database.lay_nguoi_dung(user_id):
            next_url = request.args.get("next") or "/app"
            return redirect(next_url)
        return send_from_directory(app.static_folder, "auth.html")

    @app.route("/register", methods=["GET"])
    def trang_dang_ky():
        user_id = session.get("user_id")
        if user_id and database.lay_nguoi_dung(user_id):
            return redirect("/app")
        return send_from_directory(app.static_folder, "auth.html")

    @app.route("/forgot-password", methods=["GET"])
    def trang_quen_mat_khau():
        user_id = session.get("user_id")
        if user_id and database.lay_nguoi_dung(user_id):
            return redirect("/app")
        return send_from_directory(app.static_folder, "auth.html")

    @app.route("/reset-password", methods=["GET"])
    def trang_dat_lai_mat_khau():
        return send_from_directory(app.static_folder, "auth.html")

    # =========================================================================
    # GOOGLE OAUTH
    # =========================================================================

    @app.route("/auth/google")
    def google_login():
        if not google:
            return jsonify({"loi": "Chưa cấu hình GOOGLE_CLIENT_ID hoặc GOOGLE_CLIENT_SECRET."}), 500

        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            session["auth_next"] = next_url

        callback = url_for("google_callback", _external=True)
        return google.authorize_redirect(callback)

    @app.route("/auth/callback")
    def google_callback():
        if not google:
            abort(500)

        token = google.authorize_access_token()
        thong_tin = token.get("userinfo")
        if not thong_tin or not thong_tin.get("sub"):
            abort(401)
        if not thong_tin.get("email_verified", False):
            abort(403)

        user_id = database.luu_nguoi_dung(thong_tin)
        next_url = session.get("auth_next")

        session.clear()
        session["user_id"] = user_id
        session["csrf_token"] = secrets.token_urlsafe(32)
        session.permanent = True

        return redirect(next_url or "/app")

    @app.route("/auth/link-google")
    def google_link():
        """Bắt đầu luồng liên kết tài khoản Google cho người dùng đã đăng nhập."""
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login?next=/app%23/nguoi-hoc")
        if not google:
            return jsonify({"loi": "Chưa cấu hình Google OAuth."}), 500

        session["linking_user_id"] = user_id
        callback = url_for("google_link_callback", _external=True)
        return google.authorize_redirect(callback)

    @app.route("/auth/link-google/callback")
    def google_link_callback():
        """Nhận phản hồi từ Google để liên kết danh tính Google với tài khoản hiện tại."""
        if not google:
            abort(500)

        linking_user_id = session.pop("linking_user_id", None)
        current_user_id = session.get("user_id")

        if not linking_user_id or linking_user_id != current_user_id:
            return redirect("/app#/nguoi-hoc?error=link_invalid_session")

        try:
            token = google.authorize_access_token()
            thong_tin = token.get("userinfo")
            if not thong_tin or not thong_tin.get("sub"):
                return redirect("/app#/nguoi-hoc?error=link_failed")

            sub = str(thong_tin.get("sub"))
            email = thong_tin.get("email")
            picture = thong_tin.get("picture")

            database.lien_ket_tai_khoan_google(linking_user_id, sub, email, picture)
            return redirect("/app#/nguoi-hoc?linked=google_success")
        except database.TaiKhoanGoogleDaLienKet:
            return redirect("/app#/nguoi-hoc?error=google_already_linked")
        except Exception as e:
            current_app.logger.error(f"Lỗi khi liên kết Google: {e}")
            return redirect("/app#/nguoi-hoc?error=link_failed")

    # =========================================================================
    # EMAIL / PASSWORD AUTHENTICATION APIS
    # =========================================================================

    @app.route("/api/auth/register", methods=["POST"])
    def api_dang_ky():
        """Đăng ký tài khoản mới bằng Tên tài khoản, Mật khẩu và Email tùy chọn."""
        ip = request.remote_addr or "127.0.0.1"
        if not _kiem_tra_rate_limit(_REGISTER_RATE, ip, max_requests=10, window_seconds=900):
            return jsonify({
                "thanh_cong": False,
                "code": "rate_limited",
                "thong_bao": "Quá nhiều yêu cầu đăng ký từ địa chỉ của bạn. Vui lòng thử lại sau 15 phút."
            }), 429

        data = request.get_json(silent=True) or {}
        ten = str(data.get("ten") or "").strip()
        username = str(data.get("username") or data.get("ten_tai_khoan") or "").strip()
        raw_email = data.get("email")
        if raw_email is None:
            email = None
        elif isinstance(raw_email, str):
            email = raw_email.strip().lower() or None
        else:
            email = str(raw_email).strip().lower() or None
        mat_khau = str(data.get("mat_khau") or "")
        xac_nhan = str(data.get("xac_nhan_mat_khau") or "")

        # 1. Validation họ tên
        if len(ten) < 2 or len(ten) > 50:
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_name",
                "thong_bao": "Họ và tên phải có độ dài từ 2 đến 50 ký tự."
            }), 400

        # 2. Validation tên tài khoản (username)
        if username:
            u_hop_le, u_loi = kiem_tra_chuan_username(username)
            if not u_hop_le:
                return jsonify({
                    "thanh_cong": False,
                    "code": "invalid_username",
                    "thong_bao": u_loi
                }), 400
        else:
            # Nếu không truyền username
            if not email:
                return jsonify({
                    "thanh_cong": False,
                    "code": "missing_username",
                    "thong_bao": "Vui lòng nhập tên tài khoản."
                }), 400
            # Tương thích ngược: tự sinh username từ email prefix
            prefix = email.split("@")[0]
            clean = re.sub(r"[^a-zA-Z0-9_.]", "", prefix)
            if len(clean) < 3:
                clean = f"user_{secrets.token_hex(3)}"
            candidate = clean[:25]
            if database.kiem_tra_username_ton_tai(candidate):
                candidate = f"{candidate[:20]}_{secrets.token_hex(3)}"
            username = candidate

        # 3. Validation email (chỉ kiểm tra khi người dùng thực sự nhập email)
        if email is not None:
            if len(email) > 120 or not EMAIL_REGEX.match(email):
                return jsonify({
                    "thanh_cong": False,
                    "code": "invalid_email",
                    "thong_bao": "Địa chỉ email không đúng định dạng."
                }), 400

        # 4. Validation mật khẩu
        mk_hop_le, mk_loi = kiem_tra_chuan_mat_khau(mat_khau)
        if not mk_hop_le:
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_password",
                "thong_bao": mk_loi
            }), 400

        if mat_khau != xac_nhan:
            return jsonify({
                "thanh_cong": False,
                "code": "password_mismatch",
                "thong_bao": "Mật khẩu xác nhận không khớp."
            }), 400

        # 5. Băm mật khẩu và lưu database
        mat_khau_hash = bam_mat_khau(mat_khau)
        try:
            user_id = database.dang_ky_tai_khoan(ten, username, mat_khau_hash, email=email)
        except database.UsernameDaTonTai as e:
            return jsonify({
                "thanh_cong": False,
                "code": "username_already_exists",
                "thong_bao": str(e)
            }), 409
        except database.EmailDaDangKyGoogle as e:
            return jsonify({
                "thanh_cong": False,
                "code": "email_registered_with_google",
                "thong_bao": str(e)
            }), 409
        except database.EmailChuaXacMinh as e:
            return jsonify({
                "thanh_cong": False,
                "code": "email_already_exists",
                "chua_xac_minh": True,
                "email": email,
                "email_da_che": che_email(email),
                "thong_bao": str(e)
            }), 409
        except database.EmailDaTonTai as e:
            return jsonify({
                "thanh_cong": False,
                "code": "email_already_exists",
                "thong_bao": str(e)
            }), 409

        # 6. Nếu đăng ký KHÔNG kèm email -> Hoàn tất ngay, không cần OTP
        if not email:
            return jsonify({
                "thanh_cong": True,
                "username": username,
                "can_xac_minh": False,
                "thong_bao": "Đăng ký thành công! Bạn có thể đăng nhập ngay bằng tên tài khoản và mật khẩu vừa tạo."
            }), 201

        # 7. Nếu đăng ký CÓ kèm email -> Sinh mã OTP 6 số và gửi qua email
        otp_tho = sinh_ma_otp(6)
        otp_hash = bam_otp(otp_tho, email)
        exp_otp_utc = tinh_thoi_gian_het_han_utc(5)
        database.luu_yeu_cau_otp_xac_minh_email(user_id, email, otp_hash, exp_otp_utc, ip)

        token_tho = sinh_token_bi_mat(32)
        token_hash = bam_token(token_tho)
        exp_utc = tinh_thoi_gian_het_han_utc(24 * 60)
        database.luu_token_xac_minh_email(user_id, email, token_hash, exp_utc)

        base_url = request.host_url.rstrip("/")
        verify_link = f"{base_url}/auth/verify-email?token={token_tho}"
        gui_ok, gui_msg = email_sender.gui_email_otp_xac_minh_chi_tiet(
            email, ten, otp_tho, verify_link=verify_link
        )
        if not gui_ok and not current_app.config.get("TESTING"):
            da_cau_hinh, ly_do = email_sender.kiem_tra_cau_hinh_smtp()
            if not da_cau_hinh:
                return jsonify({
                    "thanh_cong": False,
                    "code": "smtp_not_configured",
                    "thong_bao": "Dịch vụ gửi email chưa được cấu hình trên máy chủ. Vui lòng thiết lập SMTP_USERNAME và SMTP_PASSWORD trong tệp .env."
                }), 503
            return jsonify({
                "thanh_cong": False,
                "code": "email_send_failed",
                "thong_bao": "Không thể gửi email xác nhận. Vui lòng kiểm tra lại địa chỉ email hoặc thử lại sau."
            }), 500

        _RESEND_RATE[email] = time.monotonic()

        return jsonify({
            "thanh_cong": True,
            "username": username,
            "email": email,
            "email_da_che": che_email(email),
            "can_xac_minh": True,
            "co_the_gui_lai_sau": 60,
            "thong_bao": "Đăng ký thành công! Vui lòng nhập mã OTP gồm 6 chữ số đã gửi về hộp thư để kích hoạt email của bạn."
        }), 201

    @app.route("/api/auth/login", methods=["POST"])
    def api_dang_nhap():
        """Đăng nhập bằng Tên tài khoản (hoặc Email) và Mật khẩu."""
        ip = request.remote_addr or "127.0.0.1"
        data = request.get_json(silent=True) or {}
        tai_khoan = str(data.get("tai_khoan") or data.get("username") or data.get("email") or "").strip()
        mat_khau = str(data.get("mat_khau") or "")
        ghi_nho = bool(data.get("ghi_nho", False))

        rate_key = f"{ip}:{tai_khoan.lower()}"
        if not _kiem_tra_rate_limit(_LOGIN_FAILURES, rate_key, max_requests=5, window_seconds=900):
            return jsonify({
                "thanh_cong": False,
                "code": "too_many_attempts",
                "thong_bao": "Đã thử đăng nhập sai quá nhiều lần. Vui lòng thử lại sau 15 phút."
            }), 429

        if not tai_khoan or not mat_khau:
            return jsonify({
                "thanh_cong": False,
                "code": "missing_credentials",
                "thong_bao": "Vui lòng nhập đầy đủ tên tài khoản và mật khẩu."
            }), 400

        user = database.tim_nguoi_dung_theo_dinh_danh(tai_khoan)
        if not user:
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_credentials",
                "thong_bao": "Tên tài khoản hoặc mật khẩu không chính xác."
            }), 401

        mat_khau_hash = database.lay_mat_khau_hash(user["id"])
        if not mat_khau_hash:
            # Tài khoản đăng ký qua Google, chưa tạo mật khẩu
            providers = database.lay_cac_phuong_thuc_dang_nhap(user["id"])
            if "google" in providers:
                return jsonify({
                    "thanh_cong": False,
                    "code": "use_google_login",
                    "thong_bao": "Tài khoản này được đăng ký bằng Google. Vui lòng chọn 'Tiếp tục với Google'."
                }), 401
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_credentials",
                "thong_bao": "Tên tài khoản hoặc mật khẩu không chính xác."
            }), 401

        if not xac_thuc_mat_khau(mat_khau_hash, mat_khau):
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_credentials",
                "thong_bao": "Tên tài khoản hoặc mật khẩu không chính xác."
            }), 401

        if user["status"] != "active":
            return jsonify({
                "thanh_cong": False,
                "code": "account_suspended",
                "thong_bao": "Tài khoản đang bị tạm khóa hoặc vô hiệu hóa. Vui lòng liên hệ quản trị viên."
            }), 403

        # Chỉ chặn và yêu cầu OTP nếu tài khoản CÓ email nhưng CHƯA xác minh
        if user.get("email") and not user.get("email_verified"):
            otp_tho = sinh_ma_otp(6)
            otp_hash = bam_otp(otp_tho, user["email"])
            exp_otp_utc = tinh_thoi_gian_het_han_utc(5)
            database.luu_yeu_cau_otp_xac_minh_email(user["id"], user["email"], otp_hash, exp_otp_utc, ip)

            email_sender.gui_email_otp_xac_minh(user["email"], user.get("ten", "Người học"), otp_tho)

            return jsonify({
                "thanh_cong": False,
                "chua_xac_minh": True,
                "chuyen_otp": True,
                "code": "email_not_verified",
                "email": user["email"],
                "email_da_che": che_email(user["email"]),
                "co_the_gui_lai_sau": 60,
                "thong_bao": "Tài khoản chưa được xác minh email. Mã OTP xác minh mới gồm 6 chữ số đã được gửi đến hộp thư của bạn."
            }), 403

        # Đăng nhập thành công -> Xóa bộ đếm sai
        _LOGIN_FAILURES.pop(rate_key, None)
        database.cap_nhat_dang_nhap_thanh_cong(user["id"])

        # Session regeneration
        session.clear()
        session["user_id"] = user["id"]
        session["csrf_token"] = secrets.token_urlsafe(32)
        session.permanent = ghi_nho

        return jsonify({
            "thanh_cong": True,
            "thong_bao": "Đăng nhập thành công!",
            "user": database.lay_nguoi_dung(user["id"]),
            "csrf_token": session["csrf_token"]
        }), 200

    @app.route("/auth/verify-email", methods=["GET"])
    @app.route("/api/auth/verify-email", methods=["GET"])
    def xac_minh_email():
        """Xác minh email qua token link."""
        token_tho = request.args.get("token", "").strip()
        is_json_request = (
            request.path.startswith("/api/")
            or "application/json" in request.headers.get("Accept", "")
            or request.args.get("format") == "json"
        )

        if not token_tho:
            if is_json_request:
                return jsonify({"thanh_cong": False, "code": "missing_token", "thong_bao": "Thiếu mã xác minh."}), 400
            return redirect("/login?error=invalid_token")

        token_hash = bam_token(token_tho)
        record = database.tim_token_xac_minh(token_hash)

        if not record or record.get("used_at") or da_het_han_utc(record.get("expires_at", "")):
            if is_json_request:
                return jsonify({
                    "thanh_cong": False,
                    "code": "invalid_or_expired_token",
                    "thong_bao": "Liên kết xác minh không hợp lệ hoặc đã hết hạn."
                }), 400
            return redirect("/login?error=invalid_token")

        # Đánh dấu đã dùng và cập nhật trạng thái người dùng
        database.danh_dau_token_da_dung("email_verification_tokens", token_hash)
        database.xac_minh_email_nguoi_dung(record["user_id"])

        user = database.lay_nguoi_dung(record["user_id"])
        email = user["email"] if user else ""

        if is_json_request:
            return jsonify({
                "thanh_cong": True,
                "thong_bao": "Xác minh email thành công! Bạn có thể đăng nhập ngay.",
                "email": email
            }), 200

        return redirect(f"/login?verified=1&email={email}")

    @app.route("/api/auth/resend-verification", methods=["POST"])
    def api_gui_lai_xac_minh():
        """Gửi lại email xác minh tài khoản kèm mã OTP 6 chữ số."""
        ip = request.remote_addr or "127.0.0.1"
        data = request.get_json(silent=True) or {}
        email = str(data.get("email") or "").strip().lower()

        if not email or not EMAIL_REGEX.match(email):
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_email",
                "thong_bao": "Địa chỉ email không hợp lệ."
            }), 400

        # Kiểm tra cấu hình SMTP trước (không báo gửi thành công khi chưa cấu hình)
        da_cau_hinh, ly_do = email_sender.kiem_tra_cau_hinh_smtp()
        if not da_cau_hinh and not current_app.config.get("TESTING"):
            return jsonify({
                "thanh_cong": False,
                "code": "smtp_not_configured",
                "thong_bao": "Dịch vụ gửi email chưa được cấu hình trên máy chủ. Vui lòng thiết lập SMTP_USERNAME và SMTP_PASSWORD trong tệp .env."
            }), 503

        now = time.monotonic()
        last_sent = _RESEND_RATE.get(email, 0)
        if now - last_sent < 60:
            remaining = int(60 - (now - last_sent))
            return jsonify({
                "thanh_cong": False,
                "code": "rate_limited",
                "co_the_gui_lai_sau": remaining,
                "thong_bao": f"Vui lòng đợi {remaining} giây trước khi yêu cầu gửi lại."
            }), 429

        _RESEND_RATE[email] = now

        user = database.tim_nguoi_dung_theo_email_hoac_id(email)
        if user and not user.get("email_verified") and user.get("status") == "active":
            otp_tho = sinh_ma_otp(6)
            otp_hash = bam_otp(otp_tho, email)
            exp_otp_utc = tinh_thoi_gian_het_han_utc(5)
            database.luu_yeu_cau_otp_xac_minh_email(user["id"], email, otp_hash, exp_otp_utc, ip)

            token_tho = sinh_token_bi_mat(32)
            token_hash = bam_token(token_tho)
            exp_utc = tinh_thoi_gian_het_han_utc(24 * 60)
            database.luu_token_xac_minh_email(user["id"], email, token_hash, exp_utc)

            base_url = request.host_url.rstrip("/")
            verify_link = f"{base_url}/auth/verify-email?token={token_tho}"
            email_sender.gui_email_otp_xac_minh(email, user.get("ten", "Người học"), otp_tho, verify_link=verify_link)

        return jsonify({
            "thanh_cong": True,
            "email": email,
            "email_da_che": che_email(email),
            "co_the_gui_lai_sau": 60,
            "thong_bao": "Nếu email tồn tại trong hệ thống và chưa xác minh, mã OTP xác nhận mới đã được gửi vào hộp thư của bạn."
        }), 200

    @app.route("/api/auth/verify-registration-otp", methods=["POST"])
    def api_xac_thuc_otp_xac_minh_email():
        """Bước 2: Người dùng nhập mã OTP 6 chữ số để kích hoạt tài khoản đăng ký mới."""
        data = request.get_json(silent=True) or {}
        email = str(data.get("email") or "").strip().lower()
        otp = str(data.get("otp") or "").strip()

        if not email or not EMAIL_REGEX.match(email):
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_email",
                "thong_bao": "Địa chỉ email không đúng định dạng."
            }), 400

        if not otp or len(otp) != 6 or not otp.isdigit():
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_otp_format",
                "thong_bao": "Mã xác nhận phải gồm đúng 6 chữ số."
            }), 400

        record = database.tim_yeu_cau_otp_xac_minh_moi_nhat(email)
        if not record or record.get("used_at"):
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_or_expired_otp",
                "thong_bao": "Yêu cầu xác nhận không tồn tại hoặc đã được sử dụng. Vui lòng gửi lại mã mới."
            }), 400

        if record.get("attempts_left", 0) <= 0:
            return jsonify({
                "thanh_cong": False,
                "code": "max_attempts_exceeded",
                "thong_bao": "Bạn đã nhập sai mã quá 5 lần. Mã xác nhận đã bị vô hiệu hóa, vui lòng yêu cầu mã mới."
            }), 400

        if da_het_han_utc(record.get("expires_at", "")):
            return jsonify({
                "thanh_cong": False,
                "code": "otp_expired",
                "thong_bao": "Mã xác nhận đã hết hạn (hiệu lực 5 phút). Vui lòng yêu cầu mã mới."
            }), 400

        # Kiểm tra mã OTP bằng HMAC-SHA256 (timing safe)
        hop_le = xac_thuc_otp_hash(otp, email, record["otp_hash"])
        if not hop_le:
            con_lai = database.ghi_nhan_otp_xac_minh_sai(record["id"])
            if con_lai <= 0:
                return jsonify({
                    "thanh_cong": False,
                    "code": "max_attempts_exceeded",
                    "thong_bao": "Bạn đã nhập sai quá 5 lần. Mã xác nhận đã bị vô hiệu hóa, vui lòng yêu cầu mã mới."
                }), 400
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_otp",
                "thong_bao": f"Mã xác nhận không chính xác. Bạn còn {con_lai} lần thử.",
                "attempts_left": con_lai
            }), 400

        # OTP đúng -> Kích hoạt tài khoản ngay lập tức
        database.xac_nhan_otp_xac_minh_thanh_cong(record["id"], record["user_id"])

        return jsonify({
            "thanh_cong": True,
            "code": "account_verified",
            "thong_bao": "Kích hoạt tài khoản thành công! Bạn có thể đăng nhập ngay bây giờ."
        }), 200

    # =========================================================================
    # THÔNG TIN TÀI KHOẢN VÀ ĐĂNG XUẤT
    # =========================================================================

    @app.route("/api/me")
    def thong_tin_tai_khoan():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"da_dang_nhap": False})

        user = database.lay_nguoi_dung(user_id)
        if user is None or user.get("status") != "active":
            session.clear()
            return jsonify({"da_dang_nhap": False})

        providers = database.lay_cac_phuong_thuc_dang_nhap(user_id)

        return jsonify({
            "da_dang_nhap": True,
            "user": user,
            "providers": providers,
            "csrf_token": session.get("csrf_token")
        })

    @app.route("/auth/logout", methods=["POST"])
    def dang_xuat():
        if not session.get("user_id"):
            abort(401)

        csrf = request.headers.get("X-CSRF-Token")
        expected = session.get("csrf_token", "")
        if not csrf or not secrets.compare_digest(csrf, expected):
            abort(403)

        session.clear()
        return jsonify({
            "thanh_cong": True,
            "thong_bao": "Đã đăng xuất thành công."
        })

    # =========================================================================
    # QUÊN MẬT KHẨU, ĐẶT LẠI MẬT KHẨU VÀ QUẢN LÝ BẢO MẬT TÀI KHOẢN (BƯỚC 18.3)
    # =========================================================================

    @app.route("/api/auth/forgot-password", methods=["POST"])
    def api_quen_mat_khau():
        """Bước 1: Yêu cầu gửi mã xác nhận OTP qua email để khôi phục mật khẩu. Chống enumeration."""
        ip = request.remote_addr or "127.0.0.1"
        data = request.get_json(silent=True) or {}
        dinh_danh = str(data.get("dinh_danh") or data.get("email") or data.get("username") or "").strip()

        if "email" in data and not EMAIL_REGEX.match(dinh_danh):
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_email",
                "thong_bao": "Địa chỉ email không đúng định dạng."
            }), 400

        if not dinh_danh:
            return jsonify({
                "thanh_cong": False,
                "code": "missing_identifier",
                "thong_bao": "Vui lòng nhập tên tài khoản hoặc địa chỉ email."
            }), 400

        # Kiểm tra cấu hình SMTP trước (không báo thành công giả lập khi chưa cấu hình trên máy chủ)
        da_cau_hinh, ly_do = email_sender.kiem_tra_cau_hinh_smtp()
        if not da_cau_hinh and not current_app.config.get("TESTING"):
            return jsonify({
                "thanh_cong": False,
                "code": "smtp_not_configured",
                "thong_bao": "Dịch vụ gửi email chưa được cấu hình trên máy chủ. Vui lòng thiết lập SMTP_USERNAME và SMTP_PASSWORD trong tệp .env."
            }), 503

        rate_key = f"{ip}:{dinh_danh.lower()}"
        if not _kiem_tra_rate_limit(_FORGOT_RATE, rate_key, max_requests=3, window_seconds=900):
            return jsonify({
                "thanh_cong": False,
                "code": "rate_limited",
                "thong_bao": "Quá nhiều yêu cầu khôi phục mật khẩu cho tài khoản này. Vui lòng thử lại sau 15 phút."
            }), 429

        user = database.tim_nguoi_dung_theo_dinh_danh(dinh_danh)

        if user:
            # Kiểm tra tài khoản có email để nhận mã khôi phục hay không
            if not user.get("email"):
                return jsonify({
                    "thanh_cong": False,
                    "code": "no_recovery_email",
                    "thong_bao": "Tài khoản này chưa liên kết email xác minh nên không thể khôi phục mật khẩu tự động qua email. Vui lòng liên hệ quản trị viên để được hỗ trợ."
                }), 400

            target_email = user["email"].strip().lower()
            has_pw = database.lay_mat_khau_hash(user["id"]) is not None

            if user.get("status") == "active" and has_pw:
                # 1. Sinh mã OTP 6 chữ số CSPRNG và băm bằng HMAC-SHA256 (khóa server + email context)
                otp_tho = sinh_ma_otp(6)
                otp_hash = bam_otp(otp_tho, target_email)
                exp_otp_utc = tinh_thoi_gian_het_han_utc(5)  # 5 phút hiệu lực
                database.luu_yeu_cau_otp_reset(user["id"], target_email, otp_hash, exp_otp_utc, ip)

                # 2. Token dự phòng link phục vụ tương thích ngược
                token_tho = sinh_token_bi_mat(32)
                token_hash = bam_token(token_tho)
                exp_token_utc = tinh_thoi_gian_het_han_utc(30)
                database.luu_token_dat_lai_mat_khau(user["id"], token_hash, exp_token_utc)
                base_url = request.host_url.rstrip("/")
                reset_link = f"{base_url}/reset-password?token={token_tho}"

                # 3. Gửi email chứa OTP 6 số
                gui_ok, gui_msg = email_sender.gui_email_otp_dat_lai_mat_khau_chi_tiet(
                    target_email, user.get("ten", "Người học"), otp_tho, reset_link=reset_link
                )
                if not gui_ok and not current_app.config.get("TESTING"):
                    return jsonify({
                        "thanh_cong": False,
                        "code": "smtp_send_failed",
                        "thong_bao": f"Gửi email xác nhận thất bại: {gui_msg}. Vui lòng kiểm tra lại cấu hình SMTP hoặc thử lại sau ít phút."
                    }), 500
                _OTP_COOLDOWN[target_email] = time.time()

            return jsonify({
                "thanh_cong": True,
                "co_email": True,
                "email": target_email,
                "email_da_che": che_email(target_email),
                "thong_bao": "Nếu email này được đăng ký và hỗ trợ khôi phục mật khẩu, chúng tôi đã gửi mã xác nhận.",
                "co_the_gui_lai_sau": 60
            }), 200

        # Nếu không tìm thấy tài khoản
        if "@" in dinh_danh or "email" in data:
            return jsonify({
                "thanh_cong": True,
                "thong_bao": "Nếu email này được đăng ký và hỗ trợ khôi phục mật khẩu, chúng tôi đã gửi mã xác nhận.",
                "co_the_gui_lai_sau": 60
            }), 200

        return jsonify({
            "thanh_cong": False,
            "code": "account_not_found",
            "thong_bao": "Không tìm thấy tài khoản với tên đăng nhập này."
        }), 404

    @app.route("/api/auth/verify-reset-otp", methods=["POST"])
    def api_xac_thuc_otp_dat_lai_mat_khau():
        """Bước 2: Xác thực mã OTP 6 chữ số gửi qua email."""
        ip = request.remote_addr or "127.0.0.1"
        data = request.get_json(silent=True) or {}
        email = str(data.get("email") or "").strip().lower()
        otp = str(data.get("otp") or "").strip()

        if not email or not EMAIL_REGEX.match(email):
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_email",
                "thong_bao": "Địa chỉ email không đúng định dạng."
            }), 400

        if not otp or len(otp) != 6 or not otp.isdigit():
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_otp_format",
                "thong_bao": "Mã xác nhận phải gồm đúng 6 chữ số."
            }), 400

        rate_key = f"verify:{ip}:{email}"
        if not _kiem_tra_rate_limit(_FORGOT_RATE, rate_key, max_requests=10, window_seconds=600):
            return jsonify({
                "thanh_cong": False,
                "code": "rate_limited",
                "thong_bao": "Quá nhiều lần thử xác thực. Vui lòng thử lại sau ít phút."
            }), 429

        record = database.tim_yeu_cau_otp_moi_nhat(email)
        if not record:
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_otp",
                "thong_bao": "Mã xác nhận không hợp lệ hoặc đã hết hạn."
            }), 400

        if record.get("used_at"):
            return jsonify({
                "thanh_cong": False,
                "code": "otp_already_used",
                "thong_bao": "Mã xác nhận này đã được sử dụng."
            }), 400

        if record.get("attempts_left", 0) <= 0:
            return jsonify({
                "thanh_cong": False,
                "code": "max_attempts_exceeded",
                "thong_bao": "Mã xác nhận đã bị vô hiệu hóa do nhập sai quá 5 lần. Vui lòng yêu cầu mã mới."
            }), 400

        if da_het_han_utc(record.get("expires_at", "")):
            return jsonify({
                "thanh_cong": False,
                "code": "otp_expired",
                "thong_bao": "Mã xác nhận đã hết hạn (hiệu lực 5 phút). Vui lòng yêu cầu mã mới."
            }), 400

        # Kiểm tra mã OTP bằng HMAC-SHA256 (timing safe)
        hop_le = xac_thuc_otp_hash(otp, email, record["otp_hash"])
        if not hop_le:
            con_lai = database.ghi_nhan_otp_sai(record["id"])
            if con_lai <= 0:
                return jsonify({
                    "thanh_cong": False,
                    "code": "max_attempts_exceeded",
                    "thong_bao": "Bạn đã nhập sai quá 5 lần. Mã xác nhận đã bị vô hiệu hóa, vui lòng yêu cầu mã mới."
                }), 400
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_otp",
                "thong_bao": f"Mã xác nhận không chính xác. Bạn còn {con_lai} lần thử.",
                "attempts_left": con_lai
            }), 400

        # OTP đúng -> Cấp reset_grant ngẫu nhiên (32 bytes urlsafe) có hiệu lực 15 phút
        reset_grant = sinh_token_bi_mat(32)
        grant_hash = bam_token(reset_grant)
        grant_exp_utc = tinh_thoi_gian_het_han_utc(15)
        database.xac_nhan_otp_thanh_cong(record["id"], grant_hash, grant_exp_utc)

        return jsonify({
            "thanh_cong": True,
            "thong_bao": "Xác thực mã OTP thành công.",
            "reset_grant": reset_grant
        }), 200

    @app.route("/api/auth/resend-reset-otp", methods=["POST"])
    def api_gui_lai_otp_dat_lai_mat_khau():
        """Gửi lại mã OTP qua email (áp dụng cooldown 60 giây và rate limiting)."""
        ip = request.remote_addr or "127.0.0.1"
        data = request.get_json(silent=True) or {}
        email = str(data.get("email") or "").strip().lower()

        if not email or not EMAIL_REGEX.match(email):
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_email",
                "thong_bao": "Địa chỉ email không đúng định dạng."
            }), 400

        # Kiểm tra cấu hình SMTP trước (không báo gửi thành công khi chưa cấu hình)
        da_cau_hinh, ly_do = email_sender.kiem_tra_cau_hinh_smtp()
        if not da_cau_hinh and not current_app.config.get("TESTING"):
            return jsonify({
                "thanh_cong": False,
                "code": "smtp_not_configured",
                "thong_bao": "Dịch vụ gửi email chưa được cấu hình trên máy chủ. Vui lòng thiết lập SMTP_USERNAME và SMTP_PASSWORD trong tệp .env."
            }), 503

        # Kiểm tra cooldown 60 giây
        last_sent = _OTP_COOLDOWN.get(email, 0)
        now = time.time()
        if now - last_sent < 60:
            remaining = int(60 - (now - last_sent))
            return jsonify({
                "thanh_cong": False,
                "code": "cooldown_active",
                "thong_bao": f"Vui lòng chờ {remaining} giây trước khi yêu cầu gửi lại mã.",
                "remaining_seconds": remaining
            }), 429

        rate_key = f"{ip}:{email}"
        if not _kiem_tra_rate_limit(_RESEND_OTP_RATE, rate_key, max_requests=5, window_seconds=900):
            return jsonify({
                "thanh_cong": False,
                "code": "rate_limited",
                "thong_bao": "Bạn đã yêu cầu gửi lại mã quá nhiều lần. Vui lòng thử lại sau 15 phút."
            }), 429

        user = database.tim_nguoi_dung_theo_email_hoac_id(email)
        has_pw = False
        if user:
            has_pw = database.lay_mat_khau_hash(user["id"]) is not None

        if user and user.get("status") == "active" and has_pw:
            otp_tho = sinh_ma_otp(6)
            otp_hash = bam_otp(otp_tho, email)
            exp_otp_utc = tinh_thoi_gian_het_han_utc(5)
            # Lưu mới, tự động vô hiệu hóa mã cũ chưa xác minh
            database.luu_yeu_cau_otp_reset(user["id"], email, otp_hash, exp_otp_utc, ip)

            token_tho = sinh_token_bi_mat(32)
            token_hash = bam_token(token_tho)
            exp_token_utc = tinh_thoi_gian_het_han_utc(30)
            database.luu_token_dat_lai_mat_khau(user["id"], token_hash, exp_token_utc)

            base_url = request.host_url.rstrip("/")
            reset_link = f"{base_url}/reset-password?token={token_tho}"
            gui_ok, gui_msg = email_sender.gui_email_otp_dat_lai_mat_khau_chi_tiet(
                email, user.get("ten", "Người học"), otp_tho, reset_link=reset_link
            )
            if not gui_ok and not current_app.config.get("TESTING"):
                return jsonify({
                    "thanh_cong": False,
                    "code": "smtp_send_failed",
                    "thong_bao": f"Gửi email xác nhận thất bại: {gui_msg}. Vui lòng kiểm tra lại cấu hình SMTP hoặc thử lại sau ít phút."
                }), 500
            _OTP_COOLDOWN[email] = now

        return jsonify({
            "thanh_cong": True,
            "thong_bao": "Nếu email này được đăng ký và hỗ trợ khôi phục mật khẩu, chúng tôi đã gửi mã xác nhận.",
            "co_the_gui_lai_sau": 60
        }), 200

    @app.route("/api/auth/reset-password", methods=["POST"])
    def api_dat_lai_mat_khau():
        """Bước 3: Đặt lại mật khẩu mới bằng reset_grant (sau OTP) hoặc token link."""
        data = request.get_json(silent=True) or {}
        grant_or_token = str(data.get("reset_grant") or data.get("token") or "").strip()
        mat_khau = str(data.get("mat_khau") or "")
        xac_nhan = str(data.get("xac_nhan_mat_khau") or "")

        if not grant_or_token:
            return jsonify({
                "thanh_cong": False,
                "code": "missing_token",
                "thong_bao": "Thiếu mã xác thực đặt lại mật khẩu."
            }), 400

        hop_le, loi = kiem_tra_chuan_mat_khau(mat_khau)
        if not hop_le:
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_password",
                "thong_bao": loi
            }), 400

        if mat_khau != xac_nhan:
            return jsonify({
                "thanh_cong": False,
                "code": "password_mismatch",
                "thong_bao": "Mật khẩu xác nhận không khớp."
            }), 400

        grant_hash = bam_token(grant_or_token)

        # 1. Kiểm tra reset_grant từ luồng OTP
        otp_req = database.tim_yeu_cau_theo_reset_grant(grant_hash)
        if otp_req:
            if otp_req.get("used_at") or not otp_req.get("verified_at") or da_het_han_utc(otp_req.get("grant_expires_at", "")):
                return jsonify({
                    "thanh_cong": False,
                    "code": "invalid_or_expired_token",
                    "thong_bao": "Mã xác thực đặt lại mật khẩu không hợp lệ hoặc đã hết hạn."
                }), 400

            user_id = otp_req["user_id"]
            user = database.lay_nguoi_dung(user_id)
            mat_khau_moi_hash = bam_mat_khau(mat_khau)
            database.dat_lai_mat_khau_bang_otp_grant(user_id, mat_khau_moi_hash, otp_req["id"])

            # Vô hiệu hóa phiên hiện tại để buộc người dùng đăng nhập lại bằng mật khẩu mới
            session.clear()

            # Gửi email thông báo bảo mật
            if user and user.get("email"):
                gui_email_thong_bao_doi_mat_khau(user["email"], user.get("ten", "Người học"))

            return jsonify({
                "thanh_cong": True,
                "thong_bao": "Đặt lại mật khẩu thành công! Bạn có thể đăng nhập bằng mật khẩu mới."
            }), 200

        # 2. Kiểm tra token link (tương thích ngược với các liên kết cũ)
        record = database.tim_token_dat_lai(grant_hash)
        if record and not record.get("used_at") and not da_het_han_utc(record.get("expires_at", "")):
            user_id = record["user_id"]
            user = database.lay_nguoi_dung(user_id)
            mat_khau_moi_hash = bam_mat_khau(mat_khau)
            database.dat_lai_mat_khau_nguoi_dung(user_id, mat_khau_moi_hash, grant_hash)

            session.clear()
            if user and user.get("email"):
                gui_email_thong_bao_doi_mat_khau(user["email"], user.get("ten", "Người học"))

            return jsonify({
                "thanh_cong": True,
                "thong_bao": "Đặt lại mật khẩu thành công! Bạn có thể đăng nhập bằng mật khẩu mới."
            }), 200

        return jsonify({
            "thanh_cong": False,
            "code": "invalid_or_expired_token",
            "thong_bao": "Liên kết hoặc mã xác thực đặt lại mật khẩu không hợp lệ hoặc đã hết hạn."
        }), 400

    @app.route("/api/auth/change-password", methods=["POST"])
    def api_doi_mat_khau():
        """Đổi mật khẩu cho người dùng đang đăng nhập."""
        user_id = session.get("user_id")
        if not user_id:
            abort(401)

        csrf = request.headers.get("X-CSRF-Token")
        expected = session.get("csrf_token", "")
        if not csrf or not secrets.compare_digest(csrf, expected):
            abort(403)

        data = request.get_json(silent=True) or {}
        mat_khau_cu = str(data.get("mat_khau_cu") or "")
        mat_khau_moi = str(data.get("mat_khau_moi") or "")
        xac_nhan = str(data.get("xac_nhan_mat_khau") or "")

        if not mat_khau_cu or not mat_khau_moi:
            return jsonify({
                "thanh_cong": False,
                "code": "missing_fields",
                "thong_bao": "Vui lòng nhập đầy đủ mật khẩu hiện tại và mật khẩu mới."
            }), 400

        current_hash = database.lay_mat_khau_hash(user_id)
        if not current_hash:
            return jsonify({
                "thanh_cong": False,
                "code": "no_password_set",
                "thong_bao": "Tài khoản của bạn chưa thiết lập mật khẩu cá nhân. Vui lòng sử dụng tính năng thiết lập mật khẩu."
            }), 400

        if not xac_thuc_mat_khau(current_hash, mat_khau_cu):
            return jsonify({
                "thanh_cong": False,
                "code": "wrong_current_password",
                "thong_bao": "Mật khẩu hiện tại không chính xác."
            }), 400

        if mat_khau_cu == mat_khau_moi:
            return jsonify({
                "thanh_cong": False,
                "code": "same_as_old_password",
                "thong_bao": "Mật khẩu mới không được trùng với mật khẩu hiện tại."
            }), 400

        hop_le, loi = kiem_tra_chuan_mat_khau(mat_khau_moi)
        if not hop_le:
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_password",
                "thong_bao": loi
            }), 400

        if mat_khau_moi != xac_nhan:
            return jsonify({
                "thanh_cong": False,
                "code": "password_mismatch",
                "thong_bao": "Mật khẩu xác nhận không khớp."
            }), 400

        mat_khau_moi_hash = bam_mat_khau(mat_khau_moi)
        database.doi_mat_khau_nguoi_dung(user_id, mat_khau_moi_hash)

        return jsonify({
            "thanh_cong": True,
            "thong_bao": "Đổi mật khẩu thành công!"
        }), 200

    @app.route("/api/auth/set-password", methods=["POST"])
    def api_thiet_lap_mat_khau():
        """Thiết lập mật khẩu lần đầu cho tài khoản Google chưa có mật khẩu."""
        user_id = session.get("user_id")
        if not user_id:
            abort(401)

        csrf = request.headers.get("X-CSRF-Token")
        expected = session.get("csrf_token", "")
        if not csrf or not secrets.compare_digest(csrf, expected):
            abort(403)

        current_hash = database.lay_mat_khau_hash(user_id)
        if current_hash:
            return jsonify({
                "thanh_cong": False,
                "code": "password_already_set",
                "thong_bao": "Tài khoản đã có mật khẩu cá nhân. Vui lòng sử dụng chức năng đổi mật khẩu."
            }), 400

        data = request.get_json(silent=True) or {}
        mat_khau_moi = str(data.get("mat_khau_moi") or "")
        xac_nhan = str(data.get("xac_nhan_mat_khau") or "")

        hop_le, loi = kiem_tra_chuan_mat_khau(mat_khau_moi)
        if not hop_le:
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_password",
                "thong_bao": loi
            }), 400

        if mat_khau_moi != xac_nhan:
            return jsonify({
                "thanh_cong": False,
                "code": "password_mismatch",
                "thong_bao": "Mật khẩu xác nhận không khớp."
            }), 400

        mat_khau_hash = bam_mat_khau(mat_khau_moi)
        try:
            database.thiet_lap_mat_khau_lan_dau(user_id, mat_khau_hash)
            return jsonify({
                "thanh_cong": True,
                "thong_bao": "Thiết lập mật khẩu thành công! Giờ đây bạn có thể đăng nhập bằng email và mật khẩu."
            }), 200
        except database.DaCoMatKhau as e:
            return jsonify({
                "thanh_cong": False,
                "code": "password_already_set",
                "thong_bao": str(e)
            }), 400

    @app.route("/api/auth/methods", methods=["GET"])
    def api_phuong_thuc_xac_thuc():
        """Lấy thông tin các phương thức đăng nhập và bảo mật của tài khoản hiện tại."""
        user_id = session.get("user_id")
        if not user_id:
            abort(401)

        user = database.lay_nguoi_dung(user_id)
        if not user or user.get("status") != "active":
            session.clear()
            abort(401)

        chi_tiet = database.lay_chi_tiet_phuong_thuc_xac_thuc(user_id)
        return jsonify({
            "thanh_cong": True,
            "methods": chi_tiet,
            "csrf_token": session.get("csrf_token")
        }), 200

    @app.route("/api/auth/unlink-google", methods=["POST"])
    def api_huy_lien_ket_google():
        """Hủy liên kết tài khoản Google; chặn nếu Google là phương thức duy nhất."""
        user_id = session.get("user_id")
        if not user_id:
            abort(401)

        csrf = request.headers.get("X-CSRF-Token")
        expected = session.get("csrf_token", "")
        if not csrf or not secrets.compare_digest(csrf, expected):
            abort(403)

        try:
            database.huy_lien_ket_google(user_id)
            return jsonify({
                "thanh_cong": True,
                "thong_bao": "Đã hủy liên kết Google thành công."
            }), 200
        except database.KhongTheHuyPhuongThucDuyNhat as e:
            return jsonify({
                "thanh_cong": False,
                "code": "cannot_unlink_only_method",
                "thong_bao": str(e)
            }), 400
        except ValueError as e:
            return jsonify({
                "thanh_cong": False,
                "code": "unlink_error",
                "thong_bao": str(e)
            }), 400

    @app.route("/api/auth/link-email", methods=["POST"])
    def api_lien_ket_email():
        """Gửi mã OTP 6 chữ số đến địa chỉ email mới để liên kết hoặc thay đổi email."""
        user_id = session.get("user_id")
        if not user_id:
            abort(401)

        csrf = request.headers.get("X-CSRF-Token")
        expected = session.get("csrf_token", "")
        if not csrf or not secrets.compare_digest(csrf, expected):
            abort(403)

        user = database.lay_nguoi_dung(user_id)
        if not user or user.get("status") != "active":
            session.clear()
            abort(401)

        data = request.get_json(silent=True) or {}
        new_email = str(data.get("email") or "").strip().lower()
        mat_khau_hien_tai = str(data.get("mat_khau_hien_tai") or "")

        # 1. Nếu tài khoản đã có mật khẩu cá nhân, yêu cầu xác thực lại
        has_password = database.lay_mat_khau_hash(user_id) is not None
        if has_password:
            if not mat_khau_hien_tai:
                return jsonify({
                    "thanh_cong": False,
                    "code": "missing_password",
                    "thong_bao": "Vui lòng nhập mật khẩu hiện tại để xác nhận liên kết email."
                }), 400
            current_hash = database.lay_mat_khau_hash(user_id)
            if not xac_thuc_mat_khau(current_hash, mat_khau_hien_tai):
                return jsonify({
                    "thanh_cong": False,
                    "code": "wrong_password",
                    "thong_bao": "Mật khẩu hiện tại không chính xác."
                }), 400

        # 2. Kiểm tra định dạng email
        if not new_email or len(new_email) > 120 or not EMAIL_REGEX.match(new_email):
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_email",
                "thong_bao": "Địa chỉ email không đúng định dạng."
            }), 400

        # 3. Kiểm tra nếu email mới trùng với email hiện tại đã xác minh
        if user.get("email") and user["email"].strip().lower() == new_email and user.get("email_verified"):
            return jsonify({
                "thanh_cong": False,
                "code": "same_email",
                "thong_bao": "Tài khoản của bạn đã được liên kết với email này."
            }), 400

        # 4. Kiểm tra email đã thuộc về tài khoản khác chưa
        if database.kiem_tra_email_ton_tai(new_email, exclude_user_id=user_id):
            return jsonify({
                "thanh_cong": False,
                "code": "email_already_exists",
                "thong_bao": "Địa chỉ email này đã được sử dụng bởi một tài khoản khác. Vui lòng chọn email khác."
            }), 409

        # 5. Kiểm tra cấu hình SMTP
        da_cau_hinh, ly_do = email_sender.kiem_tra_cau_hinh_smtp()
        if not da_cau_hinh and not current_app.config.get("TESTING"):
            return jsonify({
                "thanh_cong": False,
                "code": "smtp_not_configured",
                "thong_bao": "Dịch vụ gửi email chưa được cấu hình trên máy chủ. Vui lòng thiết lập SMTP_USERNAME và SMTP_PASSWORD trong tệp .env."
            }), 503

        # 6. Kiểm tra cooldown 60 giây
        ip = request.remote_addr or "127.0.0.1"
        now = time.monotonic()
        last_sent = _RESEND_RATE.get(f"link:{user_id}", 0)
        if now - last_sent < 60:
            remaining = int(60 - (now - last_sent))
            return jsonify({
                "thanh_cong": False,
                "code": "rate_limited",
                "co_the_gui_lai_sau": remaining,
                "thong_bao": f"Vui lòng đợi {remaining} giây trước khi yêu cầu gửi lại mã."
            }), 429

        _RESEND_RATE[f"link:{user_id}"] = now

        # 7. Sinh mã OTP 6 số và lưu vào CSDL
        otp_tho = sinh_ma_otp(6)
        otp_hash = bam_otp(otp_tho, new_email)
        exp_otp_utc = tinh_thoi_gian_het_han_utc(5)
        database.luu_yeu_cau_otp_xac_minh_email(user_id, new_email, otp_hash, exp_otp_utc, ip)

        # 8. Gửi email xác nhận
        gui_ok, gui_msg = email_sender.gui_email_otp_xac_minh_chi_tiet(
            new_email, user.get("ten", "Người học"), otp_tho
        )
        if not gui_ok and not current_app.config.get("TESTING"):
            return jsonify({
                "thanh_cong": False,
                "code": "email_send_failed",
                "thong_bao": "Không thể gửi email xác nhận. Vui lòng thử lại sau ít phút."
            }), 500

        return jsonify({
            "thanh_cong": True,
            "email": new_email,
            "email_da_che": che_email(new_email),
            "co_the_gui_lai_sau": 60,
            "thong_bao": f"Mã xác nhận gồm 6 chữ số đã được gửi đến email {che_email(new_email)}. Vui lòng nhập mã để hoàn tất liên kết."
        }), 200

    @app.route("/api/auth/verify-link-email", methods=["POST"])
    def api_xac_nhan_lien_ket_email():
        """Xác thực mã OTP 6 chữ số để kích hoạt liên kết email với tài khoản."""
        user_id = session.get("user_id")
        if not user_id:
            abort(401)

        csrf = request.headers.get("X-CSRF-Token")
        expected = session.get("csrf_token", "")
        if not csrf or not secrets.compare_digest(csrf, expected):
            abort(403)

        data = request.get_json(silent=True) or {}
        email = str(data.get("email") or "").strip().lower()
        otp = str(data.get("otp") or "").strip()

        if not email or not EMAIL_REGEX.match(email):
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_email",
                "thong_bao": "Địa chỉ email không đúng định dạng."
            }), 400

        if not otp or len(otp) != 6 or not otp.isdigit():
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_otp_format",
                "thong_bao": "Mã xác nhận phải gồm đúng 6 chữ số."
            }), 400

        record = database.tim_yeu_cau_otp_xac_minh_moi_nhat(email)
        if not record or record.get("used_at") or record.get("user_id") != user_id:
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_or_expired_otp",
                "thong_bao": "Yêu cầu xác nhận không tồn tại hoặc đã được sử dụng. Vui lòng gửi lại mã mới."
            }), 400

        if record.get("attempts_left", 0) <= 0:
            return jsonify({
                "thanh_cong": False,
                "code": "max_attempts_exceeded",
                "thong_bao": "Bạn đã nhập sai mã quá 5 lần. Mã xác nhận đã bị vô hiệu hóa, vui lòng yêu cầu mã mới."
            }), 400

        if da_het_han_utc(record.get("expires_at", "")):
            return jsonify({
                "thanh_cong": False,
                "code": "otp_expired",
                "thong_bao": "Mã xác nhận đã hết hạn (hiệu lực 5 phút). Vui lòng yêu cầu mã mới."
            }), 400

        hop_le = xac_thuc_otp_hash(otp, email, record["otp_hash"])
        if not hop_le:
            con_lai = database.ghi_nhan_otp_xac_minh_sai(record["id"])
            if con_lai <= 0:
                return jsonify({
                    "thanh_cong": False,
                    "code": "max_attempts_exceeded",
                    "thong_bao": "Bạn đã nhập sai quá 5 lần. Mã xác nhận đã bị vô hiệu hóa, vui lòng yêu cầu mã mới."
                }), 400
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_otp",
                "thong_bao": f"Mã xác nhận không chính xác. Bạn còn {con_lai} lần thử.",
                "attempts_left": con_lai
            }), 400

        # OTP đúng -> Cập nhật email đã xác minh vào tài khoản
        database.xac_nhan_otp_xac_minh_thanh_cong(record["id"], user_id)
        try:
            database.lien_ket_email_nguoi_dung(user_id, email)
        except database.EmailDaTonTai as e:
            return jsonify({
                "thanh_cong": False,
                "code": "email_already_exists",
                "thong_bao": str(e)
            }), 409

        return jsonify({
            "thanh_cong": True,
            "email": email,
            "thong_bao": "Liên kết địa chỉ email thành công!"
        }), 200

    @app.route("/api/auth/set-username", methods=["POST"])
    def api_dat_ten_tai_khoan():
        """Cập nhật tên tài khoản (username) cho người dùng đang đăng nhập."""
        user_id = session.get("user_id")
        if not user_id:
            abort(401)

        csrf = request.headers.get("X-CSRF-Token")
        expected = session.get("csrf_token", "")
        if not csrf or not secrets.compare_digest(csrf, expected):
            abort(403)

        data = request.get_json(silent=True) or {}
        new_username = str(data.get("username") or "").strip()

        hop_le, loi = kiem_tra_chuan_username(new_username)
        if not hop_le:
            return jsonify({
                "thanh_cong": False,
                "code": "invalid_username",
                "thong_bao": loi
            }), 400

        try:
            database.cap_nhat_username_nguoi_dung(user_id, new_username)
            return jsonify({
                "thanh_cong": True,
                "username": new_username,
                "thong_bao": "Cập nhật tên tài khoản thành công!"
            }), 200
        except database.UsernameDaTonTai as e:
            return jsonify({
                "thanh_cong": False,
                "code": "username_already_exists",
                "thong_bao": str(e)
            }), 409

