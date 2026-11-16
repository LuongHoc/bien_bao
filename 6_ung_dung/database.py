
import os
import sqlite3
import json
from contextlib import closing, contextmanager

# Đường dẫn thư mục ứng dụng
GOC = os.path.dirname(os.path.abspath(__file__))

# Thư mục lưu cơ sở dữ liệu
THU_MUC_DB = os.path.join(GOC, "instance")

# Đường dẫn file SQLite
DUONG_DAN_DB = os.path.join(THU_MUC_DB, "users.db")

PHIEN_BAN_SCHEMA = 8

# Migration chỉ bổ sung bảng và cột; không xóa hoặc tạo lại bảng users đã tồn tại.
# Mỗi phần tử là một câu SQL, thực thi bằng execute trong cùng transaction.
_MIGRATIONS = {
    1: (
        """
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            quiz_type TEXT NOT NULL CHECK (length(trim(quiz_type)) > 0),
            quiz_title TEXT NOT NULL CHECK (length(trim(quiz_title)) > 0),
            question_count INTEGER NOT NULL
                CHECK (typeof(question_count) = 'integer' AND question_count > 0),
            correct_count INTEGER NOT NULL DEFAULT 0
                CHECK (typeof(correct_count) = 'integer' AND correct_count >= 0),
            incorrect_count INTEGER NOT NULL DEFAULT 0
                CHECK (typeof(incorrect_count) = 'integer' AND incorrect_count >= 0),
            skipped_count INTEGER NOT NULL DEFAULT 0
                CHECK (typeof(skipped_count) = 'integer' AND skipped_count >= 0),
            score REAL NOT NULL
                CHECK (typeof(score) IN ('integer', 'real') AND score BETWEEN 0 AND 100),
            started_at TEXT NOT NULL CHECK (julianday(started_at) IS NOT NULL),
            finished_at TEXT NOT NULL CHECK (julianday(finished_at) IS NOT NULL),
            duration_seconds INTEGER NOT NULL
                CHECK (typeof(duration_seconds) = 'integer' AND duration_seconds >= 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                CHECK (julianday(created_at) IS NOT NULL),
            CHECK (correct_count + incorrect_count + skipped_count = question_count),
            CHECK (julianday(finished_at) >= julianday(started_at))
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS quiz_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL REFERENCES quiz_attempts(id) ON DELETE CASCADE,
            question_order INTEGER NOT NULL
                CHECK (typeof(question_order) = 'integer' AND question_order > 0),
            question_id TEXT NOT NULL CHECK (length(trim(question_id)) > 0),
            sign_code TEXT CHECK (sign_code IS NULL OR length(trim(sign_code)) > 0),
            question_snapshot TEXT NOT NULL CHECK (
                CASE WHEN json_valid(question_snapshot)
                    THEN json_type(question_snapshot) = 'object'
                    ELSE 0 END
            ),
            options_snapshot TEXT NOT NULL,
            selected_answer INTEGER,
            correct_answer INTEGER NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('correct', 'incorrect', 'skipped')),
            marked_for_review INTEGER NOT NULL DEFAULT 0
                CHECK (marked_for_review IN (0, 1)),
            UNIQUE (attempt_id, question_order),
            CHECK (
                CASE WHEN json_valid(options_snapshot) THEN
                    json_type(options_snapshot) = 'array'
                    AND json_array_length(options_snapshot) > 0
                    AND typeof(correct_answer) = 'integer'
                    AND correct_answer >= 0
                    AND correct_answer < json_array_length(options_snapshot)
                    AND (selected_answer IS NULL OR (
                        typeof(selected_answer) = 'integer'
                        AND selected_answer >= 0
                        AND selected_answer < json_array_length(options_snapshot)
                    ))
                ELSE 0 END
            ),
            CHECK (
                (status = 'skipped' AND selected_answer IS NULL)
                OR (status = 'correct' AND selected_answer IS NOT NULL
                    AND selected_answer = correct_answer)
                OR (status = 'incorrect' AND selected_answer IS NOT NULL
                    AND selected_answer <> correct_answer)
            )
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_progress (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            sign_code TEXT NOT NULL CHECK (length(trim(sign_code)) > 0),
            is_learned INTEGER NOT NULL DEFAULT 0 CHECK (is_learned IN (0, 1)),
            last_viewed_at TEXT
                CHECK (last_viewed_at IS NULL OR julianday(last_viewed_at) IS NOT NULL),
            view_count INTEGER NOT NULL DEFAULT 0
                CHECK (typeof(view_count) = 'integer' AND view_count >= 0),
            PRIMARY KEY (user_id, sign_code)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS sign_review_stats (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            sign_code TEXT NOT NULL CHECK (length(trim(sign_code)) > 0),
            total_answers INTEGER NOT NULL DEFAULT 0
                CHECK (typeof(total_answers) = 'integer' AND total_answers >= 0),
            correct_count INTEGER NOT NULL DEFAULT 0
                CHECK (typeof(correct_count) = 'integer' AND correct_count >= 0),
            incorrect_count INTEGER NOT NULL DEFAULT 0
                CHECK (typeof(incorrect_count) = 'integer' AND incorrect_count >= 0),
            last_answered_at TEXT
                CHECK (last_answered_at IS NULL OR julianday(last_answered_at) IS NOT NULL),
            next_review_at TEXT
                CHECK (next_review_at IS NULL OR julianday(next_review_at) IS NOT NULL),
            PRIMARY KEY (user_id, sign_code),
            CHECK (total_answers = correct_count + incorrect_count),
            CHECK (total_answers = 0 OR last_answered_at IS NOT NULL)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_finished
        ON quiz_attempts (user_id, finished_at DESC, id DESC)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_quiz_answers_sign
        ON quiz_answers (sign_code) WHERE sign_code IS NOT NULL
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_learning_progress_user_learned
        ON learning_progress (user_id, is_learned)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_sign_review_stats_user_incorrect
        ON sign_review_stats (user_id, incorrect_count DESC)
        """,
    ),
    2: (
        """ALTER TABLE quiz_attempts ADD COLUMN submission_id TEXT
            CHECK (submission_id IS NULL OR length(submission_id) = 36)""",
        """ALTER TABLE quiz_attempts ADD COLUMN request_hash TEXT
            CHECK (request_hash IS NULL OR length(request_hash) = 64)""",
        """CREATE UNIQUE INDEX idx_quiz_attempts_user_submission
            ON quiz_attempts (user_id, submission_id) WHERE submission_id IS NOT NULL""",
    ),
    3: (
        """CREATE TABLE survey_questions (
            id INTEGER PRIMARY KEY,
            survey_version INTEGER NOT NULL CHECK (typeof(survey_version) = 'integer' AND survey_version > 0),
            code TEXT NOT NULL CHECK (length(trim(code)) > 0),
            criterion TEXT NOT NULL CHECK (length(trim(criterion)) > 0),
            question_text TEXT NOT NULL CHECK (length(trim(question_text)) > 0),
            question_type TEXT NOT NULL CHECK (question_type IN ('likert', 'text')),
            is_required INTEGER NOT NULL CHECK (is_required IN (0, 1)),
            is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
            display_order INTEGER NOT NULL CHECK (typeof(display_order) = 'integer' AND display_order > 0),
            UNIQUE (survey_version, code),
            UNIQUE (survey_version, display_order),
            UNIQUE (id, survey_version, question_type)
        )""",
        """CREATE TABLE survey_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            survey_version INTEGER NOT NULL CHECK (typeof(survey_version) = 'integer' AND survey_version > 0),
            submitted_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                CHECK (julianday(submitted_at) IS NOT NULL),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                CHECK (julianday(updated_at) IS NOT NULL),
            UNIQUE (id, survey_version),
            CHECK (julianday(updated_at) >= julianday(submitted_at))
        )""",
        """CREATE TABLE survey_answers (
            response_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            survey_version INTEGER NOT NULL,
            question_type TEXT NOT NULL CHECK (question_type IN ('likert', 'text')),
            rating INTEGER,
            text_answer TEXT,
            question_snapshot TEXT NOT NULL CHECK (
                CASE WHEN json_valid(question_snapshot) THEN json_type(question_snapshot) = 'object' ELSE 0 END
            ),
            PRIMARY KEY (response_id, question_id),
            FOREIGN KEY (response_id, survey_version)
                REFERENCES survey_responses(id, survey_version) ON DELETE CASCADE,
            FOREIGN KEY (question_id, survey_version, question_type)
                REFERENCES survey_questions(id, survey_version, question_type) ON DELETE RESTRICT,
            CHECK (
                (question_type = 'likert' AND rating IS NOT NULL AND typeof(rating) = 'integer'
                    AND rating BETWEEN 1 AND 5 AND text_answer IS NULL)
                OR (question_type = 'text' AND rating IS NULL AND text_answer IS NOT NULL
                    AND typeof(text_answer) = 'text' AND length(text_answer) BETWEEN 1 AND 1000
                    AND instr(text_answer, char(0)) = 0)
            )
        )""",
        """CREATE INDEX idx_survey_responses_version_updated
            ON survey_responses (survey_version, updated_at DESC, id DESC)""",
        """CREATE INDEX idx_survey_answers_question_rating
            ON survey_answers (question_id, rating, response_id)""",
        # Đây là nội dung khảo sát chính thức, không phải phản hồi thử nghiệm.
        # Giữ nguyên nội dung phiên bản đã phát hành; sửa nội dung cần phiên bản mới.
        """INSERT INTO survey_questions VALUES
            (1, 1, 'interface', 'Giao diện', 'Giao diện ứng dụng dễ nhìn và dễ sử dụng.', 'likert', 1, 1, 1),
            (2, 1, 'sign_library', 'Thư viện biển báo', 'Thư viện biển báo giúp tôi hiểu rõ hơn ý nghĩa các biển báo giao thông.', 'likert', 1, 1, 2),
            (3, 1, 'practice', 'Bài tập trắc nghiệm', 'Bài tập trắc nghiệm giúp tôi luyện tập và ghi nhớ biển báo.', 'likert', 1, 1, 3),
            (4, 1, 'recognition', 'Nhận dạng biển báo', 'Chức năng nhận dạng biển báo từ hình ảnh, video hoặc camera hữu ích cho việc học.', 'likert', 1, 1, 4),
            (5, 1, 'continued_use', 'Ý định tiếp tục sử dụng', 'Tôi muốn tiếp tục sử dụng ứng dụng để học và ôn tập biển báo giao thông.', 'likert', 1, 1, 5),
            (6, 1, 'feedback', 'Góp ý', 'Bạn có góp ý gì để ứng dụng được cải thiện tốt hơn?', 'text', 0, 1, 6)""",
    ),
    4: (
        # 1. Bổ sung các cột mới vào bảng users: role, status, email_verified, updated_at
        """ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'
            CHECK (role IN ('user', 'admin'))""",
        """ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'active'
            CHECK (status IN ('active', 'suspended', 'locked'))""",
        """ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0
            CHECK (email_verified IN (0, 1))""",
        """ALTER TABLE users ADD COLUMN updated_at TEXT NOT NULL DEFAULT '1970-01-01 00:00:00'""",
        # 2. Cập nhật các tài khoản Google đã có thành email_verified = 1 và cập nhật updated_at
        """UPDATE users SET email_verified = 1,
               updated_at = COALESCE(lan_dang_nhap_cuoi, ngay_tao, CURRENT_TIMESTAMP)
           WHERE google_sub IS NOT NULL AND length(trim(google_sub)) > 0""",
        # 3. Tạo bảng auth_identities quản lý các phương thức đăng nhập
        """CREATE TABLE IF NOT EXISTS auth_identities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            provider TEXT NOT NULL CHECK (provider IN ('google', 'password', 'email')),
            provider_subject TEXT NOT NULL CHECK (length(trim(provider_subject)) > 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                CHECK (julianday(created_at) IS NOT NULL),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                CHECK (julianday(updated_at) IS NOT NULL),
            UNIQUE (provider, provider_subject)
        )""",
        # 4. Di chuyển dữ liệu google_sub hiện có sang auth_identities
        """INSERT OR IGNORE INTO auth_identities (user_id, provider, provider_subject, created_at, updated_at)
           SELECT id, 'google', google_sub,
                  COALESCE(ngay_tao, CURRENT_TIMESTAMP),
                  COALESCE(lan_dang_nhap_cuoi, ngay_tao, CURRENT_TIMESTAMP)
           FROM users WHERE google_sub IS NOT NULL AND length(trim(google_sub)) > 0""",
        # 5. Tạo bảng password_credentials lưu mã băm mật khẩu
        """CREATE TABLE IF NOT EXISTS password_credentials (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            password_hash TEXT NOT NULL CHECK (length(password_hash) > 0),
            password_updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                CHECK (julianday(password_updated_at) IS NOT NULL)
        )""",
        # 6. Tạo bảng email_verification_tokens
        """CREATE TABLE IF NOT EXISTS email_verification_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE CHECK (length(token_hash) = 64),
            email TEXT NOT NULL CHECK (length(trim(email)) > 0),
            expires_at TEXT NOT NULL CHECK (julianday(expires_at) IS NOT NULL),
            used_at TEXT CHECK (used_at IS NULL OR julianday(used_at) IS NOT NULL),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                CHECK (julianday(created_at) IS NOT NULL)
        )""",
        # 7. Tạo bảng password_reset_tokens
        """CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE CHECK (length(token_hash) = 64),
            expires_at TEXT NOT NULL CHECK (julianday(expires_at) IS NOT NULL),
            used_at TEXT CHECK (used_at IS NULL OR julianday(used_at) IS NOT NULL),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                CHECK (julianday(created_at) IS NOT NULL)
        )""",
        # 8. Chỉ mục hiệu năng
        """CREATE INDEX IF NOT EXISTS idx_auth_identities_user_provider
           ON auth_identities (user_id, provider)""",
        """CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user
           ON email_verification_tokens (user_id, expires_at)""",
        """CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user
           ON password_reset_tokens (user_id, expires_at)""",
        """CREATE INDEX IF NOT EXISTS idx_users_role
           ON users (role)""",
        """CREATE INDEX IF NOT EXISTS idx_users_email
           ON users (email) WHERE email IS NOT NULL""",
    ),
    5: (
        # 1. Bảng nhật ký quản trị (admin_audit_logs)
        """CREATE TABLE IF NOT EXISTS admin_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            action TEXT NOT NULL CHECK (length(trim(action)) > 0),
            target_type TEXT NOT NULL CHECK (length(trim(target_type)) > 0),
            target_id TEXT,
            details_json TEXT,
            ip_address TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                CHECK (julianday(created_at) IS NOT NULL)
        )""",
        """CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_created
           ON admin_audit_logs (actor_user_id, created_at DESC)""",
        """CREATE INDEX IF NOT EXISTS idx_audit_logs_action_created
           ON admin_audit_logs (action, created_at DESC)""",
        # 2. Bảng quản lý xác thực hai yếu tố MFA TOTP cho Admin
        """CREATE TABLE IF NOT EXISTS admin_mfa_credentials (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            secret_key TEXT NOT NULL CHECK (length(secret_key) >= 16),
            is_enabled INTEGER NOT NULL DEFAULT 0 CHECK (is_enabled IN (0, 1)),
            backup_codes_json TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                CHECK (julianday(created_at) IS NOT NULL),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                CHECK (julianday(updated_at) IS NOT NULL)
        )""",
        # 3. Bảng metadata ghi đè an toàn cho thư viện biển báo
        """CREATE TABLE IF NOT EXISTS admin_sign_metadata (
            sign_code TEXT PRIMARY KEY CHECK (length(trim(sign_code)) > 0),
            is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
            custom_ten TEXT,
            custom_y_nghia TEXT,
            custom_ghi_chu TEXT,
            updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                CHECK (julianday(updated_at) IS NOT NULL)
        )""",
        # 4. Bảng quản lý tùy chỉnh và trạng thái câu hỏi trắc nghiệm
        """CREATE TABLE IF NOT EXISTS quiz_questions_override (
            question_id TEXT PRIMARY KEY CHECK (length(trim(question_id)) > 0),
            sign_code TEXT NOT NULL CHECK (length(trim(sign_code)) > 0),
            is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
            custom_prompt TEXT,
            custom_explanation TEXT,
            updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                CHECK (julianday(updated_at) IS NOT NULL)
        )""",
    ),
    6: (
        # 1. Bảng lưu yêu cầu xác thực OTP đặt lại mật khẩu qua email
        """CREATE TABLE IF NOT EXISTS password_reset_otp_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            email TEXT NOT NULL CHECK (length(trim(email)) > 0),
            otp_hash TEXT NOT NULL CHECK (length(otp_hash) = 64),
            attempts_left INTEGER NOT NULL DEFAULT 5 CHECK (attempts_left >= 0 AND attempts_left <= 5),
            expires_at TEXT NOT NULL CHECK (julianday(expires_at) IS NOT NULL),
            verified_at TEXT CHECK (verified_at IS NULL OR julianday(verified_at) IS NOT NULL),
            reset_grant_hash TEXT UNIQUE CHECK (reset_grant_hash IS NULL OR length(reset_grant_hash) = 64),
            grant_expires_at TEXT CHECK (grant_expires_at IS NULL OR julianday(grant_expires_at) IS NOT NULL),
            used_at TEXT CHECK (used_at IS NULL OR julianday(used_at) IS NOT NULL),
            ip_address TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP CHECK (julianday(created_at) IS NOT NULL)
        )""",
        """CREATE INDEX IF NOT EXISTS idx_reset_otp_email_active
           ON password_reset_otp_requests (email, expires_at)""",
        """CREATE INDEX IF NOT EXISTS idx_reset_otp_grant
           ON password_reset_otp_requests (reset_grant_hash)""",
        """CREATE INDEX IF NOT EXISTS idx_reset_otp_user
           ON password_reset_otp_requests (user_id, created_at)""",
    ),
    7: (
        # 1. Bảng lưu yêu cầu xác thực OTP kích hoạt tài khoản đăng ký mới qua email
        """CREATE TABLE IF NOT EXISTS email_verification_otp_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            email TEXT NOT NULL CHECK (length(trim(email)) > 0),
            otp_hash TEXT NOT NULL CHECK (length(otp_hash) = 64),
            attempts_left INTEGER NOT NULL DEFAULT 5 CHECK (attempts_left >= 0 AND attempts_left <= 5),
            expires_at TEXT NOT NULL CHECK (julianday(expires_at) IS NOT NULL),
            verified_at TEXT CHECK (verified_at IS NULL OR julianday(verified_at) IS NOT NULL),
            used_at TEXT CHECK (used_at IS NULL OR julianday(used_at) IS NOT NULL),
            ip_address TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP CHECK (julianday(created_at) IS NOT NULL)
        )""",
        """CREATE INDEX IF NOT EXISTS idx_verify_otp_email_active
           ON email_verification_otp_requests (email, expires_at)""",
        """CREATE INDEX IF NOT EXISTS idx_verify_otp_user
           ON email_verification_otp_requests (user_id, created_at)""",
    ),
    8: (
        # 1. Bổ sung cột username vào bảng users
        """ALTER TABLE users ADD COLUMN username TEXT""",
        # 2. Tạo unique index không phân biệt hoa thường COLLATE NOCASE
        """CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username
           ON users (username COLLATE NOCASE) WHERE username IS NOT NULL""",
        # 3. Tự động gán username mặc định user_{id} cho các tài khoản hiện có nếu username bị NULL
        """UPDATE users SET username = 'user_' || id
           WHERE username IS NULL OR trim(username) = ''""",
    ),
}


