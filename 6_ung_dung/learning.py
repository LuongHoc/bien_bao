"""API thống kê chỉ đọc, theo tài khoản trong Flask Session."""

import sqlite3
from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, g, jsonify, request, session

import database


# Cùng cách kyHieu/TEN_LOAI trong app.js: DP thuộc nhóm p, R.E thuộc r.
_NHOM_BIEN = {"p": "Biển cấm", "w": "Biển nguy hiểm", "r": "Biển hiệu lệnh",
              "i": "Biển chỉ dẫn", "s": "Biển phụ", "other": "Khác"}
_CHUA_DONG_BO = "Tiến độ đã học hiện lưu trong localStorage; chưa có chức năng đồng bộ tiến độ sang SQLite."


def _utc(value):
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _tien_do(user_id, bien):
    # Không suy ra đã học từ câu đúng hoặc sign_review_stats.
    theo_ma = {item["ma"]: item for item in bien}
    recorded = {row["sign_code"]: row["is_learned"] for row in database.tien_do_da_luu(user_id)}
    groups = {code: {"group_code": code, "group_name": name, "total_signs": 0,
                     "learned_signs": None, "learned_percent": None,
                     "recorded_progress_rows": 0, "recorded_learned_signs": 0}
              for code, name in _NHOM_BIEN.items()}
    for ma in theo_ma:
        code = "p" if ma.startswith("DP") else ma[0].lower()
        group = groups.get(code, groups["other"])
        group["total_signs"] += 1
        group["recorded_progress_rows"] += int(ma in recorded)
        group["recorded_learned_signs"] += int(recorded.get(ma) == 1)
    result_groups = [group for code, group in groups.items() if code != "other" or group["total_signs"]]
    return {"source": "sqlite", "sync_status": "not_synced", "sync_supported": False,
            "message": _CHUA_DONG_BO, "total_signs": len(theo_ma),
            "learned_signs": None, "learned_percent": None,
            "recorded_progress_rows": sum(group["recorded_progress_rows"] for group in result_groups),
            "recorded_learned_signs": sum(group["recorded_learned_signs"] for group in result_groups),
            "unmapped_progress_rows": sum(ma not in theo_ma for ma in recorded), "groups": result_groups}


def cau_hinh_thong_ke(app, lay_danh_sach_bien):
    bp = Blueprint("learning", __name__, url_prefix="/api/learning")

    @bp.before_request
    def yeu_cau_dang_nhap():
        user_id = session.get("user_id")
        if type(user_id) is not int or database.lay_nguoi_dung(user_id) is None:
            return jsonify({"loi": "Bạn cần đăng nhập Google để xem thống kê học tập."}), 401
        g.learning_user_id = user_id

    @bp.after_request
    def khong_cache(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    @bp.errorhandler(sqlite3.Error)
    def loi_doc_db(error):
        current_app.logger.exception("Khong doc duoc thong ke hoc tap SQLite")
        return jsonify({"loi": "Chưa đọc được thống kê học tập. Hãy thử lại sau."}), 500

    @bp.get("/overview")
    def tong_quan():
        data = database.thong_ke_tong_quan(g.learning_user_id)
        return jsonify({"source": "sqlite", **data, "learned_signs": None,
                        "progress_sync_status": "not_synced"})

    @bp.get("/trend")
    def tien_bo():
        period = request.args.get("period", "30d")
        if period not in ("7d", "30d", "all"):
            return jsonify({"loi": "period phải là 7d, 30d hoặc all."}), 400
        now = datetime.now(timezone.utc)
        start = None if period == "all" else _utc(now - timedelta(days=7 if period == "7d" else 30))
        end = None if period == "all" else _utc(now)
        attempts = database.thong_ke_tien_bo(g.learning_user_id, start, end)
        return jsonify({"source": "sqlite", "period": period, "timezone": "UTC",
                        "range_start": start, "range_end": end, "attempts": attempts})

    @bp.get("/mistakes")
    def loi_sai():
        return jsonify({"source": "sqlite.quiz_answers", **database.thong_ke_loi_sai(g.learning_user_id)})

    @bp.get("/progress")
    def tien_do():
        return jsonify(_tien_do(g.learning_user_id, lay_danh_sach_bien()))

    app.register_blueprint(bp)
