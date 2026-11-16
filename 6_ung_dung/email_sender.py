# -*- coding: utf-8 -*-
"""
email_sender.py - Adapter gửi email xác minh và thông báo cho Biển Báo AI.

Hỗ trợ:
1. Gửi qua Gmail SMTP thực tế (Google App Password 16 ký tự, cổng 587 STARTTLS hoặc 465 SSL).
2. Tương thích linh hoạt các biến môi trường: SMTP_USERNAME/SMTP_USER, SMTP_PASSWORD/SMTP_PASS,
   SMTP_HOST, SMTP_PORT, SMTP_USE_TLS, SMTP_FROM_EMAIL, SMTP_FROM_NAME.
3. Fallback sang Outbox giả lập an toàn khi chạy chế độ Development hoặc Kiểm thử tự động.
4. Tuyệt đối không hardcode mật khẩu, không in mã OTP hoặc thông tin nhạy cảm ra log.
"""

import logging
import os
import smtplib
import socket
from email.message import EmailMessage
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

logger = logging.getLogger("bienbao_email")

# Đường dẫn tuyệt đối tới file .env của 6_ung_dung
DUONG_DAN_ENV = Path(__file__).resolve().parent / ".env"

# Tự động nạp file .env tuyệt đối ngay khi import module
if DUONG_DAN_ENV.is_file():
    load_dotenv(str(DUONG_DAN_ENV), override=True)

# Danh sách outbox giả lập trong bộ nhớ phục vụ chạy unit test tự động
OUTBOX_TEST: List[Dict[str, str]] = []


def lay_cau_hinh_smtp(force_reload: bool = False) -> dict:
    """Đọc và chuẩn hóa cấu hình SMTP từ biến môi trường.
    
    Hỗ trợ linh hoạt cả quy ước SMTP_USERNAME/SMTP_USER và SMTP_PASSWORD/SMTP_PASS.
    Tự động nạp lại từ .env với override=True nếu chưa có thông tin hoặc khi yêu cầu.
    """
    if force_reload or not (os.environ.get("SMTP_USERNAME") or os.environ.get("SMTP_USER")):
        if DUONG_DAN_ENV.is_file():
            load_dotenv(str(DUONG_DAN_ENV), override=True)

    host = os.environ.get("SMTP_HOST", "").strip() or "smtp.gmail.com"
    port_str = os.environ.get("SMTP_PORT", "").strip() or "587"
    try:
        port = int(port_str)
    except ValueError:
        port = 587

    use_tls_str = os.environ.get("SMTP_USE_TLS", "true").strip().lower()
    use_tls = use_tls_str in ("true", "1", "yes", "on")

    user = (os.environ.get("SMTP_USERNAME") or os.environ.get("SMTP_USER") or "").strip()
    password = (os.environ.get("SMTP_PASSWORD") or os.environ.get("SMTP_PASS") or "").strip()
    from_email = (os.environ.get("SMTP_FROM_EMAIL") or user).strip()
    from_name = (os.environ.get("SMTP_FROM_NAME") or "Biển Báo AI").strip()

    is_configured = bool(host and user and password)

    return {
        "host": host,
        "port": port,
        "use_tls": use_tls,
        "user": user,
        "password": password,
        "from_email": from_email,
        "from_name": from_name,
        "is_configured": is_configured,
    }


def kiem_tra_cau_hinh_smtp() -> Tuple[bool, str]:
    """Kiểm tra xem hệ thống đã được cấu hình SMTP thực tế hay chưa."""
    cfg = lay_cau_hinh_smtp(force_reload=True)
    if cfg["is_configured"]:
        return True, f"Đã cấu hình SMTP: {cfg['host']}:{cfg['port']} (user: {cfg['user']})"
    return False, "Chưa cấu hình SMTP (Cần thiết lập SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD trong .env)"


