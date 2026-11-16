#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
admin_cli.py - Công cụ dòng lệnh (CLI) quản trị tài khoản và phân quyền
cho hệ thống Biển Báo AI.

Chỉ được thực thi trực tiếp trên máy chủ hoặc môi trường quản trị đáng tin cậy.
Tuyệt đối không để lộ mật khẩu, token hay dữ liệu nhạy cảm.
"""

import argparse
import os
import sys
from datetime import datetime, timezone

# Đảm bảo import được database
GOC = os.path.dirname(os.path.abspath(__file__))
if GOC not in sys.path:
    sys.path.insert(0, GOC)

import database


def log_thao_tac(thong_diep: str):
    """Ghi nhật ký thao tác với timestamp UTC chuẩn."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now_utc}] {thong_diep}")


def lenh_danh_sach(args):
    """Liệt kê toàn bộ người dùng trong hệ thống."""
    users = database.danh_sach_tat_ca_nguoi_dung()
    if not users:
        print("Chưa có tài khoản nào trong hệ thống.")
        return

    print("=" * 88)
    print(f"{'ID':<6} | {'Email':<30} | {'Tên':<20} | {'Vai trò':<8} | {'Trạng thái':<10} | {'Đã xác minh'}")
    print("-" * 88)
    for u in users:
        email = u.get("email") or "(Chưa có email)"
        ten = u.get("ten") or ""
        role = u.get("role", "user")
        status = u.get("status", "active")
        verified = "Có" if u.get("email_verified") else "Chưa"
        print(f"{u['id']:<6} | {email:<30} | {ten[:20]:<20} | {role:<8} | {status:<10} | {verified}")
    print("=" * 88)
    print(f"Tổng cộng: {len(users)} tài khoản.")


def lenh_kiem_tra(args):
    """Kiểm tra chi tiết thông tin và quyền hạn của một tài khoản."""
    user = database.tim_nguoi_dung_theo_email_hoac_id(args.dinh_danh)
    if not user:
        print(f"LỖI: Không tìm thấy tài khoản tương ứng với '{args.dinh_danh}'.")
        sys.exit(1)

    print("--- THÔNG TIN TÀI KHOẢN ---")
    print(f"  + ID:              {user['id']}")
    print(f"  + Email:           {user.get('email') or '(Chưa có)'}")
    print(f"  + Họ tên:          {user.get('ten')}")
    print(f"  + Vai trò (Role):  {user.get('role')}")
    print(f"  + Trạng thái:      {user.get('status')}")
    print(f"  + Đã xác minh:     {'Có' if user.get('email_verified') else 'Chưa'}")
    print(f"  + Ngày tạo:        {user.get('ngay_tao')}")
    print(f"  + Cập nhật cuối:   {user.get('updated_at')}")


def lenh_cap_quyen(args):
    """Cấp quyền quản trị viên (Admin) cho một tài khoản đã xác minh email."""
    user = database.tim_nguoi_dung_theo_email_hoac_id(args.dinh_danh)
    if not user:
        print(f"LỖI: Không tìm thấy tài khoản tương ứng với '{args.dinh_danh}'.")
        sys.exit(1)

    if user.get("role") == "admin":
        print(f"Thông báo: Tài khoản ID {user['id']} ({user.get('email')}) đã có vai trò 'admin'.")
        return

    if not user.get("email_verified"):
        print(f"LỖI BẢO MẬT: Tài khoản ID {user['id']} chưa được xác minh email (email_verified=0).")
        print("Chỉ được cấp quyền Admin cho tài khoản có email đã được xác minh.")
        sys.exit(1)

    if user.get("status") != "active":
        print(f"LỖI: Tài khoản ID {user['id']} không ở trạng thái hoạt động (status={user.get('status')}).")
        sys.exit(1)

    # Kiểm tra chính sách chỉ một Admin chính
    cho_phep_nhieu = getattr(args, "cho_phep_nhieu_admin", False)
    so_admin = database.dem_so_luong_admin()
    if so_admin >= 1 and not cho_phep_nhieu:
        print("LỖI CHÍNH SÁCH BẢO MẬT:")
        print(f"Hệ thống hiện đã có {so_admin} tài khoản Admin chính.")
        print("Chính sách hệ thống ban đầu chỉ cho phép DUY NHẤT 1 tài khoản Admin chính.")
        print("Nếu thực sự cần thêm, vui lòng truyền thêm cờ --cho-phep-nhieu-admin.")
        sys.exit(1)

    if not args.xac_nhan:
        print(f"CẢNH BÁO QUẢN TRỊ:")
        print(f"Bạn đang chuẩn bị cấp toàn quyền ADMIN cho:")
        print(f"  - ID:    {user['id']}")
        print(f"  - Email: {user.get('email')}")
        print(f"  - Tên:   {user.get('ten')}")
        xac_nhan = input("Nhập 'YES' để xác nhận thay đổi: ")
        if xac_nhan.strip() != "YES":
            print("Đã hủy thao tác. Không có thay đổi nào được thực hiện.")
            return

    try:
        user_moi = database.cap_nhat_vai_tro_nguoi_dung(user["id"], "admin", cho_phep_nhieu_admin=cho_phep_nhieu)
        database.ghi_audit_log(
            actor_user_id=None,
            action="promote_admin_cli",
            target_type="user",
            target_id=user["id"],
            details={"email": user.get("email"), "ten": user.get("ten"), "source": "admin_cli"}
        )
        log_thao_tac(f"ĐÃ CẤP QUYỀN ADMIN: ID={user_moi['id']} Email={user_moi.get('email')} Tên='{user_moi.get('ten')}'")
        print(f"Thành công: Tài khoản ID {user_moi['id']} ({user_moi.get('email')}) đã trở thành ADMIN CHÍNH.")
    except ValueError as e:
        print(f"LỖI: {e}")
        sys.exit(1)


