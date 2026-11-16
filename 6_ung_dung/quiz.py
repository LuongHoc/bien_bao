"""API bài tập: kiểm chứng theo cùng danh sách biển mà /api/bien cung cấp."""

import hashlib
import json
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from uuid import UUID

from flask import Blueprint, current_app, jsonify, request, session

import database


class LoiBaiTap(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def phien_ban_ngan_hang(bien):
    raw = json.dumps(bien, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def du_lieu_nop(payload):
    """Chỉ nhận thông tin lần làm thực tế; bỏ qua điểm/đáp án chuẩn giả mạo."""
    if not isinstance(payload, dict):
        raise LoiBaiTap("Bài nộp phải là đối tượng JSON.")
    required = ("submission_id", "quiz_type", "quiz_title", "bank_version",
                "started_at", "submitted_at", "questions")
    if any(key not in payload for key in required):
        raise LoiBaiTap("Bài nộp thiếu thông tin bắt buộc.")
    data = {key: payload[key] for key in required}
    try:
        if str(UUID(data["submission_id"])) != data["submission_id"]:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise LoiBaiTap("Mã lần nộp không hợp lệ.") from None
    if data["quiz_type"] not in ("nhom", "hang", "tong-hop", "on-sai", "bien-don"):
        raise LoiBaiTap("Loại bài tập không được hỗ trợ.")
    if (not isinstance(data["quiz_title"], str) or not 1 <= len(data["quiz_title"]) <= 200
            or not data["quiz_title"].strip()):
        raise LoiBaiTap("Tên bài tập không hợp lệ.")
    try:
        data["quiz_title"].encode("utf-8")
    except UnicodeEncodeError:
        raise LoiBaiTap("Tên bài tập chứa ký tự Unicode không hợp lệ.") from None
    if not isinstance(data["bank_version"], str) or not re.fullmatch(r"[0-9a-f]{64}", data["bank_version"]):
        raise LoiBaiTap("Phiên bản dữ liệu biển báo không hợp lệ.")
    for field in ("started_at", "submitted_at"):
        if type(data[field]) is not int:
            raise LoiBaiTap("Thời điểm làm bài phải là số nguyên mili giây Unix.")
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    if not 946684800000 <= data["started_at"] <= data["submitted_at"] <= now_ms + 300000:
        raise LoiBaiTap("Thời điểm bắt đầu hoặc nộp bài không hợp lệ.")
    questions = data["questions"]
    if not isinstance(questions, list) or not 1 <= len(questions) <= 100:
        raise LoiBaiTap("Bài làm phải có từ 1 đến 100 câu hỏi.")
    normalized, seen = [], set()
    for question in questions:
        fields = ("question_id", "option_codes", "selected_answer", "marked_for_review")
        if not isinstance(question, dict) or any(key not in question for key in fields):
            raise LoiBaiTap("Thông tin câu hỏi không đầy đủ.")
        item = {key: question[key] for key in fields}
        qid = item["question_id"]
        if not isinstance(qid, str) or not re.fullmatch(r"(nhin-anh|doc-ten):[^:\s]{1,40}", qid):
            raise LoiBaiTap("Mã hoặc dạng câu hỏi không hợp lệ.")
        if qid.split(":", 1)[1] in seen:
            raise LoiBaiTap("Một biển bị lặp lại trong cùng bài làm.")
        seen.add(qid.split(":", 1)[1])
        options = item["option_codes"]
        if (not isinstance(options, list) or not 1 <= len(options) <= 4
                or any(not isinstance(code, str) or not 1 <= len(code) <= 40 for code in options)
                or len(set(options)) != len(options)):
            raise LoiBaiTap("Danh sách lựa chọn không hợp lệ.")
        selected = item["selected_answer"]
        if selected is not None and (type(selected) is not int or not 0 <= selected < len(options)):
            raise LoiBaiTap("Đáp án đã chọn không hợp lệ.")
        if type(item["marked_for_review"]) is not bool:
            raise LoiBaiTap("Trạng thái đánh dấu phải là true hoặc false.")
        normalized.append(item)
    data["questions"] = normalized
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True,
                                       separators=(",", ":")).encode("utf-8")).hexdigest()
    return data, digest


