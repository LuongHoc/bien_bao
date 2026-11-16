# -*- coding: utf-8 -*-
"""
migrate_v4.py - Script nâng cấp Schema v4 (Hệ thống tài khoản & RBAC) an toàn tuyệt đối.

Các bước thực hiện:
1. Sao lưu cơ sở dữ liệu thật vào instance/backups/ trước khi thực hiện.
2. Kiểm tra tính toàn vẹn dữ liệu trước khi migrate.
3. Thực thi migration Schema v4 bên trong một transaction SQLite an toàn.
4. Kiểm tra PRAGMA foreign_key_check và PRAGMA integrity_check sau khi migrate.
5. Xác minh số lượng bản ghi và quan hệ khóa ngoại không đổi.
"""

import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Thêm thư mục ứng dụng vào sys.path
GOC = os.path.dirname(os.path.abspath(__file__))
if GOC not in sys.path:
    sys.path.insert(0, GOC)

import database


def tao_ban_sao_luu(db_path: str) -> str:
    """Tạo bản sao lưu file SQLite với nhãn thời gian UTC."""
    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"Không tìm thấy file database tại: {db_path}")

    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"users.before_rbac_v4_{timestamp}.db")

    shutil.copy2(db_path, backup_path)
    return backup_path


def kiem_tra_database(db_path: str, giai_doan: str = "Trước"):
    """Kiểm tra toàn vẹn và khóa ngoại của database."""
    conn = database.ket_noi(db_path)
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchall()
        if not integrity or integrity[0][0] != "ok":
            raise RuntimeError(f"[{giai_doan}] Kiểm tra integrity_check thất bại: {integrity}")

        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise RuntimeError(f"[{giai_doan}] Phát hiện lỗi khóa ngoại foreign_key_check: {fk_errors}")

        version = conn.execute("PRAGMA user_version").fetchone()[0]
        users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

        # Kiểm tra các bảng khác nếu có
        attempts = 0
        answers = 0
        surveys = 0
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "quiz_attempts" in tables:
            attempts = conn.execute("SELECT COUNT(*) FROM quiz_attempts").fetchone()[0]
        if "quiz_answers" in tables:
            answers = conn.execute("SELECT COUNT(*) FROM quiz_answers").fetchone()[0]
        if "survey_responses" in tables:
            surveys = conn.execute("SELECT COUNT(*) FROM survey_responses").fetchone()[0]

        return {
            "version": version,
            "users_count": users_count,
            "attempts_count": attempts,
            "answers_count": answers,
            "surveys_count": surveys
        }
    finally:
        conn.close()


def thuc_hien_migration(db_path: str = None, tao_backup: bool = True):
    """Thực thi migration an toàn."""
    target_db = db_path or database.DUONG_DAN_DB
    print(f"=== BẮT ĐẦU MIGRATION SCHEMA V4 CHO: {target_db} ===")

    backup_file = None
    if os.path.isfile(target_db) and tao_backup:
        backup_file = tao_ban_sao_luu(target_db)
        print(f"[1/4] Đã tạo bản sao lưu an toàn tại: {backup_file}")
    else:
        print("[1/4] Bỏ qua tạo bản sao lưu (chế độ kiểm thử hoặc DB mới).")

    # Kiểm tra trước migration
    stats_truoc = {}
    if os.path.isfile(target_db):
        stats_truoc = kiem_tra_database(target_db, "Trước migration")
        print(f"[2/4] Kiểm tra trước migration: Schema v{stats_truoc['version']}, {stats_truoc['users_count']} users, {stats_truoc['attempts_count']} attempts, {stats_truoc['answers_count']} answers, {stats_truoc['surveys_count']} surveys.")

    # Chạy khoi_tao_db()
    print("[3/4] Đang thực thi nâng cấp schema trong transaction...")
    try:
        database.khoi_tao_db(target_db)
    except Exception as e:
        print(f"LỖI NGHIÊM TRỌNG TRONG KHI MIGRATION: {e}")
        if backup_file and os.path.isfile(backup_file):
            print(f"Để khôi phục, sao chép file backup đè lại:\n  Copy-Item '{backup_file}' '{target_db}' -Force")
        raise

    # Kiểm tra sau migration
    stats_sau = kiem_tra_database(target_db, "Sau migration")
    print(f"[4/4] Kiểm tra sau migration: Schema v{stats_sau['version']}, {stats_sau['users_count']} users, {stats_sau['attempts_count']} attempts, {stats_sau['answers_count']} answers, {stats_sau['surveys_count']} surveys.")

    # Xác minh bảo toàn dữ liệu
    if stats_truoc:
        assert stats_sau["users_count"] == stats_truoc["users_count"], "Số lượng users bị thay đổi!"
        assert stats_sau["attempts_count"] == stats_truoc["attempts_count"], "Số lượng attempts bị thay đổi!"
        assert stats_sau["answers_count"] == stats_truoc["answers_count"], "Số lượng answers bị thay đổi!"
        assert stats_sau["surveys_count"] == stats_truoc["surveys_count"], "Số lượng surveys bị thay đổi!"

    # Kiểm tra các bảng mới
    conn = database.ket_noi(target_db)
    try:
        identities_count = conn.execute("SELECT COUNT(*) FROM auth_identities").fetchone()[0]
        print(f"  + Số định danh đăng nhập trong auth_identities: {identities_count}")
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        print(f"  + Các cột hiện tại của bảng users: {', '.join(columns)}")
    finally:
        conn.close()

    print(">>> MIGRATION SCHEMA V4 THÀNH CÔNG VÀ AN TOÀN 100%! <<<\n")
    return backup_file


if __name__ == "__main__":
    db_arg = sys.argv[1] if len(sys.argv) > 1 else None
    thuc_hien_migration(db_arg)