def _gui_qua_smtp(
    to_email: str,
    subject: str,
    text_content: str,
    html_content: str,
    extra_test_data: Optional[dict] = None
) -> Tuple[bool, str]:
    """Hàm nội bộ thực thi kết nối SMTP và gửi email an toàn."""
    to_email = to_email.strip().lower()
    cfg = lay_cau_hinh_smtp()

    # Kiểm tra xem đang chạy trong môi trường Flask testing hay không
    is_testing_env = False
    try:
        from flask import current_app
        if current_app and current_app.config.get("TESTING"):
            is_testing_env = True
    except Exception:
        pass
    if os.environ.get("FLASK_ENV") == "testing" or os.environ.get("BIENBAO_TESTING") == "1":
        is_testing_env = True

    # 1. Chế độ kiểm thử tự động (Unit Test): Luôn dùng Fake Outbox giả lập an toàn, không gửi mạng
    if is_testing_env:
        record = {
            "to": to_email,
            "subject": subject,
            "mode": "dev_test_outbox"
        }
        if extra_test_data:
            record.update(extra_test_data)
        OUTBOX_TEST.append(record)
        logger.info(f"[OUTBOX_TEST] Đã lưu email thử nghiệm tới {to_email}")
        return True, "Mô phỏng gửi email thành công (Chế độ Kiểm thử)"

    # 2. Nếu chưa cấu hình SMTP trên máy chủ
    if not cfg["is_configured"]:
        record = {
            "to": to_email,
            "subject": subject,
            "mode": "dev_test_outbox"
        }
        if extra_test_data:
            record.update(extra_test_data)
        OUTBOX_TEST.append(record)

        logger.warning(
            "Chưa cấu hình thông tin SMTP_USERNAME/SMTP_PASSWORD trong .env. "
            "Email chưa được gửi thực tế."
        )
        return False, "Chưa cấu hình SMTP_USERNAME và SMTP_PASSWORD trong tệp .env"

    # Đã có cấu hình -> Thực hiện gửi qua SMTP
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{cfg['from_name']} <{cfg['from_email']}>"
    msg["To"] = to_email
    msg.set_content(text_content)
    msg.add_alternative(html_content, subtype="html")

    try:
        if cfg["port"] == 465 or (not cfg["use_tls"] and cfg["port"] != 587):
            # Kết nối SSL trực tiếp (Port 465)
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=15) as server:
                server.login(cfg["user"], cfg["password"])
                server.send_message(msg)
        else:
            # Kết nối STARTTLS (Port 587 mặc định của Gmail)
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
                if cfg["use_tls"]:
                    server.starttls()
                server.login(cfg["user"], cfg["password"])
                server.send_message(msg)

        logger.info(f"Đã gửi email '{subject}' qua SMTP tới {to_email}")

        # Đồng thời lưu vào OUTBOX_TEST để phục vụ kiểm tra nếu cần
        record = {
            "to": to_email,
            "subject": subject,
            "mode": "smtp_sent"
        }
        if extra_test_data:
            record.update(extra_test_data)
        OUTBOX_TEST.append(record)

        return True, "Gửi email thành công"

    except smtplib.SMTPAuthenticationError:
        error_msg = "Lỗi xác thực Gmail SMTP: Sai địa chỉ email hoặc Mật khẩu ứng dụng (Google App Password 16 ký tự)."
        logger.error(f"Lỗi xác thực SMTP khi gửi tới {to_email}")
        _ghi_nhan_loi_outbox(to_email, subject, error_msg, extra_test_data)
        return False, error_msg

    except (smtplib.SMTPConnectError, TimeoutError, socket.timeout, ConnectionRefusedError, OSError) as e:
        error_msg = f"Lỗi kết nối mạng: Không thể kết nối đến máy chủ SMTP ({cfg['host']}:{cfg['port']}). Vui lòng kiểm tra Internet hoặc cổng kết nối."
        logger.error(f"Lỗi kết nối SMTP tới {cfg['host']}:{cfg['port']}: {type(e).__name__}")
        _ghi_nhan_loi_outbox(to_email, subject, error_msg, extra_test_data)
        return False, error_msg

    except smtplib.SMTPException as e:
        error_msg = f"Lỗi giao thức SMTP: {type(e).__name__}"
        logger.error(f"Lỗi SMTP khi gửi tới {to_email}: {type(e).__name__}")
        _ghi_nhan_loi_outbox(to_email, subject, error_msg, extra_test_data)
        return False, error_msg

    except Exception as e:
        error_msg = f"Lỗi hệ thống khi gửi email: {type(e).__name__}"
        logger.error(f"Lỗi không xác định khi gửi email tới {to_email}: {type(e).__name__}")
        _ghi_nhan_loi_outbox(to_email, subject, error_msg, extra_test_data)
        return False, error_msg