def lenh_ha_quyen(args):
    """Hạ quyền quản trị viên (Admin) về người dùng thông thường (user)."""
    user = database.tim_nguoi_dung_theo_email_hoac_id(args.dinh_danh)
    if not user:
        print(f"LỖI: Không tìm thấy tài khoản tương ứng với '{args.dinh_danh}'.")
        sys.exit(1)

    if user.get("role") == "user":
        print(f"Thông báo: Tài khoản ID {user['id']} ({user.get('email')}) đang ở vai trò 'user'.")
        return

    if not args.xac_nhan:
        print(f"Bạn đang chuẩn bị HẠ QUYỀN Admin về User cho:")
        print(f"  - ID:    {user['id']}")
        print(f"  - Email: {user.get('email')}")
        xac_nhan = input("Nhập 'YES' để xác nhận thay đổi: ")
        if xac_nhan.strip() != "YES":
            print("Đã hủy thao tác.")
            return

    user_moi = database.cap_nhat_vai_tro_nguoi_dung(user["id"], "user")
    database.ghi_audit_log(
        actor_user_id=None,
        action="demote_admin_cli",
        target_type="user",
        target_id=user["id"],
        details={"email": user.get("email"), "source": "admin_cli"}
    )
    log_thao_tac(f"ĐÃ HẠ QUYỀN VỀ USER: ID={user_moi['id']} Email={user_moi.get('email')}")
    print(f"Thành công: Tài khoản ID {user_moi['id']} ({user_moi.get('email')}) đã trở về vai trò USER.")


def lenh_reset_mfa(args):
    """Đặt lại/tắt MFA cho tài khoản Admin trong trường hợp khẩn cấp."""
    user = database.tim_nguoi_dung_theo_email_hoac_id(args.dinh_danh)
    if not user:
        print(f"LỖI: Không tìm thấy tài khoản tương ứng với '{args.dinh_danh}'.")
        sys.exit(1)

    if not args.xac_nhan:
        print(f"CẢNH BÁO: Đặt lại MFA cho tài khoản ID {user['id']} ({user.get('email')})?")
        xac_nhan = input("Nhập 'YES' để xác nhận: ")
        if xac_nhan.strip() != "YES":
            print("Đã hủy thao tác.")
            return

    database.tat_mfa_admin(user["id"])
    database.ghi_audit_log(
        actor_user_id=None,
        action="reset_mfa_cli",
        target_type="user",
        target_id=user["id"],
        details={"email": user.get("email"), "source": "admin_cli"}
    )
    log_thao_tac(f"ĐÃ RESET MFA: ID={user['id']} Email={user.get('email')}")
    print(f"Thành công: Đã tắt MFA cho tài khoản ID {user['id']}.")


def main():
    parser = argparse.ArgumentParser(
        description="Biển Báo AI - Quản trị tài khoản và phân quyền hệ thống (CLI)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="action", help="Lệnh quản trị")

    # 1. danh-sach
    subparsers.add_parser("danh-sach", help="Liệt kê toàn bộ tài khoản người dùng")

    # 2. kiem-tra
    p_kt = subparsers.add_parser("kiem-tra", help="Xem chi tiết một tài khoản bằng email hoặc ID")
    p_kt.add_argument("dinh_danh", help="Email hoặc ID người dùng")

    # 3. cap-quyen / promote
    for cmd in ("cap-quyen", "promote"):
        p_cq = subparsers.add_parser(cmd, help="Cấp quyền Admin cho tài khoản đã xác minh email")
        p_cq.add_argument("dinh_danh", help="Email hoặc ID người dùng cần cấp quyền")
        p_cq.add_argument("--cho-phep-nhieu-admin", action="store_true", help="Bỏ qua chính sách giới hạn 1 Admin chính")
        p_cq.add_argument("--xac-nhan", action="store_true", help="Bỏ qua nhắc xác nhận tương tác (dùng cho script/test)")

    # 4. ha-quyen / demote
    for cmd in ("ha-quyen", "demote"):
        p_hq = subparsers.add_parser(cmd, help="Hạ quyền Admin của một tài khoản về User")
        p_hq.add_argument("dinh_danh", help="Email hoặc ID người dùng cần hạ quyền")
        p_hq.add_argument("--xac-nhan", action="store_true", help="Bỏ qua nhắc xác nhận tương tác (dùng cho script/test)")

    # 5. reset-mfa
    p_rmfa = subparsers.add_parser("reset-mfa", help="Đặt lại/tắt MFA cho Admin khi gặp sự cố thiết bị")
    p_rmfa.add_argument("dinh_danh", help="Email hoặc ID người dùng")
    p_rmfa.add_argument("--xac-nhan", action="store_true", help="Bỏ qua nhắc xác nhận")

    args = parser.parse_args()
    if not args.action:
        parser.print_help()
        sys.exit(0)

    # Đảm bảo database đã được khởi tạo/migrate
    database.khoi_tao_db()

    actions = {
        "danh-sach": lenh_danh_sach,
        "kiem-tra": lenh_kiem_tra,
        "cap-quyen": lenh_cap_quyen,
        "promote": lenh_cap_quyen,
        "ha-quyen": lenh_ha_quyen,
        "demote": lenh_ha_quyen,
        "reset-mfa": lenh_reset_mfa,
    }

    actions[args.action](args)


if __name__ == "__main__":
    main()