def ket_noi(duong_dan=None):
    """Mở SQLite với khóa ngoại; bên gọi chịu trách nhiệm đóng kết nối.

    Có thể truyền đường dẫn riêng để kiểm thử mà không đụng users.db thật.
    """
    duong_dan = os.fspath(DUONG_DAN_DB if duong_dan is None else duong_dan)
    if duong_dan != ":memory:":
        duong_dan = os.path.abspath(duong_dan)
        os.makedirs(os.path.dirname(duong_dan), exist_ok=True)

    conn = sqlite3.connect(duong_dan, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 10000")
        if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise RuntimeError("Khong bat duoc khoa ngoai SQLite")
    except Exception:
        conn.close()
        raise

    return conn


@contextmanager
def giao_dich(duong_dan=None):
    """Gộp các thao tác ghi vào một transaction và luôn đóng kết nối.

    Thành công thì commit, có ngoại lệ thì rollback toàn bộ. Không tự commit
    hoặc gọi executescript trong khối này vì sẽ phá tính nguyên tử.
    """
    with closing(ket_noi(duong_dan)) as conn:
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            yield conn


def khoi_tao_db(duong_dan=None):
    """Khởi tạo/migrate schema an toàn, giữ nguyên users và tài khoản cũ."""

    with giao_dich(duong_dan) as conn:
        phien_ban = conn.execute("PRAGMA user_version").fetchone()[0]
        if phien_ban > PHIEN_BAN_SCHEMA:
            raise RuntimeError("Schema SQLite moi hon phien ban ung dung")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                google_sub TEXT NOT NULL UNIQUE,

                email TEXT,

                ten TEXT NOT NULL,

                anh_dai_dien TEXT,

                ngay_tao TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                lan_dang_nhap_cuoi TEXT
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        for ban_moi in range(phien_ban + 1, PHIEN_BAN_SCHEMA + 1):
            for sql in _MIGRATIONS[ban_moi]:
                conn.execute(sql)
            # Chỉ tăng phiên bản khi tất cả câu SQL đã thực thi thành công.
            conn.execute(f"PRAGMA user_version = {ban_moi}")

    print("Khoi tao co so du lieu thanh cong!")


def luu_nguoi_dung(thong_tin):
    """Thêm hoặc cập nhật tài khoản Google."""

    google_sub = thong_tin["sub"]
    email = thong_tin.get("email")
    ten = thong_tin.get("name") or "Người học"
    anh = thong_tin.get("picture")

    with giao_dich() as conn:
        conn.execute("""
            INSERT INTO users (
                google_sub, email, ten, anh_dai_dien, role, status, email_verified, updated_at
            )
            VALUES (?, ?, ?, ?, 'user', 'active', 1, CURRENT_TIMESTAMP)

            ON CONFLICT(google_sub) DO UPDATE SET
                email = excluded.email,
                ten = excluded.ten,
                anh_dai_dien = excluded.anh_dai_dien,
                email_verified = 1,
                lan_dang_nhap_cuoi = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
        """, (google_sub, email, ten, anh))

        row = conn.execute(
            "SELECT id, username FROM users WHERE google_sub = ?",
            (google_sub,)
        ).fetchone()

        user_id = row["id"]
        # Đảm bảo tài khoản Google luôn có username mặc định nếu chưa có
        if not row["username"] or not str(row["username"]).strip():
            conn.execute("UPDATE users SET username = 'user_' || ? WHERE id = ?", (user_id, user_id))

        # Đồng bộ sang bảng auth_identities
        conn.execute("""
            INSERT INTO auth_identities (user_id, provider, provider_subject, updated_at)
            VALUES (?, 'google', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(provider, provider_subject) DO UPDATE SET
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, google_sub))

        return user_id


def lay_nguoi_dung(user_id):
    """Lấy thông tin người dùng theo ID."""

    with closing(ket_noi()) as conn:
        row = conn.execute("""
            SELECT
                id,
                username,
                email,
                ten,
                anh_dai_dien,
                role,
                status,
                email_verified,
                ngay_tao,
                lan_dang_nhap_cuoi,
                updated_at
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

        return dict(row) if row else None


def tim_nguoi_dung_theo_dinh_danh(dinh_danh):
    """Tìm người dùng bằng tên tài khoản (username), email hoặc ID số nguyên."""
    if dinh_danh is None or dinh_danh == "":
        return None
    dinh_danh_str = str(dinh_danh).strip()
    with closing(ket_noi()) as conn:
        # 1. Nếu là số nguyên ID
        if isinstance(dinh_danh, int) or (isinstance(dinh_danh, str) and dinh_danh_str.isdigit()):
            row = conn.execute("""
                SELECT id, google_sub, username, email, ten, anh_dai_dien, role, status,
                       email_verified, ngay_tao, lan_dang_nhap_cuoi, updated_at
                FROM users WHERE id = ?
            """, (int(dinh_danh),)).fetchone()
            if row:
                return dict(row)

        # 2. Nếu chuỗi có chứa ký tự @ -> tìm theo email trước
        if "@" in dinh_danh_str:
            row = conn.execute("""
                SELECT id, google_sub, username, email, ten, anh_dai_dien, role, status,
                       email_verified, ngay_tao, lan_dang_nhap_cuoi, updated_at
                FROM users WHERE lower(trim(email)) = lower(trim(?))
            """, (dinh_danh_str,)).fetchone()
            if row:
                return dict(row)

        # 3. Tìm theo username (case-insensitive)
        row = conn.execute("""
            SELECT id, google_sub, username, email, ten, anh_dai_dien, role, status,
                   email_verified, ngay_tao, lan_dang_nhap_cuoi, updated_at
            FROM users WHERE lower(trim(username)) = lower(trim(?))
        """, (dinh_danh_str,)).fetchone()
        if row:
            return dict(row)

        # 4. Tìm theo email (nếu chuỗi không có @)
        row = conn.execute("""
            SELECT id, google_sub, username, email, ten, anh_dai_dien, role, status,
                   email_verified, ngay_tao, lan_dang_nhap_cuoi, updated_at
            FROM users WHERE lower(trim(email)) = lower(trim(?))
        """, (dinh_danh_str,)).fetchone()
        if row:
            return dict(row)

        return None


def tim_nguoi_dung_theo_email_hoac_id(dinh_danh):
    """Tìm người dùng bằng username, email hoặc ID (tương thích ngược)."""
    return tim_nguoi_dung_theo_dinh_danh(dinh_danh)


def kiem_tra_username_ton_tai(username, exclude_user_id=None):
    """Kiểm tra tên tài khoản (username) đã tồn tại hay chưa (không phân biệt hoa thường)."""
    if not username:
        return False
    u = str(username).strip()
    with closing(ket_noi()) as conn:
        if exclude_user_id is not None:
            row = conn.execute(
                "SELECT 1 FROM users WHERE lower(trim(username)) = lower(trim(?)) AND id != ?",
                (u, exclude_user_id)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT 1 FROM users WHERE lower(trim(username)) = lower(trim(?))",
                (u,)
            ).fetchone()
        return row is not None


def kiem_tra_email_ton_tai(email, exclude_user_id=None):
    """Kiểm tra email đã tồn tại hay chưa (không phân biệt hoa thường)."""
    if not email:
        return False
    e = str(email).strip().lower()
    with closing(ket_noi()) as conn:
        if exclude_user_id is not None:
            row = conn.execute(
                "SELECT 1 FROM users WHERE lower(trim(email)) = lower(trim(?)) AND id != ?",
                (e, exclude_user_id)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT 1 FROM users WHERE lower(trim(email)) = lower(trim(?))",
                (e,)
            ).fetchone()
        return row is not None


def dem_so_luong_admin():
    """Đếm tổng số tài khoản có vai trò 'admin' trong hệ thống."""
    with closing(ket_noi()) as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM users WHERE role = 'admin'").fetchone()
        return row["total"] if row else 0


def cap_nhat_vai_tro_nguoi_dung(user_id, role, cho_phep_nhieu_admin=False):
    """Cập nhật vai trò (user hoặc admin).
    
    Chỉ cho phép cấp quyền admin khi tài khoản đã xác minh email và đang hoạt động.
    Chính sách 1 Admin chính: Nếu đã có Admin và cho_phep_nhieu_admin=False, từ chối cấp thêm.
    """
    if role not in ("user", "admin"):
        raise ValueError(f"Vai trò không hợp lệ: {role}")
    with giao_dich() as conn:
        user = conn.execute("SELECT id, status, email_verified, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise ValueError(f"Không tìm thấy người dùng ID {user_id}")
        if role == "admin":
            if not user["email_verified"]:
                raise ValueError("Không thể cấp quyền Admin cho tài khoản chưa xác minh email.")
            if user["status"] != "active":
                raise ValueError(f"Không thể cấp quyền Admin cho tài khoản không ở trạng thái hoạt động (status={user['status']}).")
            if user["role"] != "admin" and not cho_phep_nhieu_admin:
                so_admin = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND id != ?", (user_id,)).fetchone()[0]
                if so_admin >= 1:
                    raise ValueError("Chính sách bảo mật: Hệ thống chỉ cho phép duy nhất một tài khoản Admin chính ban đầu.")
        conn.execute("""
            UPDATE users SET role = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (role, user_id))
    return lay_nguoi_dung(user_id)


def cap_nhat_trang_thai_nguoi_dung(user_id, status):
    """Cập nhật trạng thái người dùng (active, suspended, locked)."""
    if status not in ("active", "suspended", "locked"):
        raise ValueError(f"Trạng thái không hợp lệ: {status}")
    with giao_dich() as conn:
        user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise ValueError(f"Không tìm thấy người dùng ID {user_id}")
        conn.execute("""
            UPDATE users SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (status, user_id))
    return lay_nguoi_dung(user_id)


def danh_sach_tat_ca_nguoi_dung():
    """Liệt kê toàn bộ người dùng (phục vụ CLI quản trị)."""
    with closing(ket_noi()) as conn:
        rows = conn.execute("""
            SELECT id, username, email, ten, role, status, email_verified, ngay_tao, lan_dang_nhap_cuoi, updated_at
            FROM users ORDER BY id ASC
        """).fetchall()
        return [dict(r) for r in rows]


# ==============================================================================
# HÀM QUẢN TRỊ ADMIN (BƯỚC 18.4)
# ==============================================================================

def ghi_audit_log(actor_user_id, action, target_type, target_id=None, details=None, ip_address=None):
    """Ghi nhật ký quản trị viên vào bảng admin_audit_logs."""
    details_str = json.dumps(details, ensure_ascii=False) if details else None
    with giao_dich() as conn:
        conn.execute("""
            INSERT INTO admin_audit_logs (
                actor_user_id, action, target_type, target_id, details_json, ip_address, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (actor_user_id, action, target_type, str(target_id) if target_id is not None else None, details_str, ip_address))


def danh_sach_audit_logs(limit=20, offset=0, action=None, target_type=None):
    """Liệt kê nhật ký quản trị với bộ lọc và phân trang."""
    with closing(ket_noi()) as conn:
        where_clauses = []
        params = []
        if action:
            where_clauses.append("a.action = ?")
            params.append(action)
        if target_type:
            where_clauses.append("a.target_type = ?")
            params.append(target_type)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        count_sql = f"SELECT COUNT(*) FROM admin_audit_logs a {where_sql}"
        total = conn.execute(count_sql, params).fetchone()[0]

        sql = f"""
            SELECT a.id, a.actor_user_id, u.email AS actor_email, u.ten AS actor_name,
                   a.action, a.target_type, a.target_id, a.details_json, a.ip_address, a.created_at
            FROM admin_audit_logs a
            LEFT JOIN users u ON u.id = a.actor_user_id
            {where_sql}
            ORDER BY a.id DESC LIMIT ? OFFSET ?
        """
        rows = conn.execute(sql, params + [limit, offset]).fetchall()
        result = []
        for r in rows:
            item = dict(r)
            if item["details_json"]:
                try:
                    item["details"] = json.loads(item["details_json"])
                except Exception:
                    item["details"] = item["details_json"]
            else:
                item["details"] = None
            item.pop("details_json", None)
            result.append(item)
        return {"logs": result, "total": total, "limit": limit, "offset": offset}


def thong_ke_tong_quan_admin(range_days="30"):
    """Tổng hợp thống kê toàn diện cho Admin từ 100% dữ liệu thật trong SQLite."""
    with closing(ket_noi()) as conn:
        # 1. Thống kê người dùng
        user_stats = conn.execute("""
            SELECT
                COUNT(*) AS total_users,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_users,
                SUM(CASE WHEN status IN ('suspended', 'locked') THEN 1 ELSE 0 END) AS locked_users,
                SUM(CASE WHEN email_verified = 1 THEN 1 ELSE 0 END) AS verified_users,
                SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) AS admin_users
            FROM users
        """).fetchone()

        # 2. Thống kê bài tập trắc nghiệm
        quiz_stats = conn.execute("""
            SELECT
                COUNT(*) AS total_attempts,
                COUNT(DISTINCT user_id) AS total_participants,
                COALESCE(AVG(score), 0.0) AS average_score,
                COALESCE(SUM(question_count), 0) AS total_questions,
                COALESCE(SUM(correct_count), 0) AS total_correct
            FROM quiz_attempts
        """).fetchone()

        # 3. Thống kê khảo sát đầy đủ
        survey_full = conn.execute("""
            SELECT
                COUNT(*) AS total_responses
            FROM survey_responses
        """).fetchone()
        
        likert_avg = conn.execute("""
            SELECT AVG(rating) AS avg_likert
            FROM survey_answers
            WHERE question_type = 'likert' AND rating IS NOT NULL
        """).fetchone()

        # 4. Thống kê khảo sát nhanh (nếu bảng tồn tại)
        quick_stats = {"total_responses": 0, "avg_rating": 0.0}
        has_quick_table = conn.execute("""
            SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'quick_survey_responses'
        """).fetchone()
        if has_quick_table:
            q_row = conn.execute("""
                SELECT COUNT(*) AS total, COALESCE(AVG(rating), 0.0) AS avg_rating
                FROM quick_survey_responses
            """).fetchone()
            if q_row:
                quick_stats = {"total_responses": q_row["total"], "avg_rating": round(float(q_row["avg_rating"]), 2)}

        # 5. Dữ liệu biểu đồ (100% dữ liệu thật từ SQLite)
        # Phân bố điểm số bài tập: 0-2, 3-4, 5-6, 7-8, 9-10
        dist_row = conn.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN score >= 0 AND score < 3 THEN 1 ELSE 0 END), 0) AS s_0_2,
                COALESCE(SUM(CASE WHEN score >= 3 AND score < 5 THEN 1 ELSE 0 END), 0) AS s_3_4,
                COALESCE(SUM(CASE WHEN score >= 5 AND score < 7 THEN 1 ELSE 0 END), 0) AS s_5_6,
                COALESCE(SUM(CASE WHEN score >= 7 AND score < 9 THEN 1 ELSE 0 END), 0) AS s_7_8,
                COALESCE(SUM(CASE WHEN score >= 9 AND score <= 10 THEN 1 ELSE 0 END), 0) AS s_9_10
            FROM quiz_attempts
        """).fetchone()

        score_distribution = {
            "0-2": dist_row["s_0_2"] if dist_row else 0,
            "3-4": dist_row["s_3_4"] if dist_row else 0,
            "5-6": dist_row["s_5_6"] if dist_row else 0,
            "7-8": dist_row["s_7_8"] if dist_row else 0,
            "9-10": dist_row["s_9_10"] if dist_row else 0,
        }

        # Phân bố mức đánh giá khảo sát: 1 sao -> 5 sao
        survey_dist_sql = """
            SELECT rating, COUNT(*) as cnt FROM (
                SELECT rating FROM survey_answers WHERE question_type = 'likert' AND rating IS NOT NULL
                UNION ALL
                SELECT rating FROM quick_survey_responses WHERE rating IS NOT NULL
            ) GROUP BY rating
        """ if has_quick_table else """
            SELECT rating, COUNT(*) as cnt FROM survey_answers
            WHERE question_type = 'likert' AND rating IS NOT NULL
            GROUP BY rating
        """
        s_dist_rows = conn.execute(survey_dist_sql).fetchall()
        survey_ratings = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        for r in s_dist_rows:
            key = str(int(r["rating"])) if r["rating"] else ""
            if key in survey_ratings:
                survey_ratings[key] = r["cnt"]

        # Chuỗi thời gian bài tập & đăng ký
        range_clause = ""
        params_quiz = []
        params_user = []
        if str(range_days).lower() in ("7", "30", "90"):
            days_int = int(range_days)
            range_clause_quiz = "WHERE julianday(created_at) >= julianday('now', ?)"
            range_clause_user = "WHERE julianday(ngay_tao) >= julianday('now', ?)"
            params_quiz = [f"-{days_int} days"]
            params_user = [f"-{days_int} days"]
        else:
            range_clause_quiz = ""
            range_clause_user = ""

        daily_quizzes_rows = conn.execute(f"""
            SELECT date(created_at) AS day, COUNT(*) AS count
            FROM quiz_attempts
            {range_clause_quiz}
            GROUP BY date(created_at)
            ORDER BY day ASC
        """, params_quiz).fetchall()

        daily_users_rows = conn.execute(f"""
            SELECT date(ngay_tao) AS day, COUNT(*) AS count
            FROM users
            {range_clause_user}
            GROUP BY date(ngay_tao)
            ORDER BY day ASC
        """, params_user).fetchall()

        charts = {
            "range": str(range_days),
            "score_distribution": score_distribution,
            "survey_ratings": survey_ratings,
            "daily_quizzes": [{"day": r["day"], "count": r["count"]} for r in daily_quizzes_rows if r["day"]],
            "daily_users": [{"day": r["day"], "count": r["count"]} for r in daily_users_rows if r["day"]]
        }

        return {
            "users": {
                "total": user_stats["total_users"] or 0,
                "active": user_stats["active_users"] or 0,
                "locked": user_stats["locked_users"] or 0,
                "verified": user_stats["verified_users"] or 0,
                "admin": user_stats["admin_users"] or 0
            },
            "quizzes": {
                "total_attempts": quiz_stats["total_attempts"] or 0,
                "total_participants": quiz_stats["total_participants"] or 0,
                "average_score": round(float(quiz_stats["average_score"] or 0.0), 2),
                "total_questions": quiz_stats["total_questions"] or 0,
                "total_correct": quiz_stats["total_correct"] or 0
            },
            "surveys": {
                "full_survey": {
                    "total_responses": survey_full["total_responses"] or 0,
                    "average_rating": round(float(likert_avg["avg_likert"] or 0.0), 2) if likert_avg and likert_avg["avg_likert"] else 0.0
                },
                "quick_survey": quick_stats
            },
            "charts": charts,
            "ai_recognition": {
                "supported_on_server": False,
                "storage_mode": "browser_local_storage",
                "message": "Nhật ký nhận dạng hiện đang được lưu trên trình duyệt của người học; server không lưu ảnh/video để bảo đảm quyền riêng tư."
            }
        }


def danh_sach_nguoi_dung_admin(page=1, per_page=20, search=None, status=None, role=None, sort_by="id", sort_dir="asc"):
    """Liệt kê người dùng cho Admin: phân trang, tìm kiếm, lọc, không lộ thông tin nhạy cảm."""
    page = max(1, int(page))
    per_page = max(1, min(100, int(per_page)))
    offset = (page - 1) * per_page

    COT_SAP_XEP = {
        "id": "u.id",
        "username": "u.username",
        "ten": "u.ten",
        "ngay_tao": "u.ngay_tao",
        "lan_dang_nhap_cuoi": "u.lan_dang_nhap_cuoi",
        "role": "u.role",
        "status": "u.status"
    }
    col = COT_SAP_XEP.get(sort_by, "u.id")
    direction = "DESC" if str(sort_dir).lower() == "desc" else "ASC"

    with closing(ket_noi()) as conn:
        where = []
        params = []
        if search:
            s = f"%{search.strip().lower()}%"
            where.append("(lower(u.email) LIKE ? OR lower(u.ten) LIKE ? OR lower(u.username) LIKE ?)")
            params.extend([s, s, s])
        if status and status in ("active", "suspended", "locked"):
            where.append("u.status = ?")
            params.append(status)
        if role and role in ("user", "admin"):
            where.append("u.role = ?")
            params.append(role)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        count_sql = f"SELECT COUNT(*) FROM users u {where_sql}"
        total = conn.execute(count_sql, params).fetchone()[0]

        sql = f"""
            SELECT u.id, u.username, u.email, u.ten, u.anh_dai_dien, u.role, u.status, u.email_verified,
                   u.ngay_tao, u.lan_dang_nhap_cuoi, u.updated_at
            FROM users u
            {where_sql}
            ORDER BY {col} {direction}
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(sql, params + [per_page, offset]).fetchall()
        users = []
        for r in rows:
            u_dict = dict(r)
            p_rows = conn.execute("SELECT provider FROM auth_identities WHERE user_id = ?", (u_dict["id"],)).fetchall()
            u_dict["providers"] = [p["provider"] for p in p_rows]
            users.append(u_dict)

        return {
            "users": users,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if total > 0 else 1
        }


def chi_tiet_nguoi_dung_admin(user_id):
    """Lấy thông tin chi tiết người dùng phục vụ quản trị."""
    with closing(ket_noi()) as conn:
        row = conn.execute("""
            SELECT id, username, email, ten, anh_dai_dien, role, status, email_verified,
                   ngay_tao, lan_dang_nhap_cuoi, updated_at
            FROM users WHERE id = ?
        """, (user_id,)).fetchone()
        if not row:
            return None
        u = dict(row)
        p_rows = conn.execute("SELECT provider, created_at FROM auth_identities WHERE user_id = ?", (user_id,)).fetchall()
        u["providers"] = [{"provider": p["provider"], "created_at": p["created_at"]} for p in p_rows]

        q_count = conn.execute("SELECT COUNT(*) FROM quiz_attempts WHERE user_id = ?", (user_id,)).fetchone()[0]
        u["total_quiz_attempts"] = q_count

        s_count = conn.execute("SELECT COUNT(*) FROM survey_responses WHERE user_id = ?", (user_id,)).fetchone()[0]
        u["has_survey"] = s_count > 0

        mfa = conn.execute("SELECT is_enabled, created_at FROM admin_mfa_credentials WHERE user_id = ?", (user_id,)).fetchone()
        u["mfa_enabled"] = bool(mfa["is_enabled"]) if mfa else False

        return u


def cap_nhat_trang_thai_nguoi_dung_admin(actor_user_id, target_user_id, status, reason, ip_address=None):
    """Cập nhật trạng thái người dùng (active, suspended, locked) có audit log và kiểm tra bảo vệ Admin."""
    if status not in ("active", "suspended", "locked"):
        raise ValueError(f"Trạng thái không hợp lệ: {status}")
    if not reason or len(reason.strip()) < 3:
        raise ValueError("Vui lòng cung cấp lý do thay đổi trạng thái (tối thiểu 3 ký tự).")
    if actor_user_id == target_user_id and status != "active":
        raise ValueError("Admin không thể tự khóa tài khoản của chính mình.")

    with giao_dich() as conn:
        target = conn.execute("SELECT id, email, ten, role, status FROM users WHERE id = ?", (target_user_id,)).fetchone()
        if not target:
            raise ValueError(f"Không tìm thấy người dùng ID {target_user_id}")

        old_status = target["status"]
        if target["role"] == "admin" and status != "active":
            so_admin_khac = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'admin' AND status = 'active' AND id != ?",
                (target_user_id,)
            ).fetchone()[0]
            if so_admin_khac == 0:
                raise ValueError("Không thể khóa tài khoản Admin chính duy nhất của hệ thống.")

        conn.execute("UPDATE users SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, target_user_id))

        conn.execute("""
            INSERT INTO admin_audit_logs (actor_user_id, action, target_type, target_id, details_json, ip_address, created_at)
            VALUES (?, 'change_user_status', 'user', ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            actor_user_id,
            str(target_user_id),
            json.dumps({"old_status": old_status, "new_status": status, "reason": reason.strip()}, ensure_ascii=False),
            ip_address
        ))

    return chi_tiet_nguoi_dung_admin(target_user_id)


def lay_mfa_admin(user_id):
    """Lấy thông tin MFA của admin."""
    with closing(ket_noi()) as conn:
        row = conn.execute("SELECT user_id, secret_key, is_enabled, backup_codes_json FROM admin_mfa_credentials WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def luu_mfa_admin(user_id, secret_key, backup_codes=None):
    """Lưu cấu hình MFA tạm thời (chưa kích hoạt)."""
    codes_str = json.dumps(backup_codes) if backup_codes else None
    with giao_dich() as conn:
        conn.execute("""
            INSERT INTO admin_mfa_credentials (user_id, secret_key, is_enabled, backup_codes_json, updated_at)
            VALUES (?, ?, 0, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                secret_key = excluded.secret_key,
                is_enabled = 0,
                backup_codes_json = excluded.backup_codes_json,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, secret_key, codes_str))


def kich_hoat_mfa_admin(user_id):
    """Đánh dấu MFA đã kích hoạt thành công sau khi xác thực OTP lần đầu."""
    with giao_dich() as conn:
        conn.execute("""
            UPDATE admin_mfa_credentials SET is_enabled = 1, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))


def tat_mfa_admin(user_id):
    """Tắt MFA cho Admin."""
    with giao_dich() as conn:
        conn.execute("DELETE FROM admin_mfa_credentials WHERE user_id = ?", (user_id,))


def lay_toan_bo_sign_metadata():
    """Lấy danh sách các biển báo có metadata override."""
    with closing(ket_noi()) as conn:
        rows = conn.execute("SELECT sign_code, is_active, custom_ten, custom_y_nghia, custom_ghi_chu, updated_by, updated_at FROM admin_sign_metadata").fetchall()
        return {r["sign_code"]: dict(r) for r in rows}


def lay_sign_metadata(sign_code):
    """Lấy metadata override của 1 biển báo cụ thể."""
    with closing(ket_noi()) as conn:
        row = conn.execute("SELECT sign_code, is_active, custom_ten, custom_y_nghia, custom_ghi_chu, updated_by, updated_at FROM admin_sign_metadata WHERE sign_code = ?", (sign_code,)).fetchone()
        return dict(row) if row else None


def cap_nhat_sign_metadata(sign_code, is_active=1, custom_ten=None, custom_y_nghia=None, custom_ghi_chu=None, updated_by=None):
    """Cập nhật metadata hiển thị học tập của biển báo (không đụng mô hình AI)."""
    with giao_dich() as conn:
        conn.execute("""
            INSERT INTO admin_sign_metadata (sign_code, is_active, custom_ten, custom_y_nghia, custom_ghi_chu, updated_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(sign_code) DO UPDATE SET
                is_active = excluded.is_active,
                custom_ten = excluded.custom_ten,
                custom_y_nghia = excluded.custom_y_nghia,
                custom_ghi_chu = excluded.custom_ghi_chu,
                updated_by = excluded.updated_by,
                updated_at = CURRENT_TIMESTAMP
        """, (sign_code, is_active, custom_ten, custom_y_nghia, custom_ghi_chu, updated_by))


def lay_toan_bo_quiz_override():
    """Lấy danh sách các câu hỏi trắc nghiệm có override."""
    with closing(ket_noi()) as conn:
        rows = conn.execute("SELECT question_id, sign_code, is_active, custom_prompt, custom_explanation, updated_by, updated_at FROM quiz_questions_override").fetchall()
        return {r["question_id"]: dict(r) for r in rows}


def lay_quiz_override(question_id):
    """Lấy override của 1 câu hỏi cụ thể."""
    with closing(ket_noi()) as conn:
        row = conn.execute("SELECT question_id, sign_code, is_active, custom_prompt, custom_explanation, updated_by, updated_at FROM quiz_questions_override WHERE question_id = ?", (question_id,)).fetchone()
        return dict(row) if row else None


def cap_nhat_quiz_override(question_id, sign_code, is_active=1, custom_prompt=None, custom_explanation=None, updated_by=None):
    """Cập nhật hoặc ẩn câu hỏi trắc nghiệm (không xóa ID lịch sử)."""
    with giao_dich() as conn:
        conn.execute("""
            INSERT INTO quiz_questions_override (question_id, sign_code, is_active, custom_prompt, custom_explanation, updated_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(question_id) DO UPDATE SET
                is_active = excluded.is_active,
                custom_prompt = excluded.custom_prompt,
                custom_explanation = excluded.custom_explanation,
                updated_by = excluded.updated_by,
                updated_at = CURRENT_TIMESTAMP
        """, (question_id, sign_code, is_active, custom_prompt, custom_explanation, updated_by))


def luu_token_xac_minh_email(user_id, email, token_hash, expires_at):
    """Lưu token băm xác minh email."""
    with giao_dich() as conn:
        return conn.execute("""
            INSERT INTO email_verification_tokens (user_id, token_hash, email, expires_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, token_hash, email, expires_at)).lastrowid


def luu_token_dat_lai_mat_khau(user_id, token_hash, expires_at):
    """Lưu token băm đặt lại mật khẩu."""
    with giao_dich() as conn:
        return conn.execute("""
            INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
            VALUES (?, ?, ?)
        """, (user_id, token_hash, expires_at)).lastrowid


def tim_token_xac_minh(token_hash):
    """Tìm token xác minh email theo token_hash."""
    with closing(ket_noi()) as conn:
        row = conn.execute("""
            SELECT id, user_id, token_hash, email, expires_at, used_at, created_at
            FROM email_verification_tokens WHERE token_hash = ?
        """, (token_hash,)).fetchone()
        return dict(row) if row else None


def tim_token_dat_lai(token_hash):
    """Tìm token đặt lại mật khẩu theo token_hash."""
    with closing(ket_noi()) as conn:
        row = conn.execute("""
            SELECT id, user_id, token_hash, expires_at, used_at, created_at
            FROM password_reset_tokens WHERE token_hash = ?
        """, (token_hash,)).fetchone()
        return dict(row) if row else None


class UsernameDaTonTai(ValueError):
    """Tên tài khoản (username) đã được sử dụng."""


class UsernameKhongHopLe(ValueError):
    """Tên tài khoản không hợp lệ hoặc nằm trong danh sách cấm."""


class EmailDaTonTai(ValueError):
    """Email đã tồn tại trong hệ thống."""


class EmailChuaXacMinh(ValueError):
    """Email đã đăng ký trước đó nhưng chưa xác minh."""
    def __init__(self, message, user_id=None, email=None):
        super().__init__(message)
        self.user_id = user_id
        self.email = email


class EmailDaDangKyGoogle(ValueError):
    """Email đã đăng ký qua Google OAuth, cần hướng dẫn người dùng đăng nhập Google."""


class TaiKhoanGoogleDaLienKet(ValueError):
    """Tài khoản Google đã liên kết với người dùng khác."""


class KhongTheHuyPhuongThucDuyNhat(ValueError):
    """Không thể hủy liên kết vì đây là phương thức đăng nhập duy nhất."""


class ChuaThietLapMatKhau(ValueError):
    """Tài khoản chưa thiết lập mật khẩu cá nhân."""


class DaCoMatKhau(ValueError):
    """Tài khoản đã có mật khẩu cá nhân."""


def dang_ky_tai_khoan(ten, username, mat_khau_hash, email=None):
    """Đăng ký tài khoản mới bằng Tên tài khoản, Mật khẩu và Email tùy chọn.
    
    - ten: Bắt buộc (2-50 ký tự).
    - username: Bắt buộc (3-30 ký tự, duy nhất COLLATE NOCASE).
    - mat_khau_hash: Bắt buộc (chuỗi băm scrypt).
    - email: Tùy chọn. Nếu cung cấp, phải hợp lệ và chưa từng được sử dụng.
    """
    import secrets
    ten = ten.strip()
    username = username.strip()
    email_clean = email.strip().lower() if email and str(email).strip() else None

    with giao_dich() as conn:
        # 1. Kiểm tra username đã tồn tại chưa (case-insensitive)
        row_u = conn.execute("SELECT id FROM users WHERE lower(trim(username)) = lower(trim(?))", (username,)).fetchone()
        if row_u:
            raise UsernameDaTonTai("Tên tài khoản đã được sử dụng. Vui lòng chọn tên khác.")

        # 2. Nếu có email, kiểm tra trùng lặp email
        if email_clean:
            cu = conn.execute("SELECT id, email_verified FROM users WHERE lower(trim(email)) = ?", (email_clean,)).fetchone()
            if cu:
                is_google = conn.execute(
                    "SELECT 1 FROM auth_identities WHERE user_id = ? AND provider = 'google'",
                    (cu["id"],)
                ).fetchone()
                if is_google:
                    raise EmailDaDangKyGoogle("Email này đã được đăng ký bằng Google. Vui lòng chọn 'Đăng nhập với Google'.")
                if not cu["email_verified"]:
                    raise EmailChuaXacMinh(
                        "Email này đã được đăng ký nhưng chưa xác minh. Mã OTP mới đã được gửi để bạn kích hoạt tài khoản.",
                        user_id=cu["id"],
                        email=email_clean
                    )
                raise EmailDaTonTai("Email này đã được đăng ký tài khoản. Vui lòng đăng nhập hoặc yêu cầu xác minh.")

        # 3. Tạo tài khoản
        local_sub = "local:" + secrets.token_hex(16)
        user_id = conn.execute("""
            INSERT INTO users (
                google_sub, username, email, ten, role, status, email_verified, updated_at
            ) VALUES (?, ?, ?, ?, 'user', 'active', 0, CURRENT_TIMESTAMP)
        """, (local_sub, username, email_clean, ten)).lastrowid

        # 4. Lưu mã băm mật khẩu
        conn.execute("""
            INSERT INTO password_credentials (user_id, password_hash)
            VALUES (?, ?)
        """, (user_id, mat_khau_hash))

        # 5. Lưu vào auth_identities
        conn.execute("""
            INSERT INTO auth_identities (user_id, provider, provider_subject)
            VALUES (?, 'password', ?)
        """, (user_id, username))

        if email_clean:
            conn.execute("""
                INSERT OR IGNORE INTO auth_identities (user_id, provider, provider_subject)
                VALUES (?, 'email', ?)
            """, (user_id, email_clean))

        return user_id


def dang_ky_tai_khoan_email(ten, email, mat_khau_hash, username=None):
    """Đăng ký tài khoản mới bằng Email và Mật khẩu (hàm tương thích ngược)."""
    import secrets
    if not username:
        prefix = email.split("@")[0] if "@" in email else "user"
        clean = "".join(c for c in prefix if c.isalnum() or c in ("_", "."))
        if len(clean) < 3:
            clean = f"user_{secrets.token_hex(4)}"
        candidate = clean[:25]
        if kiem_tra_username_ton_tai(candidate):
            candidate = f"{candidate[:20]}_{secrets.token_hex(3)}"
        username = candidate
    return dang_ky_tai_khoan(ten, username, mat_khau_hash, email=email)


def lien_ket_email_nguoi_dung(user_id, email):
    """Liên kết hoặc cập nhật địa chỉ email đã xác minh cho người dùng."""
    email_clean = str(email).strip().lower()
    with giao_dich() as conn:
        other = conn.execute(
            "SELECT id FROM users WHERE lower(trim(email)) = ? AND id != ?",
            (email_clean, user_id)
        ).fetchone()
        if other:
            raise EmailDaTonTai("Địa chỉ email này đã được sử dụng bởi một tài khoản khác.")

        conn.execute("""
            UPDATE users SET email = ?, email_verified = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (email_clean, user_id))

        conn.execute("""
            INSERT INTO auth_identities (user_id, provider, provider_subject, created_at, updated_at)
            VALUES (?, 'email', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(provider, provider_subject) DO UPDATE SET
                user_id = excluded.user_id,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, email_clean))
        return True


def cap_nhat_username_nguoi_dung(user_id, new_username):
    """Cập nhật tên tài khoản (username) cho người dùng."""
    username_clean = str(new_username).strip()
    with giao_dich() as conn:
        other = conn.execute(
            "SELECT id FROM users WHERE lower(trim(username)) = lower(trim(?)) AND id != ?",
            (username_clean, user_id)
        ).fetchone()
        if other:
            raise UsernameDaTonTai("Tên tài khoản đã được sử dụng. Vui lòng chọn tên khác.")

        conn.execute("""
            UPDATE users SET username = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (username_clean, user_id))
        return True


def lay_mat_khau_hash(user_id):
    """Lấy password_hash của tài khoản theo user_id."""
    with closing(ket_noi()) as conn:
        row = conn.execute(
            "SELECT password_hash FROM password_credentials WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return row["password_hash"] if row else None


def xac_minh_email_nguoi_dung(user_id):
    """Cập nhật trạng thái email_verified = 1 cho người dùng."""
    with giao_dich() as conn:
        conn.execute("""
            UPDATE users SET email_verified = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))


def cap_nhat_dang_nhap_thanh_cong(user_id):
    """Cập nhật thời điểm đăng nhập cuối cùng."""
    with giao_dich() as conn:
        conn.execute("""
            UPDATE users SET lan_dang_nhap_cuoi = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))


def lay_cac_phuong_thuc_dang_nhap(user_id):
    """Trả về danh sách các provider ('google', 'password') của tài khoản."""
    with closing(ket_noi()) as conn:
        rows = conn.execute(
            "SELECT provider FROM auth_identities WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        return [r["provider"] for r in rows]


def lay_chi_tiet_phuong_thuc_xac_thuc(user_id):
    """Lấy thông tin chi tiết các phương thức đăng nhập và bảo mật của tài khoản."""
    with closing(ket_noi()) as conn:
        user = conn.execute(
            "SELECT id, username, email, ten, anh_dai_dien, role, status, email_verified, google_sub FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        if not user:
            return None
        cred = conn.execute(
            "SELECT password_updated_at FROM password_credentials WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        providers = conn.execute(
            "SELECT provider, provider_subject FROM auth_identities WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        prov_dict = {r["provider"]: r["provider_subject"] for r in providers}
        has_email = user["email"] is not None and len(str(user["email"]).strip()) > 0
        return {
            "user_id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "has_email": has_email,
            "ten": user["ten"],
            "anh_dai_dien": user["anh_dai_dien"],
            "role": user["role"],
            "status": user["status"],
            "email_verified": bool(user["email_verified"]),
            "has_password": cred is not None or "password" in prov_dict,
            "has_google": "google" in prov_dict,
            "password_updated_at": cred["password_updated_at"] if cred else None,
            "google_sub": prov_dict.get("google")
        }


def dat_lai_mat_khau_nguoi_dung(user_id, mat_khau_moi_hash, token_hash):
    """Đặt lại mật khẩu bằng token khôi phục và vô hiệu hóa tất cả token reset cũ."""
    with giao_dich() as conn:
        # 1. Vô hiệu hóa tất cả các token reset còn hiệu lực của user
        conn.execute("""
            UPDATE password_reset_tokens SET used_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND used_at IS NULL
        """, (user_id,))

        # 2. Cập nhật hoặc thêm mới mật khẩu
        conn.execute("""
            INSERT INTO password_credentials (user_id, password_hash, password_updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                password_hash = excluded.password_hash,
                password_updated_at = CURRENT_TIMESTAMP
        """, (user_id, mat_khau_moi_hash))

        # 3. Đảm bảo có định danh password trong auth_identities
        user = conn.execute("SELECT email FROM users WHERE id = ?", (user_id,)).fetchone()
        email = (user["email"] if user and user["email"] else f"user_{user_id}@local").strip().lower()
        conn.execute("""
            INSERT INTO auth_identities (user_id, provider, provider_subject, created_at, updated_at)
            VALUES (?, 'password', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(provider, provider_subject) DO UPDATE SET
                user_id = excluded.user_id,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, email))

        # 4. Khi reset qua email thành công, tài khoản cũng được xác minh email
        conn.execute("""
            UPDATE users SET email_verified = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))


def doi_mat_khau_nguoi_dung(user_id, mat_khau_moi_hash):
    """Đổi mật khẩu cho người dùng đã đăng nhập."""
    with giao_dich() as conn:
        cred = conn.execute("SELECT user_id FROM password_credentials WHERE user_id = ?", (user_id,)).fetchone()
        if not cred:
            raise ChuaThietLapMatKhau("Tài khoản chưa có mật khẩu cá nhân. Vui lòng thiết lập mật khẩu.")

        conn.execute("""
            UPDATE password_credentials SET password_hash = ?, password_updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (mat_khau_moi_hash, user_id))

        # Vô hiệu hóa mọi token reset cũ
        conn.execute("""
            UPDATE password_reset_tokens SET used_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND used_at IS NULL
        """, (user_id,))

        conn.execute("UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))


def thiet_lap_mat_khau_lan_dau(user_id, mat_khau_hash):
    """Thiết lập mật khẩu lần đầu cho tài khoản Google chưa có mật khẩu."""
    with giao_dich() as conn:
        cred = conn.execute("SELECT user_id FROM password_credentials WHERE user_id = ?", (user_id,)).fetchone()
        if cred:
            raise DaCoMatKhau("Tài khoản đã có mật khẩu cá nhân. Vui lòng dùng chức năng đổi mật khẩu.")

        conn.execute("""
            INSERT INTO password_credentials (user_id, password_hash, password_updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (user_id, mat_khau_hash))

        user = conn.execute("SELECT email FROM users WHERE id = ?", (user_id,)).fetchone()
        email = (user["email"] if user and user["email"] else f"user_{user_id}@local").strip().lower()
        conn.execute("""
            INSERT INTO auth_identities (user_id, provider, provider_subject, created_at, updated_at)
            VALUES (?, 'password', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(provider, provider_subject) DO UPDATE SET
                user_id = excluded.user_id,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, email))

        conn.execute("UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))


def lien_ket_tai_khoan_google(user_id, google_sub, google_email=None, google_avatar=None):
    """Liên kết tài khoản Google với tài khoản hiện tại."""
    google_sub = str(google_sub).strip()
    if not google_sub:
        raise ValueError("Google Sub không được để trống.")

    with giao_dich() as conn:
        # Kiểm tra xem google_sub đã bị liên kết với tài khoản khác chưa
        existing = conn.execute("""
            SELECT user_id FROM auth_identities
            WHERE provider = 'google' AND provider_subject = ?
        """, (google_sub,)).fetchone()
        if existing and existing["user_id"] != user_id:
            raise TaiKhoanGoogleDaLienKet("Tài khoản Google này đã được liên kết với một tài khoản khác.")

        # Kiểm tra thêm trong bảng users
        other = conn.execute("""
            SELECT id FROM users WHERE google_sub = ? AND id != ?
        """, (google_sub, user_id)).fetchone()
        if other:
            raise TaiKhoanGoogleDaLienKet("Tài khoản Google này đã được liên kết với một tài khoản khác.")

        # Lưu vào auth_identities
        conn.execute("""
            INSERT INTO auth_identities (user_id, provider, provider_subject, created_at, updated_at)
            VALUES (?, 'google', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(provider, provider_subject) DO UPDATE SET
                user_id = excluded.user_id,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, google_sub))

        # Cập nhật users: nếu google_sub đang là local: thì thay bằng google_sub thật
        user = conn.execute("SELECT google_sub, email, anh_dai_dien FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise ValueError(f"Không tìm thấy người dùng ID {user_id}")

        current_sub = user["google_sub"]
        new_sub = google_sub if current_sub.startswith("local:") else current_sub

        conn.execute("""
            UPDATE users SET
                google_sub = ?,
                email_verified = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_sub, user_id))

        if google_avatar and not user["anh_dai_dien"]:
            conn.execute("UPDATE users SET anh_dai_dien = ? WHERE id = ?", (google_avatar, user_id))

        if google_email and not user["email"]:
            conn.execute("UPDATE users SET email = ? WHERE id = ?", (google_email.strip().lower(), user_id))

        return True


def huy_lien_ket_google(user_id):
    """Hủy liên kết tài khoản Google; bắt buộc tài khoản phải còn phương thức mật khẩu."""
    import secrets

    with giao_dich() as conn:
        # 1. Kiểm tra các phương thức hiện có
        providers = conn.execute(
            "SELECT provider FROM auth_identities WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        prov_set = {r["provider"] for r in providers}

        if "google" not in prov_set:
            raise ValueError("Tài khoản chưa được liên kết với Google.")

        has_password = "password" in prov_set or conn.execute(
            "SELECT 1 FROM password_credentials WHERE user_id = ?",
            (user_id,)
        ).fetchone() is not None

        if not has_password:
            raise KhongTheHuyPhuongThucDuyNhat(
                "Không thể hủy liên kết Google vì đây là phương thức đăng nhập duy nhất của tài khoản. "
                "Vui lòng thiết lập mật khẩu cá nhân trước khi hủy liên kết."
            )

        # 2. Xóa liên kết google khỏi auth_identities
        conn.execute("""
            DELETE FROM auth_identities WHERE user_id = ? AND provider = 'google'
        """, (user_id,))

        # 3. Tạo một định danh local mới để không vi phạm ràng buộc NOT NULL UNIQUE của users.google_sub
        local_sub = f"local:unlinked:{secrets.token_hex(12)}"
        conn.execute("""
            UPDATE users SET google_sub = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (local_sub, user_id))

        return True


def danh_dau_token_da_dung(bang_token, token_hash):
    """Đánh dấu token một lần đã được sử dụng."""
    if bang_token not in ("email_verification_tokens", "password_reset_tokens"):
        raise ValueError(f"Tên bảng token không hợp lệ: {bang_token}")
    with giao_dich() as conn:
        conn.execute(f"""
            UPDATE {bang_token} SET used_at = CURRENT_TIMESTAMP
            WHERE token_hash = ? AND used_at IS NULL
        """, (token_hash,))


# Chỉ các cột cần thiết được trả qua API, không lộ user_id/request_hash.
_COT_BAI_LAM = """id, quiz_type, quiz_title, question_count, correct_count,
    incorrect_count, skipped_count, score, started_at, finished_at,
    duration_seconds, created_at"""


class MaNopDaDuocSuDung(ValueError):
    """Cùng mã lần nộp nhưng khác nội dung; không được ghi đè bài cũ."""


def tim_bai_nop(user_id, submission_id):
    with closing(ket_noi()) as conn:
        row = conn.execute("""
            SELECT id, request_hash FROM quiz_attempts
            WHERE user_id = ? AND submission_id = ?
        """, (user_id, submission_id)).fetchone()
        return dict(row) if row else None


def luu_bai_lam(user_id, submission_id, request_hash, bai):
    """Lưu dữ liệu đã được server kiểm tra; trả (attempt_id, có_tạo_mới).

    Khóa ghi và UNIQUE bảo đảm hai request đồng thời không cộng thống kê hai
    lần. Kiểm tra lại mã nộp bên trong chính transaction ghi.
    """
    with giao_dich() as conn:
        cu = conn.execute("""
            SELECT id, request_hash FROM quiz_attempts
            WHERE user_id = ? AND submission_id = ?
        """, (user_id, submission_id)).fetchone()
        if cu:
            if cu["request_hash"] != request_hash:
                raise MaNopDaDuocSuDung()
            return cu["id"], False

        attempt_id = conn.execute("""
            INSERT INTO quiz_attempts (
                user_id, submission_id, request_hash, quiz_type, quiz_title,
                question_count, correct_count, incorrect_count, skipped_count,
                score, started_at, finished_at, duration_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, submission_id, request_hash, bai["quiz_type"], bai["quiz_title"],
              len(bai["answers"]), bai["correct_count"], bai["incorrect_count"],
              bai["skipped_count"], bai["score"], bai["started_at"], bai["finished_at"],
              bai["duration_seconds"])).lastrowid

        for answer in bai["answers"]:
            conn.execute("""
                INSERT INTO quiz_answers (
                    attempt_id, question_order, question_id, sign_code,
                    question_snapshot, options_snapshot, selected_answer,
                    correct_answer, status, marked_for_review
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (attempt_id, answer["question_order"], answer["question_id"], answer["sign_code"],
                  json.dumps(answer["question_snapshot"], ensure_ascii=False),
                  json.dumps(answer["options_snapshot"], ensure_ascii=False),
                  answer["selected_answer"], answer["correct_answer"], answer["status"],
                  int(answer["marked_for_review"])))
            if answer["status"] == "skipped":
                continue
            dung = int(answer["status"] == "correct")
            conn.execute("""
                INSERT INTO sign_review_stats (
                    user_id, sign_code, total_answers, correct_count,
                    incorrect_count, last_answered_at
                ) VALUES (?, ?, 1, ?, ?, ?)
                ON CONFLICT(user_id, sign_code) DO UPDATE SET
                    total_answers = sign_review_stats.total_answers + 1,
                    correct_count = sign_review_stats.correct_count + excluded.correct_count,
                    incorrect_count = sign_review_stats.incorrect_count + excluded.incorrect_count,
                    last_answered_at = MAX(
                        COALESCE(sign_review_stats.last_answered_at, excluded.last_answered_at),
                        excluded.last_answered_at)
            """, (user_id, answer["sign_code"], dung, 1 - dung, bai["finished_at"]))
        # learning_progress cố ý không được cập nhật ở bước này.
        return attempt_id, True


def lich_su_bai_lam(user_id, limit=20, offset=0):
    with closing(ket_noi()) as conn:
        total = conn.execute("SELECT COUNT(*) FROM quiz_attempts WHERE user_id = ?",
                             (user_id,)).fetchone()[0]
        rows = conn.execute(f"""
            SELECT {_COT_BAI_LAM} FROM quiz_attempts WHERE user_id = ?
            ORDER BY finished_at DESC, id DESC LIMIT ? OFFSET ?
        """, (user_id, limit, offset)).fetchall()
        return {"attempts": [dict(row) for row in rows], "total": total,
                "limit": limit, "offset": offset}


def chi_tiet_bai_lam(user_id, attempt_id):
    with closing(ket_noi()) as conn:
        row = conn.execute(f"""
            SELECT {_COT_BAI_LAM} FROM quiz_attempts WHERE id = ? AND user_id = ?
        """, (attempt_id, user_id)).fetchone()
        if row is None:
            return None
        answers = []
        for item in conn.execute("""
            SELECT question_order, question_id, sign_code, question_snapshot,
                   options_snapshot, selected_answer, correct_answer, status, marked_for_review
            FROM quiz_answers WHERE attempt_id = ? ORDER BY question_order
        """, (attempt_id,)):
            answer = dict(item)
            answer["question_snapshot"] = json.loads(answer["question_snapshot"])
            answer["options_snapshot"] = json.loads(answer["options_snapshot"])
            answer["marked_for_review"] = bool(answer["marked_for_review"])
            answers.append(answer)
        return {"attempt": dict(row), "answers": answers}


@contextmanager
def _doc_thong_ke():
    """Các truy vấn cùng API đọc một snapshot; không lấy khóa ghi IMMEDIATE."""
    with closing(ket_noi()) as conn:
        conn.execute("PRAGMA query_only = ON")
        with conn:
            conn.execute("BEGIN")
            yield conn


def thong_ke_tong_quan(user_id):
    # Không JOIN câu trả lời: mỗi bài chỉ đóng góp một lần vào tổng hợp.
    with _doc_thong_ke() as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS completed_attempts,
                   COALESCE(SUM(question_count), 0) AS total_questions,
                   COALESCE(SUM(correct_count + incorrect_count), 0) AS answered_questions,
                   COALESCE(SUM(correct_count), 0) AS correct_answers,
                   COALESCE(SUM(incorrect_count), 0) AS incorrect_answers,
                   COALESCE(SUM(skipped_count), 0) AS skipped_questions,
                   100.0 * SUM(correct_count) / NULLIF(SUM(question_count), 0)
                       AS overall_accuracy_percent,
                   AVG(score) AS average_score_percent,
                   MAX(score) AS best_score_percent,
                   COALESCE(SUM(duration_seconds), 0) AS total_duration_seconds,
                   strftime('%Y-%m-%dT%H:%M:%fZ', MAX(julianday(finished_at)))
                       AS last_attempt_at
            FROM quiz_attempts WHERE user_id = ?
        """, (user_id,)).fetchone()
        return dict(row)


def thong_ke_tien_bo(user_id, bat_dau=None, ket_thuc=None):
    sql = """
        SELECT id AS attempt_id,
               strftime('%Y-%m-%dT%H:%M:%fZ', finished_at) AS finished_at,
               100.0 * correct_count / question_count AS accuracy_percent,
               correct_count, question_count, duration_seconds
        FROM quiz_attempts WHERE user_id = ?
    """
    params = [user_id]
    if bat_dau is not None:
        sql += " AND julianday(finished_at) >= julianday(?)"
        params.append(bat_dau)
    if ket_thuc is not None:
        sql += " AND julianday(finished_at) <= julianday(?)"
        params.append(ket_thuc)
    sql += " ORDER BY julianday(finished_at), id"
    with _doc_thong_ke() as conn:
        return [dict(row) for row in conn.execute(sql, params)]


def thong_ke_loi_sai(user_id):
    """Chỉ dùng answers; kiểm chứng liên kết biển bằng ID và snapshot đã lưu.

    Không cần biển còn trong thư viện hiện tại để đọc lịch sử hợp lệ.
    Không JOIN sign_review_stats vì sẽ cộng hai lần cùng hoạt động.
    """
    with _doc_thong_ke() as conn:
        total = conn.execute("""
            SELECT COUNT(*) FROM quiz_answers q
            JOIN quiz_attempts a ON a.id = q.attempt_id WHERE a.user_id = ?
        """, (user_id,)).fetchone()[0]
        rows = conn.execute("""
            SELECT q.sign_code, COUNT(*) AS question_count,
                   SUM(q.status <> 'skipped') AS answered_count,
                   SUM(q.status = 'correct') AS correct_count,
                   SUM(q.status = 'incorrect') AS incorrect_count,
                   SUM(q.status = 'skipped') AS skipped_count,
                   100.0 * SUM(q.status = 'incorrect') / COUNT(*) AS incorrect_rate_percent,
                   100.0 * SUM(q.status = 'incorrect') / NULLIF(SUM(q.status <> 'skipped'), 0)
                       AS answered_incorrect_rate_percent,
                   strftime('%Y-%m-%dT%H:%M:%fZ', MAX(julianday(a.finished_at))) AS last_seen_at,
                   strftime('%Y-%m-%dT%H:%M:%fZ', MAX(CASE WHEN q.status <> 'skipped'
                       THEN julianday(a.finished_at) END)) AS last_answered_at
            FROM quiz_answers q JOIN quiz_attempts a ON a.id = q.attempt_id
            WHERE a.user_id = ?
              AND q.sign_code IS NOT NULL
              AND json_extract(q.question_snapshot, '$.kieu') IN ('nhin-anh', 'doc-ten')
              AND q.question_id = json_extract(q.question_snapshot, '$.kieu') || ':' || q.sign_code
              AND json_extract(q.question_snapshot, '$.dap_an.ma') = q.sign_code
              AND json_extract(q.options_snapshot, '$[' || q.correct_answer || '].ma') = q.sign_code
            GROUP BY q.sign_code
            ORDER BY incorrect_count DESC, skipped_count DESC, q.sign_code
        """, (user_id,)).fetchall()
        signs = [dict(row) for row in rows]
        mapped = sum(row["question_count"] for row in signs)
        return {"signs": signs, "mapped_questions": mapped, "unmapped_questions": total - mapped}


def tien_do_da_luu(user_id):
    with _doc_thong_ke() as conn:
        return [dict(row) for row in conn.execute("""
            SELECT sign_code, is_learned FROM learning_progress WHERE user_id = ?
        """, (user_id,))]


if __name__ == "__main__":
    khoi_tao_db()


def luu_yeu_cau_otp_reset(user_id, email, otp_hash, expires_at, ip_address=None):
    """Lưu yêu cầu xác thực OTP đặt lại mật khẩu và vô hiệu hóa các OTP chưa xác minh trước đó."""
    email_clean = email.strip().lower()
    with giao_dich() as conn:
        # Vô hiệu hóa mã cũ chưa xác minh để tránh đoán mã cũ
        conn.execute("""
            UPDATE password_reset_otp_requests
            SET attempts_left = 0, expires_at = CURRENT_TIMESTAMP
            WHERE (user_id = ? OR email = ?) AND verified_at IS NULL AND expires_at > CURRENT_TIMESTAMP
        """, (user_id, email_clean))

        cursor = conn.execute("""
            INSERT INTO password_reset_otp_requests (
                user_id, email, otp_hash, attempts_left, expires_at, ip_address, created_at
            ) VALUES (?, ?, ?, 5, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, email_clean, otp_hash, expires_at, ip_address))
        return cursor.lastrowid


def tim_yeu_cau_otp_moi_nhat(email):
    """Lấy yêu cầu xác thực OTP mới nhất theo địa chỉ email."""
    email_clean = email.strip().lower()
    with closing(ket_noi()) as conn:
        row = conn.execute("""
            SELECT id, user_id, email, otp_hash, attempts_left, expires_at,
                   verified_at, reset_grant_hash, grant_expires_at, used_at, ip_address, created_at
            FROM password_reset_otp_requests
            WHERE email = ?
            ORDER BY id DESC LIMIT 1
        """, (email_clean,)).fetchone()
        return dict(row) if row else None


def ghi_nhan_otp_sai(request_id):
    """Trừ 1 lượt thử khi nhập sai OTP (tối đa 5 lần). Trả về số lần còn lại."""
    with giao_dich() as conn:
        conn.execute("""
            UPDATE password_reset_otp_requests
            SET attempts_left = MAX(0, attempts_left - 1)
            WHERE id = ?
        """, (request_id,))
        row = conn.execute("SELECT attempts_left FROM password_reset_otp_requests WHERE id = ?", (request_id,)).fetchone()
        return row["attempts_left"] if row else 0


def xac_nhan_otp_thanh_cong(request_id, reset_grant_hash, grant_expires_at):
    """Đánh dấu OTP đã xác thực thành công và cấp mã reset grant ngắn hạn."""
    with giao_dich() as conn:
        conn.execute("""
            UPDATE password_reset_otp_requests
            SET verified_at = CURRENT_TIMESTAMP,
                reset_grant_hash = ?,
                grant_expires_at = ?
            WHERE id = ?
        """, (reset_grant_hash, grant_expires_at, request_id))


def tim_yeu_cau_theo_reset_grant(reset_grant_hash):
    """Tìm yêu cầu đặt lại mật khẩu theo hash của reset grant."""
    with closing(ket_noi()) as conn:
        row = conn.execute("""
            SELECT id, user_id, email, otp_hash, attempts_left, expires_at,
                   verified_at, reset_grant_hash, grant_expires_at, used_at, ip_address, created_at
            FROM password_reset_otp_requests
            WHERE reset_grant_hash = ?
        """, (reset_grant_hash,)).fetchone()
        return dict(row) if row else None


def dat_lai_mat_khau_bang_otp_grant(user_id, mat_khau_moi_hash, request_id):
    """Đặt lại mật khẩu bằng reset grant đã qua xác thực OTP và thu hồi mọi phiên/yêu cầu cũ."""
    with giao_dich() as conn:
        # 1. Đánh dấu grant này đã sử dụng
        conn.execute("""
            UPDATE password_reset_otp_requests
            SET used_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (request_id,))

        # 2. Vô hiệu hóa tất cả các OTP và token reset còn lại của user
        conn.execute("""
            UPDATE password_reset_otp_requests
            SET used_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND used_at IS NULL
        """, (user_id,))
        conn.execute("""
            UPDATE password_reset_tokens
            SET used_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND used_at IS NULL
        """, (user_id,))

        # 3. Cập nhật mật khẩu băm mới
        conn.execute("""
            INSERT INTO password_credentials (user_id, password_hash, password_updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                password_hash = excluded.password_hash,
                password_updated_at = CURRENT_TIMESTAMP
        """, (user_id, mat_khau_moi_hash))

        # 4. Đảm bảo auth_identities có định danh password
        user = conn.execute("SELECT email FROM users WHERE id = ?", (user_id,)).fetchone()
        email = (user["email"] if user and user["email"] else f"user_{user_id}@local").strip().lower()
        conn.execute("""
            INSERT INTO auth_identities (user_id, provider, provider_subject, created_at, updated_at)
            VALUES (?, 'password', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(provider, provider_subject) DO UPDATE SET
                user_id = excluded.user_id,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, email))

        # 5. Đánh dấu xác minh email thành công và cập nhật thời gian
        conn.execute("""
            UPDATE users SET email_verified = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))


# ==============================================================================
# QUẢN LÝ XÁC THỰC OTP ĐĂNG KÝ VÀ KÍCH HOẠT TÀI KHOẢN (BƯỚC 18.2 / 18.6)
# ==============================================================================

def luu_yeu_cau_otp_xac_minh_email(user_id, email, otp_hash, expires_at, ip_address=None):
    """Lưu yêu cầu OTP xác minh tài khoản đăng ký mới.
    
    Tự động vô hiệu hóa các OTP kích hoạt cũ chưa xác minh của tài khoản này.
    """
    email_clean = email.strip().lower()
    with giao_dich() as conn:
        conn.execute("""
            UPDATE email_verification_otp_requests
            SET used_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND used_at IS NULL
        """, (user_id,))

        cursor = conn.execute("""
            INSERT INTO email_verification_otp_requests (
                user_id, email, otp_hash, attempts_left, expires_at, ip_address, created_at
            ) VALUES (?, ?, ?, 5, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, email_clean, otp_hash, expires_at, ip_address))
        return cursor.lastrowid


def tim_yeu_cau_otp_xac_minh_moi_nhat(email):
    """Lấy yêu cầu xác thực OTP kích hoạt tài khoản mới nhất theo địa chỉ email."""
    email_clean = email.strip().lower()
    with closing(ket_noi()) as conn:
        row = conn.execute("""
            SELECT id, user_id, email, otp_hash, attempts_left, expires_at,
                   verified_at, used_at, ip_address, created_at
            FROM email_verification_otp_requests
            WHERE email = ?
            ORDER BY id DESC LIMIT 1
        """, (email_clean,)).fetchone()
        return dict(row) if row else None


def ghi_nhan_otp_xac_minh_sai(request_id):
    """Trừ 1 lượt thử khi nhập sai OTP kích hoạt (tối đa 5 lần). Trả về số lần còn lại."""
    with giao_dich() as conn:
        conn.execute("""
            UPDATE email_verification_otp_requests
            SET attempts_left = MAX(0, attempts_left - 1)
            WHERE id = ?
        """, (request_id,))
        row = conn.execute("SELECT attempts_left FROM email_verification_otp_requests WHERE id = ?", (request_id,)).fetchone()
        return row["attempts_left"] if row else 0


def xac_nhan_otp_xac_minh_thanh_cong(request_id, user_id):
    """Đánh dấu OTP kích hoạt thành công và đặt email_verified = 1 cho người dùng."""
    with giao_dich() as conn:
        conn.execute("""
            UPDATE email_verification_otp_requests
            SET verified_at = CURRENT_TIMESTAMP,
                used_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (request_id,))

        # Vô hiệu hóa tất cả các OTP và token xác minh cũ của user
        conn.execute("""
            UPDATE email_verification_otp_requests
            SET used_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND used_at IS NULL
        """, (user_id,))
        conn.execute("""
            UPDATE email_verification_tokens
            SET used_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND used_at IS NULL
        """, (user_id,))

        # Kích hoạt tài khoản
        conn.execute("""
            UPDATE users SET email_verified = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))