def _ghi_nhan_loi_outbox(to_email: str, subject: str, err: str, extra: Optional[dict] = None):
    rec = {
        "to": to_email,
        "subject": subject,
        "error": err
    }
    if extra:
        rec.update(extra)
    OUTBOX_TEST.append(rec)


# =============================================================================
# 1. MẪU EMAIL XÁC MINH TÀI KHOẢN (OTP 6 SỐ & LINK DỰ PHÒNG)
# =============================================================================

def tao_noi_dung_html_otp_xac_minh(ho_ten: str, otp_code: str) -> str:
    """Tạo mẫu email HTML gửi mã OTP 6 số xác minh tài khoản đăng ký mới."""
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Biển Báo AI – Mã xác nhận tài khoản</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 24px; }}
    .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05); }}
    .header {{ background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%); padding: 28px 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.02em; }}
    .header p {{ margin: 6px 0 0 0; font-size: 13.5px; opacity: 0.9; }}
    .body {{ padding: 32px 28px; line-height: 1.6; font-size: 15px; color: #334155; }}
    .body p {{ margin: 0 0 16px 0; }}
    .otp-box {{ text-align: center; margin: 24px 0; padding: 18px; background: #eff6ff; border: 2px dashed #93c5fd; border-radius: 12px; }}
    .otp-code {{ font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #1d4ed8; font-family: Consolas, monospace, sans-serif; display: inline-block; }}
    .warning-box {{ background-color: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 6px; font-size: 13.5px; color: #92400e; margin: 20px 0; }}
    .footer {{ background-color: #f8fafc; padding: 20px 28px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Biển Báo AI</h1>
      <p>Mã xác nhận kích hoạt tài khoản</p>
    </div>
    <div class="body">
      <p>Xin chào,</p>
      <p>Mã xác nhận của bạn là:</p>
      <div class="otp-box">
        <span class="otp-code">{otp_code}</span>
      </div>
      <div class="warning-box">
        Mã có hiệu lực trong <strong>5 phút</strong>.
      </div>
      <p style="font-size: 13.5px; color: #64748b;">Nếu bạn không yêu cầu mã này, hãy bỏ qua email.</p>
      <p style="margin-top: 24px;">Trân trọng,<br><strong>Biển Báo AI.</strong></p>
    </div>
    <div class="footer">
      <p>Đồ án tốt nghiệp: "Xây dựng ứng dụng trợ giúp người học nhận dạng biển báo giao thông sử dụng mạng nơron nhân tạo".</p>
    </div>
  </div>
</body>
</html>"""


def gui_email_otp_xac_minh(to_email: str, ho_ten: str, otp_code: str, verify_link: str = "") -> bool:
    """Gửi email chứa mã OTP 6 chữ số để kích hoạt tài khoản đăng ký mới."""
    ok, _ = gui_email_otp_xac_minh_chi_tiet(to_email, ho_ten, otp_code, verify_link)
    return ok


def gui_email_otp_xac_minh_chi_tiet(
    to_email: str, ho_ten: str, otp_code: str, verify_link: str = ""
) -> Tuple[bool, str]:
    """Gửi email OTP kích hoạt tài khoản đăng ký mới, trả về (thành_công, thông_báo_kết_quả)."""
    subject = "Biển Báo AI – Mã xác nhận tài khoản"
    text_content = f"""Xin chào,

Mã xác nhận của bạn là:

{otp_code}

Mã có hiệu lực trong 5 phút.

Nếu bạn không yêu cầu mã này, hãy bỏ qua email.

Trân trọng,
Biển Báo AI."""

    html_content = tao_noi_dung_html_otp_xac_minh(ho_ten, otp_code)
    return _gui_qua_smtp(
        to_email,
        subject,
        text_content,
        html_content,
        extra_test_data={
            "otp": otp_code,
            "link": verify_link,
            "type": "registration_otp"
        }
    )


def tao_noi_dung_html_xac_minh(ho_ten: str, verify_link: str) -> str:
    """Tạo mẫu email HTML xác minh tài khoản chuẩn thương hiệu Biển Báo AI."""
    ten_hien_thi = ho_ten if ho_ten else "Người học"
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Biển Báo AI – Mã xác nhận tài khoản</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 24px; }}
    .container {{ max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05); }}
    .header {{ background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%); padding: 32px 28px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.02em; }}
    .header p {{ margin: 6px 0 0 0; font-size: 13.5px; opacity: 0.9; }}
    .body {{ padding: 32px 28px; line-height: 1.6; font-size: 15px; color: #334155; }}
    .body p {{ margin: 0 0 16px 0; }}
    .btn-wrap {{ text-align: center; margin: 28px 0; }}
    .btn {{ display: inline-block; background-color: #2563eb; color: #ffffff !important; padding: 13px 30px; border-radius: 10px; font-weight: 700; text-decoration: none; font-size: 15px; }}
    .btn:hover {{ background-color: #1d4ed8; }}
    .link-alt {{ font-size: 12.5px; word-break: break-all; color: #64748b; background: #f1f5f9; padding: 12px; border-radius: 8px; margin-top: 16px; }}
    .footer {{ background-color: #f8fafc; padding: 20px 28px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Biển Báo AI</h1>
      <p>Học biển báo giao thông thông minh với AI</p>
    </div>
    <div class="body">
      <p>Xin chào <strong>{ten_hien_thi}</strong>,</p>
      <p>Cảm ơn bạn đã đăng ký tài khoản tại <strong>Biển Báo AI</strong>. Để hoàn tất kích hoạt tài khoản và bắt đầu lưu trữ tiến độ học tập, vui lòng xác nhận địa chỉ email của bạn bằng nút bên dưới:</p>
      <div class="btn-wrap">
        <a class="btn" href="{verify_link}" target="_blank" rel="noopener noreferrer">Xác minh email ngay</a>
      </div>
      <p style="font-size: 13.5px; color: #64748b;">Liên kết này có hiệu lực trong vòng <strong>24 giờ</strong> và chỉ được sử dụng một lần duy nhất.</p>
      <p style="font-size: 13px; color: #64748b; margin-top: 20px;">Nếu nút trên không mở được, bạn có thể sao chép và dán liên kết sau vào trình duyệt:</p>
      <div class="link-alt">{verify_link}</div>
    </div>
    <div class="footer">
      <p>Đồ án tốt nghiệp: "Xây dựng ứng dụng trợ giúp người học nhận dạng biển báo giao thông sử dụng mạng nơron nhân tạo".</p>
      <p>Nếu bạn không thực hiện đăng ký này, vui lòng bỏ qua email.</p>
      <p style="margin-top: 8px;">Trân trọng,<br><strong>Biển Báo AI</strong></p>
    </div>
  </div>
 </body>
</html>"""


def gui_email_xac_minh(to_email: str, ho_ten: str, verify_link: str) -> bool:
    """Gửi email xác minh tài khoản đến người dùng."""
    subject = "Biển Báo AI – Mã xác nhận tài khoản"
    text_content = f"""Xin chào,

Cảm ơn bạn đã đăng ký tài khoản tại Biển Báo AI.
Vui lòng nhấp vào liên kết sau để kích hoạt tài khoản của bạn (liên kết có hiệu lực trong 24 giờ):

{verify_link}

Nếu bạn không yêu cầu đăng ký tài khoản này, hãy bỏ qua email.

Trân trọng,
Biển Báo AI."""

    html_content = tao_noi_dung_html_xac_minh(ho_ten, verify_link)
    ok, _ = _gui_qua_smtp(
        to_email,
        subject,
        text_content,
        html_content,
        extra_test_data={"link": verify_link, "type": "email_verification"}
    )
    return ok


# =============================================================================
# 2. MẪU EMAIL KHÔI PHỤC MẬT KHẨU (LINK DỰ PHÒNG)
# =============================================================================

def tao_noi_dung_html_dat_lai_mat_khau(ho_ten: str, reset_link: str) -> str:
    """Tạo mẫu email HTML khôi phục mật khẩu chuẩn thương hiệu Biển Báo AI."""
    ten_hien_thi = ho_ten if ho_ten else "Người học"
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Biển Báo AI – Yêu cầu khôi phục mật khẩu</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 24px; }}
    .container {{ max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05); }}
    .header {{ background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%); padding: 32px 28px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.02em; }}
    .header p {{ margin: 6px 0 0 0; font-size: 13.5px; opacity: 0.9; }}
    .body {{ padding: 32px 28px; line-height: 1.6; font-size: 15px; color: #334155; }}
    .body p {{ margin: 0 0 16px 0; }}
    .btn-wrap {{ text-align: center; margin: 28px 0; }}
    .btn {{ display: inline-block; background-color: #2563eb; color: #ffffff !important; padding: 13px 30px; border-radius: 10px; font-weight: 700; text-decoration: none; font-size: 15px; }}
    .btn:hover {{ background-color: #1d4ed8; }}
    .link-alt {{ font-size: 12.5px; word-break: break-all; color: #64748b; background: #f1f5f9; padding: 12px; border-radius: 8px; margin-top: 16px; }}
    .warning-box {{ background-color: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 6px; font-size: 13.5px; color: #92400e; margin: 20px 0; }}
    .footer {{ background-color: #f8fafc; padding: 20px 28px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Biển Báo AI</h1>
      <p>Yêu cầu khôi phục mật khẩu tài khoản</p>
    </div>
    <div class="body">
      <p>Xin chào <strong>{ten_hien_thi}</strong>,</p>
      <p>Hệ thống nhận được yêu cầu đặt lại mật khẩu cho tài khoản Biển Báo AI của bạn. Hãy nhấp vào nút bên dưới để tiến hành tạo mật khẩu mới:</p>
      <div class="btn-wrap">
        <a class="btn" href="{reset_link}" target="_blank" rel="noopener noreferrer">Đặt lại mật khẩu ngay</a>
      </div>
      <div class="warning-box">
        <strong>Lưu ý bảo mật:</strong> Liên kết này chỉ có hiệu lực trong vòng <strong>30 phút</strong> và sẽ tự động vô hiệu hóa sau một lần sử dụng.
      </div>
      <p style="font-size: 13px; color: #64748b;">Nếu nút phía trên không bấm được, bạn vui lòng dán đường dẫn này vào trình duyệt:</p>
      <div class="link-alt">{reset_link}</div>
    </div>
    <div class="footer">
      <p>Nếu bạn không gửi yêu cầu khôi phục này, tài khoản của bạn vẫn an toàn và bạn có thể yên tâm bỏ qua email này.</p>
      <p style="margin-top: 8px;">Trân trọng,<br><strong>Biển Báo AI</strong></p>
    </div>
  </div>
</body>
</html>"""


def gui_email_dat_lai_mat_khau(to_email: str, ho_ten: str, reset_link: str) -> bool:
    """Gửi email chứa liên kết đặt lại mật khẩu cho người dùng."""
    subject = "Biển Báo AI – Khôi phục mật khẩu tài khoản"
    text_content = f"""Xin chào {ho_ten or 'Người học'},

Hệ thống nhận được yêu cầu đặt lại mật khẩu cho tài khoản Biển Báo AI của bạn.
Vui lòng truy cập đường dẫn sau để đặt lại mật khẩu (liên kết có hiệu lực trong vòng 30 phút và chỉ dùng được 1 lần):

{reset_link}

Nếu bạn không gửi yêu cầu này, vui lòng bỏ qua email. Mật khẩu hiện tại của bạn vẫn được giữ an toàn.

Trân trọng,
Biển Báo AI."""

    html_content = tao_noi_dung_html_dat_lai_mat_khau(ho_ten, reset_link)
    ok, _ = _gui_qua_smtp(
        to_email,
        subject,
        text_content,
        html_content,
        extra_test_data={"link": reset_link, "type": "password_reset"}
    )
    return ok


# =============================================================================
# 3. MẪU EMAIL MÃ OTP ĐẶT LẠI MẬT KHẨU (QUY CHUẨN MỤC 4)
# =============================================================================

def tao_noi_dung_html_otp_dat_lai_mat_khau(ho_ten: str, otp_code: str) -> str:
    """Tạo mẫu email HTML gửi mã OTP xác nhận đặt lại mật khẩu."""
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Biển Báo AI – Mã xác nhận tài khoản</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 24px; }}
    .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05); }}
    .header {{ background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%); padding: 28px 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.02em; }}
    .header p {{ margin: 6px 0 0 0; font-size: 13.5px; opacity: 0.9; }}
    .body {{ padding: 32px 28px; line-height: 1.6; font-size: 15px; color: #334155; }}
    .body p {{ margin: 0 0 16px 0; }}
    .otp-box {{ text-align: center; margin: 24px 0; padding: 18px; background: #eff6ff; border: 2px dashed #93c5fd; border-radius: 12px; }}
    .otp-code {{ font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #1d4ed8; font-family: Consolas, monospace, sans-serif; display: inline-block; }}
    .warning-box {{ background-color: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 6px; font-size: 13.5px; color: #92400e; margin: 20px 0; }}
    .footer {{ background-color: #f8fafc; padding: 20px 28px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Biển Báo AI</h1>
      <p>Mã xác nhận đặt lại mật khẩu</p>
    </div>
    <div class="body">
      <p>Xin chào,</p>
      <p>Mã xác nhận của bạn là:</p>
      <div class="otp-box">
        <span class="otp-code">{otp_code}</span>
      </div>
      <div class="warning-box">
        Mã có hiệu lực trong <strong>5 phút</strong>.
      </div>
      <p style="font-size: 13.5px; color: #64748b;">Nếu bạn không yêu cầu mã này, hãy bỏ qua email.</p>
      <p style="margin-top: 24px;">Trân trọng,<br><strong>Biển Báo AI.</strong></p>
    </div>
    <div class="footer">
      <p>Đồ án tốt nghiệp: "Xây dựng ứng dụng trợ giúp người học nhận dạng biển báo giao thông sử dụng mạng nơron nhân tạo".</p>
    </div>
  </div>
</body>
</html>"""


def gui_email_otp_dat_lai_mat_khau(to_email: str, ho_ten: str, otp_code: str, reset_link: str = "") -> bool:
    """Gửi email chứa mã OTP 6 chữ số để xác nhận đặt lại mật khẩu."""
    ok, _ = gui_email_otp_dat_lai_mat_khau_chi_tiet(to_email, ho_ten, otp_code, reset_link)
    return ok


def gui_email_otp_dat_lai_mat_khau_chi_tiet(
    to_email: str, ho_ten: str, otp_code: str, reset_link: str = ""
) -> Tuple[bool, str]:
    """Gửi email OTP đặt lại mật khẩu, trả về (thành_công, thông_báo_kết_quả)."""
    subject = "Biển Báo AI – Mã xác nhận tài khoản"
    text_content = f"""Xin chào,

Mã xác nhận của bạn là:

{otp_code}

Mã có hiệu lực trong 5 phút.

Nếu bạn không yêu cầu mã này, hãy bỏ qua email.

Trân trọng,
Biển Báo AI."""

    html_content = tao_noi_dung_html_otp_dat_lai_mat_khau(ho_ten, otp_code)
    return _gui_qua_smtp(
        to_email,
        subject,
        text_content,
        html_content,
        extra_test_data={
            "otp": otp_code,
            "link": reset_link,
            "type": "password_reset_otp"
        }
    )


# =============================================================================
# 4. MẪU EMAIL THÔNG BÁO ĐỔI MẬT KHẨU THÀNH CÔNG
# =============================================================================

def tao_noi_dung_html_thong_bao_doi_mat_khau(ho_ten: str) -> str:
    """Tạo mẫu email thông báo đổi mật khẩu thành công."""
    ten_hien_thi = ho_ten if ho_ten else "Người học"
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Biển Báo AI – Mật khẩu của bạn đã thay đổi</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 24px; }}
    .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05); }}
    .header {{ background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%); padding: 28px 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.02em; }}
    .header p {{ margin: 6px 0 0 0; font-size: 13.5px; opacity: 0.9; }}
    .body {{ padding: 32px 28px; line-height: 1.6; font-size: 15px; color: #334155; }}
    .body p {{ margin: 0 0 16px 0; }}
    .alert-box {{ background-color: #eff6ff; border: 1px solid #bfdbfe; border-left: 4px solid #2563eb; padding: 14px 16px; border-radius: 8px; font-size: 14px; color: #1e40af; margin: 20px 0; }}
    .footer {{ background-color: #f8fafc; padding: 20px 28px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Biển Báo AI</h1>
      <p>Thông báo bảo mật tài khoản</p>
    </div>
    <div class="body">
      <p>Xin chào <strong>{ten_hien_thi}</strong>,</p>
      <div class="alert-box">
        Mật khẩu tài khoản <strong>Biển Báo AI</strong> của bạn vừa được thay đổi thành công.
      </div>
      <p>Tất cả các phiên đăng nhập cũ trên các thiết bị khác đã được vô hiệu hóa để bảo vệ tài khoản của bạn.</p>
      <p style="font-size: 13.5px; color: #dc2626;">Nếu bạn không thực hiện thay đổi này, hãy liên hệ ngay với chúng tôi để bảo vệ tài khoản.</p>
      <p style="margin-top: 24px;">Trân trọng,<br><strong>Biển Báo AI.</strong></p>
    </div>
    <div class="footer">
      <p>Đồ án tốt nghiệp: "Xây dựng ứng dụng trợ giúp người học nhận dạng biển báo giao thông sử dụng mạng nơron nhân tạo".</p>
    </div>
  </div>
</body>
</html>"""


def gui_email_thong_bao_doi_mat_khau(to_email: str, ho_ten: str) -> bool:
    """Gửi email thông báo cho người dùng khi mật khẩu vừa được đổi thành công."""
    subject = "Biển Báo AI – Mật khẩu tài khoản đã được thay đổi"
    text_content = f"""Xin chào {ho_ten or 'Người học'},

Mật khẩu tài khoản Biển Báo AI của bạn vừa được thay đổi thành công.
Tất cả các phiên đăng nhập cũ đã được vô hiệu hóa để bảo vệ an toàn cho tài khoản của bạn.

Nếu bạn không thực hiện thay đổi này, vui lòng liên hệ ngay với chúng tôi để bảo vệ tài khoản.

Trân trọng,
Biển Báo AI."""

    html_content = tao_noi_dung_html_thong_bao_doi_mat_khau(ho_ten)
    ok, _ = _gui_qua_smtp(
        to_email,
        subject,
        text_content,
        html_content,
        extra_test_data={"type": "password_changed_notification"}
    )
    return ok