def cham_bai(data, bien):
    if data["bank_version"] != phien_ban_ngan_hang(bien):
        raise LoiBaiTap("Dữ liệu biển báo đã thay đổi. Bài này chưa thể lưu; hãy tải lại dữ liệu để làm bài mới.", 409)
    theo_ma = {sign["ma"]: sign for sign in bien}
    answers = []
    for order, item in enumerate(data["questions"], 1):
        kind, code = item["question_id"].split(":", 1)
        sign = theo_ma.get(code)
        options = [theo_ma.get(value) for value in item["option_codes"]]
        # Luyện từ trang chi tiết/ôn sai có thể dùng biển chưa hopLe; giống
        # frontend, vẫn phải có ảnh và là mã biển đã biết trên server.
        if sign is None or not sign.get("anh") or any(value is None or not value.get("anh") for value in options):
            raise LoiBaiTap("Câu hỏi chứa mã biển không tồn tại hoặc chưa có ảnh.")
        if code not in item["option_codes"] or len({value["ten"] for value in options}) != len(options):
            raise LoiBaiTap("Các lựa chọn không chứa đáp án chuẩn hoặc bị trùng nội dung.")
        correct = item["option_codes"].index(code)
        selected = item["selected_answer"]
        status = "skipped" if selected is None else "correct" if selected == correct else "incorrect"
        prompt = "Biển báo này có ý nghĩa gì?" if kind == "nhin-anh" else f'Biển nào có ý nghĩa “{sign["ten"]}”?'
        answers.append({"question_order": order, "question_id": item["question_id"], "sign_code": code,
                        "question_snapshot": {"kieu": kind, "noi_dung": prompt, "dap_an": sign},
                        "options_snapshot": options, "selected_answer": selected, "correct_answer": correct,
                        "status": status, "marked_for_review": item["marked_for_review"]})
    correct_count = sum(answer["status"] == "correct" for answer in answers)
    skipped_count = sum(answer["status"] == "skipped" for answer in answers)
    def utc(ms):
        return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return {"quiz_type": data["quiz_type"], "quiz_title": data["quiz_title"], "answers": answers,
            "correct_count": correct_count, "skipped_count": skipped_count,
            "incorrect_count": len(answers) - correct_count - skipped_count,
            "score": 100 * correct_count / len(answers), "started_at": utc(data["started_at"]),
            "finished_at": utc(data["submitted_at"]),
            "duration_seconds": (data["submitted_at"] - data["started_at"] + 500) // 1000}


def cau_hinh_bai_tap(app, lay_danh_sach_bien):
    bp = Blueprint("quiz", __name__, url_prefix="/api/quiz")

    @bp.errorhandler(LoiBaiTap)
    def loi_du_lieu(error):
        return jsonify({"loi": str(error)}), error.status

    @bp.after_request
    def khong_cache(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    def nguoi_dung():
        user_id = session.get("user_id")
        if type(user_id) is not int or database.lay_nguoi_dung(user_id) is None:
            raise LoiBaiTap("Bạn cần đăng nhập Google để lưu hoặc xem bài làm.", 401)
        return user_id

    @bp.post("/submit")
    def nop_bai():
        user_id = nguoi_dung()
        token, expected = request.headers.get("X-CSRF-Token", ""), session.get("csrf_token")
        if not isinstance(expected, str) or not expected or not secrets.compare_digest(token.encode(), expected.encode()):
            raise LoiBaiTap("Phiên đăng nhập hoặc CSRF không hợp lệ. Hãy kiểm tra đăng nhập rồi thử lại.", 403)
        if request.content_length is not None and request.content_length > 256 * 1024:
            raise LoiBaiTap("Bài nộp vượt quá dung lượng cho phép.", 413)
        data, digest = du_lieu_nop(request.get_json(silent=True))
        try:
            old = database.tim_bai_nop(user_id, data["submission_id"])
            if old:
                if old["request_hash"] != digest:
                    raise database.MaNopDaDuocSuDung()
                attempt_id, created = old["id"], False
            else:
                bai = cham_bai(data, lay_danh_sach_bien())
                attempt_id, created = database.luu_bai_lam(user_id, data["submission_id"], digest, bai)
            result = database.chi_tiet_bai_lam(user_id, attempt_id)
        except database.MaNopDaDuocSuDung:
            raise LoiBaiTap("Mã lần nộp đã được dùng với nội dung khác.", 409) from None
        except sqlite3.Error:
            current_app.logger.exception("Khong luu duoc bai tap SQLite")
            raise LoiBaiTap("Chưa lưu được kết quả. Bạn có thể thử lưu lại cùng bài nộp.", 500) from None
        return jsonify({"da_luu": True, "lap_lai": not created, **result}), 201 if created else 200

    @bp.get("/history")
    def lich_su():
        user_id = nguoi_dung()
        try:
            limit = int(request.args.get("limit", "20"))
            offset = int(request.args.get("offset", "0"))
        except ValueError:
            raise LoiBaiTap("Tham số phân trang không hợp lệ.") from None
        if not 1 <= limit <= 100 or offset < 0 or offset > 2147483647:
            raise LoiBaiTap("limit phải từ 1 đến 100; offset phải là số nguyên không âm hợp lệ.")
        return jsonify(database.lich_su_bai_lam(user_id, limit, offset))

    @bp.get("/history/<int:attempt_id>")
    def chi_tiet(attempt_id):
        user_id = nguoi_dung()
        if attempt_id > 9223372036854775807:
            raise LoiBaiTap("Không tìm thấy bài làm.", 404)
        result = database.chi_tiet_bai_lam(user_id, attempt_id)
        if result is None:
            raise LoiBaiTap("Không tìm thấy bài làm.", 404)
        return jsonify(result)

    app.register_blueprint(bp)
