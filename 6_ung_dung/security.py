# -*- coding: utf-8 -*-
"""
security.py - Nền tảng bảo mật, băm mật khẩu, quản lý token và phân quyền RBAC
cho ứng dụng Biển Báo AI.

Sử dụng:
- werkzeug.security (thuật toán scrypt chuẩn an toàn nhất hiện nay) để băm mật khẩu.
- secrets (bộ sinh ngẫu nhiên mật mã) để tạo token bí mật.
- hashlib.sha256 để lưu token_hash trong database (không bao giờ lưu token thô).
"""

import base64
import hashlib
import hmac
import os
import re
import secrets
import struct
import time
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import current_app, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash


# ==============================================================================
# 0. QUY TẮC VÀ KIỂM TRA TÊN TÀI KHOẢN (USERNAME)
# ==============================================================================

DO_DAI_USERNAME_TOI_THIEU = 3
DO_DAI_USERNAME_TOI_DA = 30
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.]{3,30}$")

DANH_SACH_USERNAME_CAM = frozenset({
    "admin",
    "administrator",
    "root",
    "system",
    "moderator",
    "guest",
    "null",
    "undefined",
    "bienbao",
    "bienbaoai",
})


def kiem_tra_chuan_username(username: str) -> tuple[bool, str]:
    """Kiểm tra tính hợp lệ của tên tài khoản (username).
    
    Quy tắc:
    - Độ dài từ 3 đến 30 ký tự.
    - Ký tự cho phép: chữ cái (a-z, A-Z), chữ số (0-9), gạch dưới (_), dấu chấm (.).
    - Không chứa dấu cách hay ký tự đặc biệt khác.
    - Không trùng các tên bảo lưu (admin, administrator, root, system, ...).
    
    Trả về: (hop_le: bool, thong_bao_loi: str)
    """
    if not isinstance(username, str) or not username.strip():
        return False, "Vui lòng nhập tên tài khoản."
    u = username.strip()
    if len(u) < DO_DAI_USERNAME_TOI_THIEU or len(u) > DO_DAI_USERNAME_TOI_DA:
        return False, f"Tên tài khoản phải có độ dài từ {DO_DAI_USERNAME_TOI_THIEU} đến {DO_DAI_USERNAME_TOI_DA} ký tự."
    if not USERNAME_REGEX.match(u):
        return False, "Tên tài khoản chỉ được chứa chữ cái, chữ số, dấu gạch dưới (_) và dấu chấm (.), không chứa khoảng trắng."
    if u.lower() in DANH_SACH_USERNAME_CAM:
        return False, "Tên tài khoản này được bảo lưu bởi hệ thống. Vui lòng chọn tên khác."
    return True, ""


# ==============================================================================
# 1. BĂM VÀ KIỂM TRA MẬT KHẨU
# ==============================================================================

DO_DAI_MAT_KHAU_TOI_THIEU = 8
DO_DAI_MAT_KHAU_TOI_DA = 128


def kiem_tra_chuan_mat_khau(mat_khau_tho: str) -> tuple[bool, str]:
    """Kiểm tra độ phức tạp cơ bản của mật khẩu thô.
    
    Trả về: (hop_le: bool, thong_bao_loi: str)
    """
    if not isinstance(mat_khau_tho, str):
        return False, "Mật khẩu phải là chuỗi văn bản."
    if len(mat_khau_tho) < DO_DAI_MAT_KHAU_TOI_THIEU:
        return False, f"Mật khẩu phải có tối thiểu {DO_DAI_MAT_KHAU_TOI_THIEU} ký tự."
    if len(mat_khau_tho) > DO_DAI_MAT_KHAU_TOI_DA:
        return False, f"Mật khẩu không được vượt quá {DO_DAI_MAT_KHAU_TOI_DA} ký tự."
    if "\0" in mat_khau_tho:
        return False, "Mật khẩu không được chứa ký tự NUL."
    return True, ""


def bam_mat_khau(mat_khau_tho: str) -> str:
    """Băm mật khẩu bằng thuật toán scrypt an toàn.
    
    Tuyệt đối không lưu plaintext mật khẩu.
    """
    hop_le, loi = kiem_tra_chuan_mat_khau(mat_khau_tho)
    if not hop_le:
        raise ValueError(loi)
    return generate_password_hash(mat_khau_tho, method="scrypt")


def xac_thuc_mat_khau(mat_khau_hash: str, mat_khau_tho: str) -> bool:
    """Xác minh mật khẩu thô với mã băm đã lưu."""
    if not mat_khau_hash or not mat_khau_tho:
        return False
    return check_password_hash(mat_khau_hash, mat_khau_tho)


# ==============================================================================
# 2. SINH VÀ BĂM TOKEN (XÁC MINH EMAIL & QUÊN MẬT KHẨU)
# ==============================================================================

