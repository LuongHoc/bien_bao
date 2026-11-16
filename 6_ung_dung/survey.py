"""Khảo sát trải nghiệm: một phiếu mỗi tài khoản, không suy luận kết quả học."""

import json
import os
import secrets
import sqlite3

from flask import Blueprint, current_app, g, jsonify, request, session
from werkzeug.exceptions import RequestEntityTooLarge

import database
import survey_db

SURVEY_VERSION = 1
MAX_FEEDBACK_LENGTH = 1000
MAX_REQUEST_BYTES = 32 * 1024
PURPOSE = "Phản hồi được thu thập để đánh giá trải nghiệm người học và cải thiện ứng dụng trong đồ án tốt nghiệp."
PRIVACY_NOTICE = ("Phiếu gắn với tài khoản Google của bạn, không phải khảo sát ẩn danh. "
                  "Chỉ quản trị viên được xem tổng hợp và góp ý; kết quả không kèm email tài khoản. "
                  "Bạn có thể cập nhật hoặc xóa phiếu của mình. Không nhập thông tin nhạy cảm vào góp ý.")
INTERPRETATION_NOTICE = "Điểm khảo sát phản ánh trải nghiệm tự đánh giá, không chứng minh người học đã cải thiện kiến thức."
LIKERT_SCALE = [{"value": value, "label": label} for value, label in enumerate(
    ("Rất không đồng ý", "Không đồng ý", "Bình thường", "Đồng ý", "Rất đồng ý"), 1)]


class LoiKhaoSat(ValueError):
    def __init__(self, message, status=400, code="invalid_survey"):
        super().__init__(message)
        self.status, self.code = status, code


def danh_sach_quan_tri(value):
    """Chỉ cấu hình backend tin cậy, mặc định rỗng. Sai cấu hình thì dừng nạp."""
    if isinstance(value, str):
        if not value.strip():
            return frozenset()
        parts = [part.strip() for part in value.split(",")]
        if any(not part.isascii() or not part.isdecimal() for part in parts):
            raise ValueError("SURVEY_ADMIN_USER_IDS phải là danh sách ID số nguyên dương, cách nhau bằng dấu phẩy.")
        value = [int(part) for part in parts]
    if not isinstance(value, (list, tuple, set, frozenset)) or any(
            type(item) is not int or not 0 < item <= 9223372036854775807 for item in value):
        raise ValueError("SURVEY_ADMIN_USER_IDS chỉ chấp nhận các ID tài khoản hợp lệ trên backend.")
    return frozenset(value)


def kiem_tra_cau_tra_loi(payload, questions):
    """Đọc lại câu hỏi trong transaction ghi, tránh đổi ngân hàng giữa kiểm tra và lưu."""
    if not isinstance(payload, dict) or set(payload) != {"survey_version", "answers"}:
        raise LoiKhaoSat("Phiếu phải chứa đúng survey_version và answers.")
    if type(payload["survey_version"]) is not int or payload["survey_version"] < 1:
        raise LoiKhaoSat("survey_version phải là số nguyên dương.")
    if payload["survey_version"] != SURVEY_VERSION:
        raise LoiKhaoSat("Phiên bản khảo sát đã thay đổi. Hãy tải lại danh sách câu hỏi.", 409, "survey_version_mismatch")
    if not questions or not any(question["is_required"] for question in questions):
        raise LoiKhaoSat("Hiện chưa có bộ câu hỏi khảo sát hợp lệ.", 409, "survey_unavailable")
    answers = payload["answers"]
    if not isinstance(answers, list) or len(answers) > len(questions):
        raise LoiKhaoSat("answers phải là danh sách câu trả lời, không vượt số câu đang hoạt động.")
    by_id = {question["id"]: question for question in questions}
    seen, normalized = set(), []
    for answer in answers:
        if not isinstance(answer, dict) or set(answer) != {"question_id", "value"}:
            raise LoiKhaoSat("Mỗi câu trả lời phải có đúng question_id và value.")
        question_id, value = answer["question_id"], answer["value"]
        if type(question_id) is not int or question_id not in by_id:
            raise LoiKhaoSat("ID câu hỏi không tồn tại hoặc không thuộc khảo sát đang hoạt động.")
        if question_id in seen:
            raise LoiKhaoSat("Không được gửi trùng ID câu hỏi.")
        seen.add(question_id)
        question = by_id[question_id]
        if question["question_type"] == "likert":
            if type(value) is not int or not 1 <= value <= 5:
                raise LoiKhaoSat("Điểm từng tiêu chí phải là số nguyên từ 1 đến 5.", code="invalid_rating")
        else:
            if not isinstance(value, str) or len(value) > MAX_FEEDBACK_LENGTH or "\0" in value:
                raise LoiKhaoSat("Góp ý phải là văn bản không quá 1000 ký tự và không có ký tự NUL.", code="invalid_feedback")
            try:
                value.encode("utf-8")
            except UnicodeEncodeError:
                raise LoiKhaoSat("Góp ý chứa ký tự Unicode không hợp lệ.", code="invalid_feedback") from None
            value = value.strip()
            if not value:
                if question["is_required"]:
                    raise LoiKhaoSat("Cần trả lời đủ các câu hỏi bắt buộc.", code="missing_answers")
                continue
        normalized.append({"question": question, "value": value})
    if any(question["is_required"] and question["id"] not in seen for question in questions):
        raise LoiKhaoSat("Cần trả lời đủ các câu hỏi bắt buộc.", code="missing_answers")
    return normalized


