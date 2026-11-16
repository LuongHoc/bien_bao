"""Lưu/đọc khảo sát độc lập với kết quả học; mọi câu SQL dùng tham số."""

import json
from contextlib import closing, contextmanager

import database


@contextmanager
def doc_khao_sat():
    with closing(database.ket_noi()) as conn:
        conn.execute("PRAGMA query_only = ON")
        with conn:
            conn.execute("BEGIN")
            yield conn


def cau_hoi(conn, version):
    questions = [dict(row) for row in conn.execute("""
        SELECT id, survey_version, code, criterion, question_text, question_type,
               is_required, display_order
        FROM survey_questions WHERE survey_version = ? AND is_active = 1
        ORDER BY display_order, id
    """, (version,))]
    for question in questions:
        question["is_required"] = bool(question["is_required"])
    return questions


def phieu_cua_toi(conn, user_id):
    row = conn.execute("""
        SELECT id, survey_version, submitted_at, updated_at
        FROM survey_responses WHERE user_id = ?
    """, (user_id,)).fetchone()
    if row is None:
        return None
    response = dict(row)
    answers = []
    for item in conn.execute("""
        SELECT question_id, question_type, rating, text_answer, question_snapshot
        FROM survey_answers WHERE response_id = ? ORDER BY question_id
    """, (row["id"],)):
        answer = dict(item)
        answer["value"] = answer["rating"] if answer["question_type"] == "likert" else answer["text_answer"]
        del answer["rating"], answer["text_answer"]
        answer["question_snapshot"] = json.loads(answer["question_snapshot"])
        answers.append(answer)
    response["answers"] = sorted(answers, key=lambda item: item["question_snapshot"]["display_order"])
    return response