def sinh_token_bi_mat(so_byte: int = 32) -> str:
    """Sinh chuỗi token ngẫu nhiên bảo mật cao bằng cryptographic PRNG."""
    return secrets.token_urlsafe(so_byte)


def bam_token(token_tho: str) -> str:
    """Băm token bằng SHA-256 để lưu vào cơ sở dữ liệu.
    
    Database chỉ lưu token_hash (64 hex characters). Token thô chỉ gửi cho người dùng.
    """
    if not isinstance(token_tho, str) or not token_tho:
        raise ValueError("Token thô không hợp lệ.")
    return hashlib.sha256(token_tho.encode("utf-8")).hexdigest()


def tinh_thoi_gian_het_han_utc(so_phut: int = 60) -> str:
    """Tính thời điểm hết hạn theo giờ chuẩn UTC định dạng YYYY-MM-DD HH:MM:SS."""
    han = datetime.now(timezone.utc) + timedelta(minutes=so_phut)
    return han.strftime("%Y-%m-%d %H:%M:%S")


def da_het_han_utc(thoi_gian_utc_str: str) -> bool:
    """Kiểm tra thời điểm UTC truyền vào đã qua thời gian hiện tại hay chưa."""
    try:
        # Hỗ trợ cả định dạng SQLite 'YYYY-MM-DD HH:MM:SS' và ISO
        clean_str = thoi_gian_utc_str.replace("T", " ").replace("Z", "")
        if "." in clean_str:
            clean_str = clean_str.split(".")[0]
        han = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > han
    except Exception:
        return True


def lay_otp_secret_key() -> bytes:
    """Lấy khóa bí mật cho HMAC OTP từ cấu hình ứng dụng hoặc biến môi trường."""
    try:
        secret = current_app.config.get("SECRET_KEY")
        if secret and isinstance(secret, str) and secret.strip():
            return secret.strip().encode("utf-8")
    except RuntimeError:
        pass
    env_secret = os.environ.get("OTP_SECRET_KEY") or os.environ.get("SECRET_KEY")
    if env_secret and env_secret.strip():
        return env_secret.strip().encode("utf-8")
    return b"bienbao_ai_otp_hmac_secret_key_default_2026_secure"


def sinh_ma_otp(so_chu_so: int = 6) -> str:
    """Sinh mã OTP gồm đúng số chữ số ngẫu nhiên bằng CSPRNG (secrets module)."""
    if so_chu_so <= 0 or so_chu_so > 10:
        so_chu_so = 6
    val = secrets.randbelow(10 ** so_chu_so)
    return f"{val:0{so_chu_so}d}"


def bam_otp(otp_tho: str, email: str = "") -> str:
    """Băm mã OTP bằng HMAC-SHA256 sử dụng khóa bí mật phía server và email làm ngữ cảnh.
    
    Bảo vệ mã OTP 6 số (không gian 1 triệu khả năng) khỏi tấn công rainbow table/precomputation.
    Tuyệt đối không lưu plaintext và không dùng SHA256 không khóa đơn thuần.
    """
    key = lay_otp_secret_key()
    email_clean = (email or "").strip().lower()
    otp_clean = str(otp_tho).strip()
    msg = f"{email_clean}:{otp_clean}".encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def xac_thuc_otp_hash(otp_tho: str, email: str, otp_hash_luu: str) -> bool:
    """Xác thực mã OTP thô với mã băm HMAC-SHA256 bằng compare_digest chống timing attack."""
    if not otp_tho or not otp_hash_luu:
        return False
    computed = bam_otp(otp_tho, email)
    return secrets.compare_digest(computed, otp_hash_luu)


# ==============================================================================
# 3. XÁC THỰC HAI YẾU TỐ (TOTP MFA - RFC 6238)
# ==============================================================================

def sinh_totp_secret(so_byte: int = 20) -> str:
    """Sinh chuỗi bí mật Base32 cho TOTP (RFC 6238)."""
    raw = secrets.token_bytes(so_byte)
    return base64.b32encode(raw).decode("utf-8").replace("=", "")