def cau_hinh_khao_sat(app):
    app.config["SURVEY_ADMIN_USER_IDS"] = danh_sach_quan_tri(
        app.config.get("SURVEY_ADMIN_USER_IDS", os.environ.get("SURVEY_ADMIN_USER_IDS", "")))
    with database.giao_dich() as conn:
        survey_db.khoi_tao_bang_khao_sat_nhanh(conn)
    bp = Blueprint("survey", __name__, url_prefix="/api/survey")

    @bp.errorhandler(LoiKhaoSat)
    def loi_du_lieu(error):
        return jsonify({"loi": str(error), "code": error.code}), error.status

    @bp.errorhandler(RequestEntityTooLarge)
    def qua_lon(error):
        return jsonify({"loi": "Phiếu khảo sát vượt dung lượng cho phép.", "code": "request_too_large"}), 413

    @bp.errorhandler(sqlite3.Error)
    def loi_db(error):
        current_app.logger.exception("Khong xu ly duoc khao sat SQLite")
        return jsonify({"loi": "Chưa xử lý được khảo sát. Hãy thử lại sau.", "code": "survey_storage_error"}), 500

    @bp.after_request
    def khong_cache(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @bp.before_request
    def bao_ve():
        if request.endpoint in ("survey.questions", "survey.quick_check") or request.method == "OPTIONS":
            return
        user_id = session.get("user_id")
        user = database.lay_nguoi_dung(user_id) if type(user_id) is int and 0 < user_id <= 9223372036854775807 else None
        if user is None:
            raise LoiKhaoSat("Bạn cần đăng nhập Google để sử dụng khảo sát.", 401, "authentication_required")
        g.survey_user_id = user_id
        is_admin = (user.get("role") == "admin" and user.get("status") == "active") or (user_id in current_app.config.get("SURVEY_ADMIN_USER_IDS", frozenset()))
        if request.endpoint == "survey.summary" and not is_admin:
            raise LoiKhaoSat("Bạn không có quyền xem tổng hợp khảo sát.", 403, "admin_required")
        if request.method in ("POST", "DELETE"):
            token, expected = request.headers.get("X-CSRF-Token", ""), session.get("csrf_token")
            if not isinstance(expected, str) or not expected or not secrets.compare_digest(token.encode(), expected.encode()):
                raise LoiKhaoSat("CSRF không hợp lệ. Hãy kiểm tra đăng nhập và thử lại.", 403, "invalid_csrf")

    @bp.get("/questions", endpoint="questions")
    def danh_sach_cau_hoi():
        with survey_db.doc_khao_sat() as conn:
            questions = survey_db.cau_hoi(conn, SURVEY_VERSION)
        return jsonify({"survey_version": SURVEY_VERSION, "purpose": PURPOSE, "privacy_notice": PRIVACY_NOTICE,
                        "interpretation_notice": INTERPRETATION_NOTICE, "likert_scale": LIKERT_SCALE,
                        "feedback_max_length": MAX_FEEDBACK_LENGTH, "questions": questions})

    @bp.get("/quick/check", endpoint="quick_check")
    def kiem_tra_khao_sat_nhanh():
        user_id = session.get("user_id")
        if type(user_id) is not int or database.lay_nguoi_dung(user_id) is None:
            return jsonify({"should_prompt": False, "da_dang_nhap": False, "reason": "not_logged_in"}), 200
        attempt_id = request.args.get("attempt_id")
        if attempt_id is not None:
            try:
                attempt_id = int(attempt_id)
            except ValueError:
                attempt_id = None
        with database.giao_dich() as conn:
            result = survey_db.kiem_tra_dieu_kien_khao_sat_nhanh(conn, user_id, attempt_id)
        return jsonify({"da_dang_nhap": True, **result}), 200

    @bp.post("/quick/dismiss")
    def bo_qua_khao_sat_nhanh():
        attempt_id = None
        if request.is_json:
            data = request.get_json(silent=True)
            if isinstance(data, dict):
                attempt_id = data.get("attempt_id")
                if attempt_id is not None and type(attempt_id) is not int:
                    attempt_id = None
        with database.giao_dich() as conn:
            prompt_count = survey_db.ghi_nhan_bo_qua_khao_sat_nhanh(conn, g.survey_user_id, attempt_id)
        return jsonify({"dismissed": True, "prompt_count": prompt_count}), 200

    @bp.post("/quick/submit")
    def nop_khao_sat_nhanh():
        if not request.is_json:
            raise LoiKhaoSat("Dữ liệu phải gửi dưới dạng application/json.", 415, "json_required")
        if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
            raise RequestEntityTooLarge()
        raw = request.stream.read(MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES:
            raise RequestEntityTooLarge()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            raise LoiKhaoSat("Nội dung JSON không hợp lệ.") from None
        if not isinstance(payload, dict):
            raise LoiKhaoSat("Dữ liệu khảo sát phải là đối tượng JSON.")
        rating = payload.get("rating")
        if type(rating) is not int or not 1 <= rating <= 5:
            raise LoiKhaoSat("Điểm đánh giá phải là số nguyên từ 1 đến 5.", code="invalid_rating")
        tags = payload.get("tags")
        if tags is not None:
            if not isinstance(tags, list) or len(tags) > 10 or any(not isinstance(t, str) or not 1 <= len(t) <= 100 for t in tags):
                raise LoiKhaoSat("Danh sách lựa chọn không hợp lệ.", code="invalid_tags")
        feedback = payload.get("feedback")
        if feedback is not None:
            if not isinstance(feedback, str) or len(feedback) > MAX_FEEDBACK_LENGTH or "\0" in feedback:
                raise LoiKhaoSat("Góp ý phải là văn bản không quá 1000 ký tự và không có ký tự NUL.", code="invalid_feedback")
            try:
                feedback.encode("utf-8")
            except UnicodeEncodeError:
                raise LoiKhaoSat("Góp ý chứa ký tự Unicode không hợp lệ.", code="invalid_feedback") from None
            feedback = feedback.strip()
            if not feedback:
                feedback = None
        attempt_id = payload.get("attempt_id")
        if attempt_id is not None and type(attempt_id) is not int:
            attempt_id = None
        with database.giao_dich() as conn:
            survey_db.ghi_khao_sat_nhanh(conn, g.survey_user_id, rating, tags, feedback, attempt_id)
        return jsonify({"saved": True, "thanh_cong": True}), 201

    @bp.get("/quick/me")
    def khao_sat_nhanh_cua_toi():
        with survey_db.doc_khao_sat() as conn:
            data = survey_db.lay_khao_sat_nhanh(conn, g.survey_user_id)
        return jsonify(data), 200

    @bp.get("/me")
    def phieu_cua_toi():
        with survey_db.doc_khao_sat() as conn:
            response = survey_db.phieu_cua_toi(conn, g.survey_user_id)
        return jsonify({"has_response": response is not None, "response": response})

    @bp.post("/submit")
    def gui_phieu():
        if not request.is_json:
            raise LoiKhaoSat("Phiếu phải gửi dưới dạng application/json.", 415, "json_required")
        if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
            raise RequestEntityTooLarge()
        raw = request.stream.read(MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES:
            raise RequestEntityTooLarge()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            raise LoiKhaoSat("Nội dung JSON không hợp lệ.") from None
        with database.giao_dich() as conn:
            questions = survey_db.cau_hoi(conn, SURVEY_VERSION)
            answers = kiem_tra_cau_tra_loi(payload, questions)
            response, created = survey_db.ghi_phieu(conn, g.survey_user_id, SURVEY_VERSION, answers)
        return jsonify({"saved": True, "created": created, "response": response}), 201 if created else 200

    @bp.delete("/me")
    def xoa_phieu_cua_toi():
        return jsonify({"deleted": survey_db.xoa_phieu(g.survey_user_id)})

    @bp.get("/summary", endpoint="summary")
    def tong_hop():
        try:
            limit = int(request.args.get("limit", "20"))
            offset = int(request.args.get("offset", "0"))
        except ValueError:
            raise LoiKhaoSat("Tham số phân trang không hợp lệ.") from None
        if not 1 <= limit <= 100 or not 0 <= offset <= 2147483647:
            raise LoiKhaoSat("limit phải từ 1 đến 100; offset phải là số nguyên không âm hợp lệ.")
        return jsonify({"interpretation_notice": INTERPRETATION_NOTICE,
                        **survey_db.tong_hop(SURVEY_VERSION, limit, offset)})

    app.register_blueprint(bp)
