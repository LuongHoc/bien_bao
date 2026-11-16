# -*- coding: utf-8 -*-
"""
admin.py - Module Backend Quản trị và API Quản trị cho Biển Báo AI (Bước 18.4).

Chịu trách nhiệm:
1. Xác thực hai yếu tố MFA (TOTP - RFC 6238) cho Admin.
2. Thống kê tổng quan quản trị (100% dữ liệu thật từ SQLite).
3. Quản lý người dùng, phân quyền và khóa/mở khóa tài khoản an toàn.
4. Quản lý ngân hàng câu hỏi trắc nghiệm (lớp override metadata, không làm hỏng dữ liệu bài làm cũ).
5. Quản lý nội dung học tập thư viện biển báo (không đụng mô hình AI hay class YOLO/CNN).
6. Quản lý khảo sát người học (tách bạch khảo sát đầy đủ và khảo sát nhanh).
7. Nhật ký quản trị (admin_audit_logs) lưu lại mọi thao tác quan trọng.
"""

import json
import re
import secrets
import time
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, request, session

import database
import security
from security import yeu_cau_admin, yeu_cau_dang_nhap

_MFA_FAILURES = {}  # ip:user_id -> [timestamps]


def _kiem_tra_rate_limit(store, key, max_requests=5, window_seconds=900):
    now = time.monotonic()
    records = [t for t in store.get(key, []) if now - t < window_seconds]
    if len(records) >= max_requests:
        store[key] = records
        return False
    records.append(now)
    store[key] = records
    return True