def ghi_phieu(conn, user_id, version, answers):
    """Bên gọi giữ BEGIN IMMEDIATE từ lúc đọc câu hỏi, kiểm tra đến ghi/đọc lại."""
    old = conn.execute("SELECT id FROM survey_responses WHERE user_id = ?", (user_id,)).fetchone()
    if old is None:
        response_id = conn.execute("""
            INSERT INTO survey_responses (user_id, survey_version) VALUES (?, ?)
        """, (user_id, version)).lastrowid
    else:
        response_id = old["id"]
        # Xóa đáp án trước khi đổi version để không vi phạm FK ghép.
        conn.execute("DELETE FROM survey_answers WHERE response_id = ?", (response_id,))
        conn.execute("""
            UPDATE survey_responses SET survey_version = ?,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ?
        """, (version, response_id))
    for answer in answers:
        question = answer["question"]
        is_rating = question["question_type"] == "likert"
        conn.execute("""
            INSERT INTO survey_answers (
                response_id, question_id, survey_version, question_type, rating, text_answer, question_snapshot
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (response_id, question["id"], version, question["question_type"],
              answer["value"] if is_rating else None, None if is_rating else answer["value"],
              json.dumps(question, ensure_ascii=False)))
    return phieu_cua_toi(conn, user_id), old is None


def xoa_phieu(user_id):
    with database.giao_dich() as conn:
        return conn.execute("DELETE FROM survey_responses WHERE user_id = ?", (user_id,)).rowcount > 0


# Loại phiếu thiếu câu bắt buộc, kể cả khi dữ liệu được nhập ngoài API.
# Không JOIN tài khoản, bài tập, learning_progress hoặc sign_review_stats.
_PHIEU_HOP_LE = """
    WITH valid AS (
        SELECT r.id, r.updated_at FROM survey_responses r
        WHERE r.survey_version = ?
          AND EXISTS (SELECT 1 FROM survey_questions q WHERE q.survey_version = r.survey_version
                      AND q.is_active = 1 AND q.is_required = 1)
          AND NOT EXISTS (
            SELECT 1 FROM survey_questions q
            WHERE q.survey_version = r.survey_version AND q.is_active = 1 AND q.is_required = 1
              AND NOT EXISTS (
                SELECT 1 FROM survey_answers a WHERE a.response_id = r.id AND a.question_id = q.id
                  AND ((q.question_type = 'likert' AND a.rating BETWEEN 1 AND 5)
                       OR (q.question_type = 'text' AND length(trim(a.text_answer)) > 0))
              )
          )
    )
"""


def tong_hop(version, limit, offset):
    with doc_khao_sat() as conn:
        total = conn.execute("SELECT COUNT(*) FROM survey_responses WHERE survey_version = ?", (version,)).fetchone()[0]
        valid = conn.execute(_PHIEU_HOP_LE + "SELECT COUNT(*) FROM valid", (version,)).fetchone()[0]
        rows = conn.execute(_PHIEU_HOP_LE + """
            SELECT q.id AS question_id, q.code, q.criterion, q.question_text,
                   COUNT(a.rating) AS response_count, AVG(a.rating) AS average_rating,
                   SUM(a.rating = 1) AS n1, SUM(a.rating = 2) AS n2, SUM(a.rating = 3) AS n3,
                   SUM(a.rating = 4) AS n4, SUM(a.rating = 5) AS n5
            FROM survey_questions q LEFT JOIN survey_answers a
              ON a.question_id = q.id AND a.response_id IN (SELECT id FROM valid)
            WHERE q.survey_version = ? AND q.is_active = 1 AND q.question_type = 'likert'
            GROUP BY q.id ORDER BY q.display_order, q.id
        """, (version, version)).fetchall()
        criteria = []
        for row in rows:
            item = dict(row)
            item["distribution"] = {str(value): item.pop("n" + str(value)) or 0 for value in range(1, 6)}
            criteria.append(item)
        feedback_sql = _PHIEU_HOP_LE + """
            SELECT a.text_answer AS text, v.updated_at
            FROM valid v JOIN survey_answers a ON a.response_id = v.id
            JOIN survey_questions q ON q.id = a.question_id
            WHERE q.is_active = 1 AND q.question_type = 'text'
              AND length(trim(a.text_answer)) > 0
        """
        comments_total = conn.execute("SELECT COUNT(*) FROM (" + feedback_sql + ")", (version,)).fetchone()[0]
        comments = [dict(row) for row in conn.execute(feedback_sql + """
            ORDER BY julianday(v.updated_at) DESC, v.id DESC LIMIT ? OFFSET ?
        """, (version, limit, offset))]
        return {"survey_version": version, "total_responses": total, "valid_responses": valid,
                "excluded_responses": total - valid, "criteria": criteria,
                "comments": {"items": comments, "total": comments_total, "limit": limit, "offset": offset}}


def khoi_tao_bang_khao_sat_nhanh(conn):
    """Khởi tạo bảng trạng thái lời mời và phản hồi khảo sát nhanh (idempotent)."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS survey_prompt_state (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            prompt_count INTEGER NOT NULL DEFAULT 0
                CHECK (typeof(prompt_count) = 'integer' AND prompt_count >= 0),
            last_prompt_at TEXT
                CHECK (last_prompt_at IS NULL OR julianday(last_prompt_at) IS NOT NULL),
            last_attempt_id INTEGER REFERENCES quiz_attempts(id) ON DELETE SET NULL,
            completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
            dismissed INTEGER NOT NULL DEFAULT 0 CHECK (dismissed IN (0, 1)),
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                CHECK (julianday(created_at) IS NOT NULL),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                CHECK (julianday(updated_at) IS NOT NULL)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quick_survey_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL
                CHECK (typeof(rating) = 'integer' AND rating BETWEEN 1 AND 5),
            tags TEXT CHECK (tags IS NULL OR json_valid(tags)),
            feedback TEXT CHECK (
                feedback IS NULL OR (
                    typeof(feedback) = 'text' AND length(feedback) <= 1000
                    AND instr(feedback, char(0)) = 0
                )
            ),
            attempt_id INTEGER REFERENCES quiz_attempts(id) ON DELETE SET NULL,
            submitted_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                CHECK (julianday(submitted_at) IS NOT NULL),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                CHECK (julianday(updated_at) IS NOT NULL)
        )
    """)


def kiem_tra_dieu_kien_khao_sat_nhanh(conn, user_id, attempt_id=None):
    """Xác định tài khoản có đủ điều kiện nhận lời mời khảo sát nhanh hay không."""
    khoi_tao_bang_khao_sat_nhanh(conn)

    # 1. Đã hoàn thành khảo sát đầy đủ 6 câu ở trang Giới thiệu
    has_full = conn.execute("SELECT 1 FROM survey_responses WHERE user_id = ?", (user_id,)).fetchone()
    if has_full:
        return {"should_prompt": False, "prompt_step": 0, "reason": "has_full_survey"}

    # 2. Đã từng gửi khảo sát nhanh
    has_quick = conn.execute("SELECT 1 FROM quick_survey_responses WHERE user_id = ?", (user_id,)).fetchone()
    if has_quick:
        return {"should_prompt": False, "prompt_step": 0, "reason": "already_completed"}

    # 3. Trạng thái lời mời
    prompt_state = conn.execute("SELECT * FROM survey_prompt_state WHERE user_id = ?", (user_id,)).fetchone()
    if prompt_state:
        if prompt_state["completed"] == 1:
            return {"should_prompt": False, "prompt_step": 0, "reason": "already_completed"}
        if prompt_state["dismissed"] == 1 or prompt_state["prompt_count"] >= 2:
            return {"should_prompt": False, "prompt_step": 0, "reason": "max_prompts_reached"}

    # 4. Đếm số bài tập hợp lệ đã lưu trong quiz_attempts
    attempt_count = conn.execute(
        "SELECT COUNT(*) FROM quiz_attempts WHERE user_id = ?", (user_id,)
    ).fetchone()[0]

    prompt_count = prompt_state["prompt_count"] if prompt_state else 0

    # Lời mời lần 1: Hoàn thành bài đầu tiên (attempt_count == 1) và chưa từng được mời (prompt_count == 0)
    if attempt_count == 1 and prompt_count == 0:
        return {
            "should_prompt": True,
            "prompt_step": 1,
            "attempt_count": 1,
            "reason": "first_quiz"
        }

    # Lời mời lần 2 (nhắc lại cuối cùng): Hoàn thành bài thứ 3 (attempt_count == 3) và đã bỏ qua lần đầu (prompt_count == 1)
    if attempt_count == 3 and prompt_count == 1:
        return {
            "should_prompt": True,
            "prompt_step": 2,
            "attempt_count": 3,
            "reason": "third_quiz"
        }

    return {
        "should_prompt": False,
        "prompt_step": 0,
        "attempt_count": attempt_count,
        "reason": "not_eligible"
    }


def ghi_nhan_bo_qua_khao_sat_nhanh(conn, user_id, attempt_id=None):
    """Ghi nhận người học chọn 'Để sau' hoặc đóng hộp thoại."""
    khoi_tao_bang_khao_sat_nhanh(conn)
    old = conn.execute("SELECT * FROM survey_prompt_state WHERE user_id = ?", (user_id,)).fetchone()
    now = conn.execute("SELECT strftime('%Y-%m-%dT%H:%M:%fZ', 'now')").fetchone()[0]

    if old is None:
        new_count = 1
        conn.execute("""
            INSERT INTO survey_prompt_state (
                user_id, prompt_count, last_prompt_at, last_attempt_id, completed, dismissed, created_at, updated_at
            ) VALUES (?, 1, ?, ?, 0, 0, ?, ?)
        """, (user_id, now, attempt_id, now, now))
    else:
        new_count = old["prompt_count"] + 1
        dismissed = 1 if new_count >= 2 else old["dismissed"]
        conn.execute("""
            UPDATE survey_prompt_state
            SET prompt_count = ?,
                last_prompt_at = ?,
                last_attempt_id = coalesce(?, last_attempt_id),
                dismissed = ?,
                updated_at = ?
            WHERE user_id = ?
        """, (new_count, now, attempt_id, dismissed, now, user_id))

    return new_count


def ghi_khao_sat_nhanh(conn, user_id, rating, tags, feedback, attempt_id=None):
    """Lưu phản hồi khảo sát nhanh và đánh dấu hoàn thành trong survey_prompt_state."""
    khoi_tao_bang_khao_sat_nhanh(conn)
    tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
    now = conn.execute("SELECT strftime('%Y-%m-%dT%H:%M:%fZ', 'now')").fetchone()[0]

    conn.execute("""
        INSERT INTO quick_survey_responses (
            user_id, rating, tags, feedback, attempt_id, submitted_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            rating = excluded.rating,
            tags = excluded.tags,
            feedback = excluded.feedback,
            attempt_id = coalesce(excluded.attempt_id, quick_survey_responses.attempt_id),
            updated_at = excluded.updated_at
    """, (user_id, rating, tags_json, feedback, attempt_id, now, now))

    conn.execute("""
        INSERT INTO survey_prompt_state (
            user_id, prompt_count, completed, last_prompt_at, last_attempt_id, created_at, updated_at
        ) VALUES (?, 1, 1, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            completed = 1,
            last_attempt_id = coalesce(excluded.last_attempt_id, survey_prompt_state.last_attempt_id),
            updated_at = excluded.updated_at
    """, (user_id, now, attempt_id, now, now))

    return True


def lay_khao_sat_nhanh(conn, user_id):
    """Đọc phản hồi khảo sát nhanh và trạng thái prompt của tài khoản."""
    khoi_tao_bang_khao_sat_nhanh(conn)
    resp = conn.execute("SELECT * FROM quick_survey_responses WHERE user_id = ?", (user_id,)).fetchone()
    state = conn.execute("SELECT * FROM survey_prompt_state WHERE user_id = ?", (user_id,)).fetchone()

    response_data = None
    if resp:
        response_data = {
            "id": resp["id"],
            "rating": resp["rating"],
            "tags": json.loads(resp["tags"]) if resp["tags"] else [],
            "feedback": resp["feedback"],
            "attempt_id": resp["attempt_id"],
            "submitted_at": resp["submitted_at"],
            "updated_at": resp["updated_at"]
        }

    state_data = None
    if state:
        state_data = {
            "prompt_count": state["prompt_count"],
            "last_prompt_at": state["last_prompt_at"],
            "last_attempt_id": state["last_attempt_id"],
            "completed": bool(state["completed"]),
            "dismissed": bool(state["dismissed"])
        }

    return {
        "has_response": response_data is not None,
        "response": response_data,
        "prompt_state": state_data
    }