def tinh_ma_totp(secret_base32: str, time_step: int | None = None) -> str:
    """Tính mã OTP 6 số theo thời gian (RFC 6238, HMAC-SHA1, chu kỳ 30s)."""
    if time_step is None:
        time_step = int(time.time() // 30)

    # Đảm bảo độ dài padding Base32
    secret_clean = secret_base32.strip().upper()
    missing_padding = len(secret_clean) % 8
    if missing_padding:
        secret_clean += "=" * (8 - missing_padding)

    key = base64.b32decode(secret_clean, casefold=True)
    msg = struct.pack(">Q", time_step)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[19] & 0x0f
    code = (struct.unpack(">I", h[offset:offset + 4])[0] & 0x7fffffff) % 1000000
    return f"{code:06d}"


def xac_thuc_ma_totp(secret_base32: str, otp_code: str, window: int = 1) -> bool:
    """Xác thực mã OTP 6 số, chấp nhận chênh lệch +- window chu kỳ 30 giây."""
    otp_code = str(otp_code).strip()
    if len(otp_code) != 6 or not otp_code.isdigit():
        return False

    current_step = int(time.time() // 30)
    for offset in range(-window, window + 1):
        expected = tinh_ma_totp(secret_base32, current_step + offset)
        if secrets.compare_digest(otp_code, expected):
            return True
    return False


def tao_totp_uri(secret_base32: str, email: str, issuer: str = "BienBaoAI") -> str:
    """Tạo URI chuẩn otpauth:// để quét mã QR bằng Google Authenticator / Authy."""
    email_clean = email.strip()
    return f"otpauth://totp/{issuer}:{email_clean}?secret={secret_base32}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"


# ==============================================================================
# 4. PHÂN QUYỀN RBAC VÀ DECORATORS BẢO VỆ
# ==============================================================================

VAI_TRO_HOP_LE = frozenset({"user", "admin"})
TRANG_THAI_HOP_LE = frozenset({"active", "suspended", "locked"})
ADMIN_SESSION_TIMEOUT_SECONDS = 1800  # 30 phút không hoạt động sẽ hết hạn phiên admin


def kiem_tra_quyen_admin(user: dict | None) -> bool:
    """Kiểm tra tài khoản có vai trò admin đang hoạt động hay không.
    
    Tương thích ngược: Nếu user_id nằm trong SURVEY_ADMIN_USER_IDS của config,
    cũng được xem là admin.
    """
    if not user or not isinstance(user, dict):
        return False
    if user.get("status") != "active":
        return False
    if user.get("role") == "admin":
        return True
    
    try:
        admin_ids = current_app.config.get("SURVEY_ADMIN_USER_IDS", frozenset())
        if user.get("id") in admin_ids:
            return True
    except RuntimeError:
        pass
        
    return False


def yeu_cau_dang_nhap(f):
    """Decorator yêu cầu phiên người dùng đã đăng nhập hợp lệ và đang hoạt động."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from database import lay_nguoi_dung

        user_id = session.get("user_id")
        if not user_id or type(user_id) is not int:
            return jsonify({
                "loi": "Yêu cầu đăng nhập để thực hiện chức năng này.",
                "code": "authentication_required"
            }), 401

        user = lay_nguoi_dung(user_id)
        if not user:
            session.clear()
            return jsonify({
                "loi": "Tài khoản không tồn tại hoặc phiên đã hết hạn.",
                "code": "session_expired"
            }), 401

        if user.get("status") != "active":
            session.clear()
            return jsonify({
                "loi": "Tài khoản đang bị tạm khóa hoặc vô hiệu hóa.",
                "code": "account_suspended"
            }), 403

        g.user = user
        g.user_id = user["id"]
        return f(*args, **kwargs)

    return decorated_function


def yeu_cau_admin(f):
    """Decorator yêu cầu quyền quản trị viên (Admin), xác thực MFA và bảo vệ CSRF."""
    @wraps(f)
    @yeu_cau_dang_nhap
    def decorated_function(*args, **kwargs):
        import database

        user = getattr(g, "user", None)
        if not kiem_tra_quyen_admin(user):
            return jsonify({
                "loi": "Bạn không có quyền truy cập chức năng quản trị.",
                "code": "admin_required"
            }), 403

        # 1. Kiểm tra MFA nếu tài khoản admin đã kích hoạt MFA
        mfa = database.lay_mfa_admin(user["id"])
        if mfa and mfa["is_enabled"]:
            if not session.get("admin_mfa_verified"):
                return jsonify({
                    "loi": "Yêu cầu hoàn tất xác thực hai yếu tố (MFA/TOTP) trước khi truy cập.",
                    "code": "mfa_required"
                }), 401

            # Kiểm tra thời gian hết hạn phiên Admin (30 phút không hoạt động)
            last_active = session.get("admin_last_active", 0)
            now = time.time()
            if last_active and (now - last_active > ADMIN_SESSION_TIMEOUT_SECONDS):
                session["admin_mfa_verified"] = False
                return jsonify({
                    "loi": "Phiên quản trị đã hết hạn do không hoạt động. Vui lòng xác thực lại MFA.",
                    "code": "admin_session_expired"
                }), 401

            # Cập nhật thời điểm hoạt động mới nhất
            session["admin_last_active"] = now

        # 2. Bảo vệ CSRF đối với các thao tác thay đổi dữ liệu (POST, PATCH, PUT, DELETE)
        if request.method in ("POST", "PATCH", "PUT", "DELETE"):
            csrf = request.headers.get("X-CSRF-Token")
            expected = session.get("csrf_token", "")
            if not csrf or not expected or not secrets.compare_digest(csrf, expected):
                return jsonify({
                    "loi": "Mã xác thực CSRF không hợp lệ hoặc đã hết hạn.",
                    "code": "csrf_invalid"
                }), 403

        g.is_admin = True
        return f(*args, **kwargs)

    return decorated_function