def cau_hinh_admin(app, lay_danh_sach_bien_func=None, ma_ai_classes=None):
    """Đăng ký Blueprint quản trị cho Flask App."""
    bp = Blueprint("admin", __name__, url_prefix="/api/admin")

    @bp.after_request
    def no_cache(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        return response

    # =========================================================================
    # 1. XÁC THỰC HAI YẾU TỐ MFA (TOTP)
    # =========================================================================

    @bp.route("/mfa/setup", methods=["POST"])
    @yeu_cau_dang_nhap
    def mfa_setup():
        """Bắt đầu thiết lập TOTP MFA cho tài khoản Admin."""
        user = g.user
        if not security.kiem_tra_quyen_admin(user):
            return jsonify({"loi": "Chỉ quản trị viên mới được cấu hình MFA.", "code": "admin_required"}), 403

        # Sinh secret Base32 mới
        secret = security.sinh_totp_secret()
        # Sinh 5 mã dự phòng
        backup_codes = [secrets.token_hex(4).upper() for _ in range(5)]
        backup_hashes = [security.bam_token(c) for c in backup_codes]

        database.luu_mfa_admin(user["id"], secret, backup_hashes)
        otpauth_uri = security.tao_totp_uri(secret, user.get("email") or f"admin_{user['id']}")

        database.ghi_audit_log(
            actor_user_id=user["id"],
            action="setup_mfa_initiated",
            target_type="user",
            target_id=user["id"],
            details={"message": "Khởi tạo thiết lập MFA TOTP"},
            ip_address=request.remote_addr
        )

        return jsonify({
            "thanh_cong": True,
            "secret": secret,
            "otpauth_uri": otpauth_uri,
            "backup_codes": backup_codes,
            "thong_bao": "Đã tạo thông tin MFA. Vui lòng quét mã và nhập mã OTP 6 số để kích hoạt."
        }), 200

    @bp.route("/mfa/verify", methods=["POST"])
    @yeu_cau_dang_nhap
    def mfa_verify():
        """Xác thực mã OTP 6 số để kích hoạt hoặc xác nhận phiên Admin."""
        user = g.user
        if not security.kiem_tra_quyen_admin(user):
            return jsonify({"loi": "Chỉ quản trị viên mới cần xác thực MFA.", "code": "admin_required"}), 403

        ip = request.remote_addr or "127.0.0.1"
        rate_key = f"{ip}:{user['id']}"
        if not _kiem_tra_rate_limit(_MFA_FAILURES, rate_key, max_requests=5, window_seconds=900):
            return jsonify({
                "thanh_cong": False,
                "code": "too_many_mfa_attempts",
                "loi": "Đã thử sai mã OTP quá nhiều lần. Vui lòng thử lại sau 15 phút."
            }), 429

        data = request.get_json(silent=True) or {}
        code = str(data.get("code") or "").strip()

        mfa = database.lay_mfa_admin(user["id"])
        if not mfa or not mfa.get("secret_key"):
            return jsonify({"thanh_cong": False, "code": "mfa_not_setup", "loi": "Tài khoản chưa khởi tạo MFA."}), 400

        # Kiểm tra mã TOTP
        hop_le = security.xac_thuc_ma_totp(mfa["secret_key"], code)
        dung_backup = False

        if not hop_le and mfa.get("backup_codes_json"):
            # Kiểm tra mã dự phòng
            try:
                b_hashes = json.loads(mfa["backup_codes_json"])
                c_hash = security.bam_token(code.upper())
                if c_hash in b_hashes:
                    hop_le = True
                    dung_backup = True
                    b_hashes.remove(c_hash)
                    database.luu_mfa_admin(user["id"], mfa["secret_key"], b_hashes)
            except Exception:
                pass

        if not hop_le:
            database.ghi_audit_log(
                actor_user_id=user["id"],
                action="verify_mfa_failed",
                target_type="user",
                target_id=user["id"],
                details={"ip": ip},
                ip_address=ip
            )
            return jsonify({"thanh_cong": False, "code": "invalid_otp_code", "loi": "Mã xác thực OTP không chính xác hoặc đã hết hạn."}), 400

        # Xác thực thành công -> Xóa bộ đếm sai
        _MFA_FAILURES.pop(rate_key, None)
        database.kich_hoat_mfa_admin(user["id"])

        # Thiết lập session Admin
        session["admin_mfa_verified"] = True
        session["admin_mfa_time"] = time.time()
        session["admin_last_active"] = time.time()

        database.ghi_audit_log(
            actor_user_id=user["id"],
            action="verify_mfa_success",
            target_type="user",
            target_id=user["id"],
            details={"used_backup_code": dung_backup},
            ip_address=ip
        )

        return jsonify({
            "thanh_cong": True,
            "thong_bao": "Xác thực MFA thành công! Phiên quản trị đã sẵn sàng.",
            "used_backup_code": dung_backup
        }), 200

    @bp.route("/mfa/status", methods=["GET"])
    @yeu_cau_dang_nhap
    def mfa_status():
        """Kiểm tra trạng thái cấu hình MFA của tài khoản hiện tại."""
        user = g.user
        if not security.kiem_tra_quyen_admin(user):
            return jsonify({"loi": "Chỉ dành cho quản trị viên.", "code": "admin_required"}), 403

        mfa = database.lay_mfa_admin(user["id"])
        is_enabled = bool(mfa and mfa.get("is_enabled"))
        is_verified_in_session = bool(session.get("admin_mfa_verified"))

        return jsonify({
            "thanh_cong": True,
            "mfa_enabled": is_enabled,
            "mfa_verified_in_session": is_verified_in_session,
            "session_active": bool(session.get("admin_last_active"))
        }), 200

    # =========================================================================
    # 2. THỐNG KÊ TỔNG QUAN (ADMIN OVERVIEW)
    # =========================================================================

    @bp.route("/overview", methods=["GET"])
    @yeu_cau_admin
    def admin_overview():
        """Lấy số liệu thống kê tổng hợp từ dữ liệu thật trong SQLite."""
        range_days = request.args.get("range", "30")
        stats = database.thong_ke_tong_quan_admin(range_days=range_days)
        danh_sach_bien = lay_danh_sach_bien_func() if callable(lay_danh_sach_bien_func) else []
        stats["quizzes"]["total_bank_questions"] = len(danh_sach_bien) * 2
        return jsonify({"thanh_cong": True, "data": stats}), 200

    # =========================================================================
    # 3. QUẢN LÝ NGƯỜI DÙNG (USER MANAGEMENT)
    # =========================================================================

    @bp.route("/users", methods=["GET"])
    @yeu_cau_admin
    def danh_sach_nguoi_dung():
        """Liệt kê người dùng: phân trang, tìm kiếm, lọc status/role."""
        try:
            page = int(request.args.get("page", "1"))
            per_page = int(request.args.get("per_page", "20"))
        except ValueError:
            return jsonify({"loi": "Tham số phân trang không hợp lệ.", "code": "invalid_pagination"}), 400

        search = request.args.get("search")
        status = request.args.get("status")
        role = request.args.get("role")
        sort_by = request.args.get("sort_by", "id")
        sort_dir = request.args.get("sort_dir", "asc")

        result = database.danh_sach_nguoi_dung_admin(
            page=page,
            per_page=per_page,
            search=search,
            status=status,
            role=role,
            sort_by=sort_by,
            sort_dir=sort_dir
        )
        return jsonify({"thanh_cong": True, **result}), 200

    @bp.route("/users/<int:target_user_id>", methods=["GET"])
    @yeu_cau_admin
    def chi_tiet_nguoi_dung(target_user_id):
        """Xem thông tin chi tiết một người dùng."""
        u = database.chi_tiet_nguoi_dung_admin(target_user_id)
        if not u:
            return jsonify({"loi": f"Không tìm thấy người dùng ID {target_user_id}.", "code": "user_not_found"}), 404
        return jsonify({"thanh_cong": True, "user": u}), 200

    @bp.route("/users/<int:target_user_id>/status", methods=["PATCH"])
    @yeu_cau_admin
    def doi_trang_thai_nguoi_dung(target_user_id):
        """Khóa, tạm dừng hoặc kích hoạt lại tài khoản người dùng."""
        data = request.get_json(silent=True) or {}
        new_status = str(data.get("status") or "").strip().lower()
        reason = str(data.get("reason") or "").strip()

        if new_status not in ("active", "suspended", "locked"):
            return jsonify({"loi": f"Trạng thái '{new_status}' không hợp lệ.", "code": "invalid_status"}), 400

        if not reason or len(reason) < 3:
            return jsonify({"loi": "Vui lòng nhập lý do thay đổi trạng thái (tối thiểu 3 ký tự).", "code": "reason_required"}), 400

        try:
            updated_user = database.cap_nhat_trang_thai_nguoi_dung_admin(
                actor_user_id=g.user_id,
                target_user_id=target_user_id,
                status=new_status,
                reason=reason,
                ip_address=request.remote_addr
            )
            return jsonify({
                "thanh_cong": True,
                "thong_bao": f"Đã cập nhật trạng thái người dùng ID {target_user_id} thành '{new_status}'.",
                "user": updated_user
            }), 200
        except ValueError as e:
            return jsonify({"loi": str(e), "code": "status_update_rejected"}), 400

    # =========================================================================
    # 4. QUẢN LÝ NGÂN HÀNG CÂU HỎI TRẮC NGHIỆM
    # =========================================================================

    @bp.route("/quiz/questions", methods=["GET"])
    @yeu_cau_admin
    def danh_sach_cau_hoi():
        """Liệt kê danh sách câu hỏi trắc nghiệm (tổng hợp từ biển báo và override)."""
        danh_sach_bien = lay_danh_sach_bien_func() if callable(lay_danh_sach_bien_func) else []
        overrides = database.lay_toan_bo_quiz_override()

        search = (request.args.get("search") or "").strip().lower()
        kieu_filter = request.args.get("kieu")  # nhin-anh hoặc doc-ten
        nhom_filter = request.args.get("nhom")  # p, w, r, i, s

        all_questions = []
        for b in danh_sach_bien:
            ma = b.get("ma", "")
            ten = b.get("ten", "")
            nhom = b.get("nhom", "")
            anh = b.get("anh") or b.get("anh_url") or ""

            if nhom_filter:
                prefix = ma[0].lower() if not ma.startswith("DP") else "p"
                if prefix != nhom_filter.lower():
                    continue

            # Sinh 2 dạng câu hỏi chuẩn
            for kieu in ("nhin-anh", "doc-ten"):
                if kieu_filter and kieu_filter != kieu:
                    continue

                qid = f"{kieu}:{ma}"
                ov = overrides.get(qid, {})
                is_active = ov.get("is_active", 1)

                prompt = ov.get("custom_prompt") or (
                    "Biển báo này có ý nghĩa gì?" if kieu == "nhin-anh" else f'Biển nào có ý nghĩa “{ten}”?'
                )

                if search:
                    if search not in ma.lower() and search not in ten.lower() and search not in prompt.lower():
                        continue

                all_questions.append({
                    "question_id": qid,
                    "sign_code": ma,
                    "sign_name": ten,
                    "sign_group": nhom,
                    "sign_image": anh,
                    "kieu": kieu,
                    "prompt": prompt,
                    "is_active": is_active,
                    "is_customized": bool(ov),
                    "custom_explanation": ov.get("custom_explanation")
                })

        try:
            page = max(1, int(request.args.get("page", "1")))
            per_page = max(1, min(100, int(request.args.get("per_page", "20"))))
        except ValueError:
            page, per_page = 1, 20

        total = len(all_questions)
        offset = (page - 1) * per_page
        items = all_questions[offset:offset + per_page]

        return jsonify({
            "thanh_cong": True,
            "questions": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if total > 0 else 1
        }), 200

    @bp.route("/quiz/questions/<question_id>", methods=["GET"])
    @yeu_cau_admin
    def chi_tiet_cau_hoi(question_id):
        """Xem chi tiết một câu hỏi và thông tin override."""
        if not re.fullmatch(r"(nhin-anh|doc-ten):[^:\s]{1,40}", question_id):
            return jsonify({"loi": "Định dạng question_id không hợp lệ.", "code": "invalid_question_id"}), 400

        kieu, code = question_id.split(":", 1)
        danh_sach_bien = lay_danh_sach_bien_func() if callable(lay_danh_sach_bien_func) else []
        sign = next((b for b in danh_sach_bien if b.get("ma") == code), None)

        if not sign:
            return jsonify({"loi": f"Không tìm thấy biển báo có mã '{code}'.", "code": "sign_not_found"}), 404

        ov = database.lay_quiz_override(question_id) or {}
        return jsonify({
            "thanh_cong": True,
            "question_id": question_id,
            "sign": sign,
            "kieu": kieu,
            "is_active": ov.get("is_active", 1),
            "custom_prompt": ov.get("custom_prompt"),
            "custom_explanation": ov.get("custom_explanation"),
            "updated_at": ov.get("updated_at")
        }), 200

    @bp.route("/quiz/questions/<question_id>", methods=["PATCH"])
    @yeu_cau_admin
    def cap_nhat_cau_hoi(question_id):
        """Cập nhật tùy chỉnh nội dung hoặc ẩn/hiện câu hỏi."""
        if not re.fullmatch(r"(nhin-anh|doc-ten):[^:\s]{1,40}", question_id):
            return jsonify({"loi": "Định dạng question_id không hợp lệ.", "code": "invalid_question_id"}), 400

        kieu, code = question_id.split(":", 1)
        data = request.get_json(silent=True) or {}

        is_active = 1 if data.get("is_active", 1) in (1, True, "1") else 0
        custom_prompt = data.get("custom_prompt")
        custom_explanation = data.get("custom_explanation")

        if custom_prompt is not None:
            custom_prompt = str(custom_prompt).strip() or None
        if custom_explanation is not None:
            custom_explanation = str(custom_explanation).strip() or None

        database.cap_nhat_quiz_override(
            question_id=question_id,
            sign_code=code,
            is_active=is_active,
            custom_prompt=custom_prompt,
            custom_explanation=custom_explanation,
            updated_by=g.user_id
        )

        database.ghi_audit_log(
            actor_user_id=g.user_id,
            action="update_quiz_question",
            target_type="quiz_question",
            target_id=question_id,
            details={"is_active": is_active, "has_custom_prompt": bool(custom_prompt)},
            ip_address=request.remote_addr
        )

        return jsonify({
            "thanh_cong": True,
            "thong_bao": f"Đã cập nhật câu hỏi '{question_id}'.",
            "question_id": question_id,
            "is_active": is_active
        }), 200

    # =========================================================================
    # 5. QUẢN LÝ THƯ VIỆN BIỂN BÁO
    # =========================================================================

    @bp.route("/signs", methods=["GET"])
    @yeu_cau_admin
    def danh_sach_bien_admin():
        """Liệt kê biển báo phục vụ quản lý nội dung học tập."""
        danh_sach = lay_danh_sach_bien_func() if callable(lay_danh_sach_bien_func) else []
        meta_dict = database.lay_toan_bo_sign_metadata()

        search = (request.args.get("search") or "").strip().lower()
        nhom_filter = request.args.get("nhom")

        ai_set = set(ma_ai_classes or [])

        result_list = []
        for b in danh_sach:
            ma = b.get("ma", "")
            ten = b.get("ten", "")
            nhom = b.get("nhom", "")

            if nhom_filter and nhom_filter.lower() not in nhom.lower():
                continue

            if search:
                if search not in ma.lower() and search not in ten.lower():
                    continue

            meta = meta_dict.get(ma, {})
            result_list.append({
                "ma": ma,
                "ten": meta.get("custom_ten") or ten,
                "ten_goc": ten,
                "nhom": nhom,
                "y_nghia": meta.get("custom_y_nghia") or b.get("y_nghia", ""),
                "anh_url": b.get("anh") or b.get("anh_url"),
                "can_cu": b.get("can_cu"),
                "is_active": meta.get("is_active", 1),
                "is_ai_supported": ma in ai_set,
                "is_customized": bool(meta)
            })

        try:
            page = max(1, int(request.args.get("page", "1")))
            per_page = max(1, min(100, int(request.args.get("per_page", "20"))))
        except ValueError:
            page, per_page = 1, 20

        total = len(result_list)
        offset = (page - 1) * per_page
        items = result_list[offset:offset + per_page]

        return jsonify({
            "thanh_cong": True,
            "signs": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if total > 0 else 1
        }), 200

    @bp.route("/signs/<sign_code>", methods=["GET"])
    @yeu_cau_admin
    def chi_tiet_bien_admin(sign_code):
        """Chi tiết một biển báo và thông tin override metadata."""
        danh_sach = lay_danh_sach_bien_func() if callable(lay_danh_sach_bien_func) else []
        b = next((item for item in danh_sach if item.get("ma") == sign_code), None)
        if not b:
            return jsonify({"loi": f"Không tìm thấy biển báo có mã '{sign_code}'.", "code": "sign_not_found"}), 404

        meta = database.lay_sign_metadata(sign_code) or {}
        ai_set = set(ma_ai_classes or [])

        return jsonify({
            "thanh_cong": True,
            "sign": {
                **b,
                "is_ai_supported": sign_code in ai_set,
                "override_metadata": meta
            }
        }), 200

    @bp.route("/signs/<sign_code>", methods=["PATCH"])
    @yeu_cau_admin
    def cap_nhat_bien_admin(sign_code):
        """Cập nhật metadata thông tin học tập của biển báo (không đụng mô hình AI)."""
        danh_sach = lay_danh_sach_bien_func() if callable(lay_danh_sach_bien_func) else []
        b = next((item for item in danh_sach if item.get("ma") == sign_code), None)
        if not b:
            return jsonify({"loi": f"Không tìm thấy biển báo có mã '{sign_code}'.", "code": "sign_not_found"}), 404

        data = request.get_json(silent=True) or {}
        is_active = 1 if data.get("is_active", 1) in (1, True, "1") else 0
        custom_ten = data.get("custom_ten")
        custom_y_nghia = data.get("custom_y_nghia")
        custom_ghi_chu = data.get("custom_ghi_chu")

        if custom_ten is not None:
            custom_ten = str(custom_ten).strip() or None
        if custom_y_nghia is not None:
            custom_y_nghia = str(custom_y_nghia).strip() or None
        if custom_ghi_chu is not None:
            custom_ghi_chu = str(custom_ghi_chu).strip() or None

        database.cap_nhat_sign_metadata(
            sign_code=sign_code,
            is_active=is_active,
            custom_ten=custom_ten,
            custom_y_nghia=custom_y_nghia,
            custom_ghi_chu=custom_ghi_chu,
            updated_by=g.user_id
        )

        database.ghi_audit_log(
            actor_user_id=g.user_id,
            action="update_sign_metadata",
            target_type="sign",
            target_id=sign_code,
            details={"is_active": is_active, "custom_ten": custom_ten},
            ip_address=request.remote_addr
        )

        return jsonify({
            "thanh_cong": True,
            "thong_bao": f"Đã cập nhật thông tin hiển thị của biển '{sign_code}'.",
            "sign_code": sign_code,
            "is_active": is_active
        }), 200

    # =========================================================================
    # 6. QUẢN LÝ KHẢO SÁT NGƯỜI HỌC
    # =========================================================================

    @bp.route("/surveys/summary", methods=["GET"])
    @yeu_cau_admin
    def khao_sat_tong_hop():
        """Tổng hợp kết quả khảo sát đầy đủ và khảo sát nhanh (tách bạch rõ ràng)."""
        import survey_db
        full_summary = survey_db.tong_hop(version=1, limit=5, offset=0)

        # Lấy thêm phân tích khảo sát nhanh từ SQLite
        quick_analysis = {"total": 0, "distribution": {}, "tags": {}, "average_rating": 0.0}
        with database.closing(database.ket_noi()) as conn:
            has_table = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='quick_survey_responses'").fetchone()
            if has_table:
                total_q = conn.execute("SELECT COUNT(*) FROM quick_survey_responses").fetchone()[0]
                avg_q = conn.execute("SELECT AVG(rating) FROM quick_survey_responses").fetchone()[0] or 0.0
                dist_rows = conn.execute("SELECT rating, COUNT(*) as cnt FROM quick_survey_responses GROUP BY rating").fetchall()
                tag_rows = conn.execute("SELECT tags FROM quick_survey_responses WHERE tags IS NOT NULL").fetchall()

                tag_counts = {}
                for tr in tag_rows:
                    try:
                        ts = json.loads(tr["tags"])
                        for t in ts:
                            tag_counts[t] = tag_counts.get(t, 0) + 1
                    except Exception:
                        pass

                quick_analysis = {
                    "total": total_q,
                    "average_rating": round(float(avg_q), 2),
                    "distribution": {str(r["rating"]): r["cnt"] for r in dist_rows},
                    "tags": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])
                }

        return jsonify({
            "thanh_cong": True,
            "full_survey": full_summary,
            "quick_survey": quick_analysis
        }), 200

    @bp.route("/surveys/feedback", methods=["GET"])
    @yeu_cau_admin
    def danh_sach_gop_y():
        """Danh sách ý kiến đóng góp từ cả 2 nguồn khảo sát (phân trang, không lộ thông tin nhạy cảm)."""
        try:
            limit = max(1, min(100, int(request.args.get("limit", "20"))))
            offset = max(0, int(request.args.get("offset", "0")))
        except ValueError:
            limit, offset = 20, 0

        with database.closing(database.ket_noi()) as conn:
            # 1. Góp ý từ khảo sát đầy đủ
            full_sql = """
                SELECT 'full_survey' AS source, a.text_answer AS feedback, v.updated_at,
                       NULL AS rating, NULL AS tags
                FROM survey_responses v
                JOIN survey_answers a ON a.response_id = v.id
                JOIN survey_questions q ON q.id = a.question_id
                WHERE q.question_type = 'text' AND length(trim(a.text_answer)) > 0
            """

            # 2. Góp ý từ khảo sát nhanh
            has_quick = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='quick_survey_responses'").fetchone()
            if has_quick:
                quick_sql = """
                    SELECT 'quick_survey' AS source, feedback, updated_at, rating, tags
                    FROM quick_survey_responses
                    WHERE length(trim(feedback)) > 0
                """
                union_sql = f"({full_sql}) UNION ALL ({quick_sql})"
            else:
                union_sql = f"({full_sql})"

            total = conn.execute(f"SELECT COUNT(*) FROM ({union_sql})").fetchone()[0]
            rows = conn.execute(f"""
                SELECT source, feedback, updated_at, rating, tags
                FROM ({union_sql})
                ORDER BY julianday(updated_at) DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()

            result = []
            for r in rows:
                item = dict(r)
                if item["tags"]:
                    try:
                        item["tags"] = json.loads(item["tags"])
                    except Exception:
                        pass
                result.append(item)

            return jsonify({
                "thanh_cong": True,
                "feedbacks": result,
                "total": total,
                "limit": limit,
                "offset": offset
            }), 200

    # =========================================================================
    # 7. NHẬT KÝ QUẢN TRỊ (AUDIT LOGS)
    # =========================================================================

    @bp.route("/audit-logs", methods=["GET"])
    @yeu_cau_admin
    def audit_logs():
        """Liệt kê nhật ký hoạt động của quản trị viên."""
        try:
            limit = max(1, min(100, int(request.args.get("limit", "20"))))
            offset = max(0, int(request.args.get("offset", "0")))
        except ValueError:
            limit, offset = 20, 0

        action = request.args.get("action")
        target_type = request.args.get("target_type")

        result = database.danh_sach_audit_logs(limit=limit, offset=offset, action=action, target_type=target_type)
        return jsonify({"thanh_cong": True, **result}), 200

    app.register_blueprint(bp)
