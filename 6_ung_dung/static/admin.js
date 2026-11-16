/**
 * BIỂN BÁO AI - ADMIN DASHBOARD CLIENT CONTROLLER (BƯỚC 18.5)
 * Module điều khiển toàn diện giao diện quản trị Admin SaaS
 */

(function () {
    "use strict";

    // Trạng thái ứng dụng
    const state = {
        currentUser: null,
        csrfToken: "",
        mfaStatus: {
            mfa_enabled: false,
            mfa_verified_in_session: false
        },
        currentRoute: "overview",
        theme: localStorage.getItem("bienbao_admin_theme") || "light",
        sidebarCollapsed: localStorage.getItem("bienbao_admin_sidebar") === "collapsed",
        // Bộ nhớ đệm phân trang & bộ lọc
        overviewRange: "30",
        users: { page: 1, search: "", status: "", role: "", totalPages: 1 },
        quiz: { page: 1, search: "", kieu: "", nhom: "", totalPages: 1 },
        signs: { page: 1, search: "", nhom: "", totalPages: 1 },
        surveys: { limit: 15, offset: 0, total: 0 },
        logs: { limit: 20, offset: 0, action: "", total: 0 }
    };

    // =========================================================================
    // 1. TIỆN ÍCH CHUNG & API HELPER
    // =========================================================================

    function showToast(title, message, type = "info", duration = 4000) {
        const container = document.getElementById("toast-container");
        if (!container) return;

        const toast = document.createElement("div");
        toast.className = `toast-item ${type}`;

        const icons = {
            success: "✅",
            error: "❌",
            warning: "⚠️",
            info: "ℹ️"
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || "ℹ️"}</div>
            <div class="toast-content">
                <div class="toast-title">${escapeHtml(title)}</div>
                <div class="toast-msg">${escapeHtml(message)}</div>
            </div>
            <button type="button" class="toast-close">&times;</button>
        `;

        toast.querySelector(".toast-close").addEventListener("click", () => toast.remove());
        container.appendChild(toast);

        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.opacity = "0";
                toast.style.transform = "translateX(100%)";
                setTimeout(() => toast.remove(), 250);
            }
        }, duration);
    }

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function formatDateVN(dateStr) {
        if (!dateStr) return "--";
        try {
            const d = new Date(dateStr.endsWith("Z") ? dateStr : dateStr + "Z");
            return d.toLocaleString("vi-VN", {
                year: "numeric", month: "2-digit", day: "2-digit",
                hour: "2-digit", minute: "2-digit", second: "2-digit"
            });
        } catch {
            return dateStr;
        }
    }

    async function apiCall(url, options = {}) {
        const headers = options.headers || {};
        if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
            options.body = JSON.stringify(options.body);
            headers["Content-Type"] = "application/json";
        }
        if (state.csrfToken && ["POST", "PATCH", "PUT", "DELETE"].includes((options.method || "GET").toUpperCase())) {
            headers["X-CSRF-Token"] = state.csrfToken;
        }

        options.headers = headers;
        options.credentials = "include";

        try {
            const res = await fetch(url, options);
            const data = await res.json().catch(() => ({}));

            if (res.status === 401) {
                if (data.code === "mfa_required") {
                    openMfaGateModal();
                    throw new Error("Yêu cầu xác thực hai yếu tố (2FA).");
                } else if (data.code === "admin_session_expired") {
                    showToast("Phiên làm việc hết hạn", "Phiên quản trị đã hết hạn sau 30 phút không hoạt động. Đang chuyển hướng đăng nhập...", "warning");
                    setTimeout(() => window.location.href = "/login?next=/admin", 1500);
                    throw new Error("Phiên quản trị đã hết hạn.");
                } else {
                    window.location.href = "/login?next=/admin";
                    throw new Error(data.loi || "Yêu cầu đăng nhập.");
                }
            }

            if (res.status === 403) {
                showToast("Từ chối truy cập", data.loi || "Bạn không có quyền thực hiện thao tác này.", "error");
                throw new Error(data.loi || "Không có quyền.");
            }

            if (!res.ok) {
                throw new Error(data.loi || `Yêu cầu thất bại (Mã lỗi ${res.status})`);
            }

            return data;
        } catch (err) {
            console.error(`Lỗi API [${url}]:`, err);
            throw err;
        }
    }

    // =========================================================================
    // 2. KHỞI TẠO ỨNG DỤNG & XÁC THỰC ADMIN
    // =========================================================================

    async function initApp() {
        const loader = document.getElementById("admin-init-loader");
        const layout = document.getElementById("admin-layout");

        try {
            // 1. Kiểm tra phiên đăng nhập hiện tại
            const meRes = await apiCall("/api/me");
            if (!meRes.da_dang_nhap || !meRes.user) {
                window.location.href = "/login?next=/admin";
                return;
            }

            state.currentUser = meRes.user;
            state.csrfToken = meRes.csrf_token || "";

            // 2. Kiểm tra vai trò Admin
            if (state.currentUser.role !== "admin") {
                window.location.href = "/app";
                return;
            }

            // 3. Kiểm tra trạng thái MFA
            const mfaRes = await apiCall("/api/admin/mfa/status");
            state.mfaStatus = mfaRes;

            updateUserInterfaceHeader();

            // Nếu admin đã bật MFA nhưng phiên chưa xác thực OTP
            if (mfaRes.mfa_enabled && !mfaRes.mfa_verified_in_session) {
                if (loader) loader.style.display = "none";
                if (layout) layout.style.display = "flex";
                openMfaGateModal();
                return;
            }

            // Hiển thị giao diện chính
            if (loader) loader.style.display = "none";
            if (layout) layout.style.display = "flex";

            // Hiển thị banner khuyến cáo nếu chưa bật 2FA
            const bannerMfa = document.getElementById("banner-mfa-warning");
            if (bannerMfa) {
                bannerMfa.style.display = mfaRes.mfa_enabled ? "none" : "flex";
            }

            // Thiết lập Theme và Sidebar
            applyTheme(state.theme);
            applySidebarState(state.sidebarCollapsed);

            // Gắn lắng nghe sự kiện
            bindEventListeners();

            // Xử lý Route ban đầu
            handleHashChange();

        } catch (err) {
            console.error("Khởi tạo thất bại:", err);
            if (loader) {
                loader.innerHTML = `
                    <div style="text-align: center; max-width: 420px; padding: 24px;">
                        <h2 style="color: #EF4444; margin-bottom: 12px;">Không thể kết nối Bảng Quản trị</h2>
                        <p style="color: #94A3B8; margin-bottom: 20px;">${escapeHtml(err.message || "Vui lòng đăng nhập bằng tài khoản có quyền Quản trị viên.")}</p>
                        <a href="/login?next=/admin" class="btn btn-primary">Đăng nhập Quản trị viên</a>
                    </div>
                `;
            }
        }
    }

    function updateUserInterfaceHeader() {
        const u = state.currentUser || {};
        const name = u.ten || u.email || "Quản trị viên";
        const initial = (name.charAt(0) || "A").toUpperCase();

        const sAvatar = document.getElementById("sidebar-user-avatar");
        const sName = document.getElementById("sidebar-user-name");
        const sRole = document.getElementById("sidebar-user-role");

        const hAvatar = document.getElementById("header-user-avatar");
        const hName = document.getElementById("header-user-name");

        if (sAvatar) sAvatar.textContent = initial;
        if (sName) sName.textContent = name;
        if (sRole) sRole.textContent = u.role === "admin" ? "Quản trị viên" : "Học viên";

        if (hAvatar) hAvatar.textContent = initial;
        if (hName) hName.textContent = name;
    }

    // =========================================================================
    // 3. ĐIỀU HƯỚNG ROUTING (SPA HASH-BASED)
    // =========================================================================

    const ROUTE_CONFIG = {
        "overview": { title: "Tổng quan hệ thống", breadcrumb: "Bảng quản trị / Tổng quan", load: loadOverviewView },
        "users": { title: "Quản lý Người dùng", breadcrumb: "Bảng quản trị / Người dùng", load: loadUsersView },
        "quiz": { title: "Ngân hàng Câu hỏi Trắc nghiệm", breadcrumb: "Bảng quản trị / Câu hỏi", load: loadQuizView },
        "signs": { title: "Thư viện Biển báo Giao thông", breadcrumb: "Bảng quản trị / Biển báo", load: loadSignsView },
        "surveys": { title: "Khảo sát & Góp ý Người học", breadcrumb: "Bảng quản trị / Khảo sát", load: loadSurveysView },
        "audit-logs": { title: "Nhật ký Hoạt động Quản trị", breadcrumb: "Bảng quản trị / Nhật ký", load: loadAuditLogsView },
        "settings": { title: "Cài đặt Tài khoản Quản trị", breadcrumb: "Bảng quản trị / Cài đặt", load: loadSettingsView }
    };

    function handleHashChange() {
        const hash = window.location.hash.replace("#", "") || "overview";
        const routeKey = ROUTE_CONFIG[hash] ? hash : "overview";
        state.currentRoute = routeKey;

        // Cập nhật Active Link trên Sidebar
        document.querySelectorAll(".sidebar-nav .nav-item").forEach(item => {
            const isMatch = item.getAttribute("data-route") === routeKey;
            item.classList.toggle("active", isMatch);
        });

        // Cập nhật Header
        const cfg = ROUTE_CONFIG[routeKey];
        const pageTitle = document.getElementById("header-page-title");
        const breadcrumb = document.getElementById("header-breadcrumb");
        if (pageTitle) pageTitle.textContent = cfg.title;
        if (breadcrumb) breadcrumb.textContent = cfg.breadcrumb;

        // Ẩn tất cả views và mở view tương ứng
        document.querySelectorAll(".admin-view").forEach(v => v.classList.remove("active"));
        const targetView = document.getElementById(`view-${routeKey}`);
        if (targetView) targetView.classList.add("active");

        // Đóng mobile sidebar drawer nếu đang mở
        closeMobileSidebar();

        // Tải dữ liệu tương ứng
        if (typeof cfg.load === "function") {
            cfg.load();
        }
    }

    // =========================================================================
    // 4. VIEW CONTROLLER: TỔNG QUAN (OVERVIEW & CHARTS)
    // =========================================================================

    async function loadOverviewView() {
        try {
            const res = await apiCall(`/api/admin/overview?range=${encodeURIComponent(state.overviewRange)}`);
            const d = res.data || {};

            // 1. Cập nhật 6 KPI Cards
            const u = d.users || {};
            const q = d.quizzes || {};
            const s = d.surveys || {};

            const elTotalUsers = document.getElementById("kpi-total-users");
            const elActiveUsers = document.getElementById("kpi-active-users");
            const elLockedUsers = document.getElementById("kpi-locked-users");
            if (elTotalUsers) elTotalUsers.textContent = Number(u.total || 0).toLocaleString();
            if (elActiveUsers) elActiveUsers.textContent = `${u.active || 0} hoạt động`;
            if (elLockedUsers) elLockedUsers.textContent = `${u.locked || 0} bị khóa`;

            const elTotalQuizzes = document.getElementById("kpi-total-quizzes");
            const elQuizPart = document.getElementById("kpi-quiz-participants");
            if (elTotalQuizzes) elTotalQuizzes.textContent = Number(q.total_attempts || 0).toLocaleString();
            if (elQuizPart) elQuizPart.textContent = `${q.total_participants || 0} người tham gia`;

            const elAvgScore = document.getElementById("kpi-avg-score");
            const elTotalAns = document.getElementById("kpi-total-answers");
            if (elAvgScore) elAvgScore.textContent = `${(q.average_score || 0).toFixed(1)} / 10`;
            if (elTotalAns) elTotalAns.textContent = `${Number(q.total_questions || 0).toLocaleString()} câu hỏi đã trả lời`;

            const fullCount = s.full_survey?.total_responses || 0;
            const quickCount = s.quick_survey?.total_responses || 0;
            const elTotalSurveys = document.getElementById("kpi-total-surveys");
            const elSurveyBreakdown = document.getElementById("kpi-survey-breakdown");
            if (elTotalSurveys) elTotalSurveys.textContent = Number(fullCount + quickCount).toLocaleString();
            if (elSurveyBreakdown) elSurveyBreakdown.textContent = `${fullCount} đầy đủ | ${quickCount} nhanh`;

            const elBankQ = document.getElementById("kpi-bank-questions");
            if (elBankQ) elBankQ.textContent = Number(q.total_bank_questions || 704).toLocaleString();

            // 2. Vẽ 4 Biểu đồ tương tác bằng Pure Canvas
            const charts = d.charts || {};
            renderDailyQuizzesChart(charts.daily_quizzes || []);
            renderDailyUsersChart(charts.daily_users || []);
            renderScoreDistChart(charts.score_distribution || {});
            renderSurveyRatingsChart(charts.survey_ratings || {});

            // 3. Tải 5 nhật ký gần nhất
            loadRecentLogsTable();

        } catch (err) {
            console.error("Lỗi tải tổng quan:", err);
            showToast("Lỗi dữ liệu", "Không thể tải số liệu thống kê tổng quan.", "error");
        }
    }

    async function loadRecentLogsTable() {
        const tbody = document.getElementById("tbody-overview-recent-logs");
        if (!tbody) return;
        try {
            const res = await apiCall("/api/admin/audit-logs?limit=5");
            const logs = res.logs || [];
            if (logs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" class="text-center text-subtle">Chưa có nhật ký hoạt động nào.</td></tr>`;
                return;
            }

            tbody.innerHTML = logs.map(l => `
                <tr>
                    <td>${formatDateVN(l.created_at)}</td>
                    <td><strong>${escapeHtml(l.actor_email || `ID ${l.actor_user_id}`)}</strong></td>
                    <td><span class="badge-role-admin">${escapeHtml(l.action)}</span></td>
                    <td>${escapeHtml(l.target_type)}: ${escapeHtml(l.target_id || "--")}</td>
                </tr>
            `).join("");
        } catch {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">Lỗi khi tải nhật ký gần đây.</td></tr>`;
        }
    }

    // =========================================================================
    // 5. THƯ VIỆN VẼ BIỂU ĐỒ CANVAS NHẸ & TỰ CHỨA (NO EXTERNAL DEPENDENCY)
    // =========================================================================

    function setupCanvasDPI(canvas) {
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        const ctx = canvas.getContext("2d");
        ctx.scale(dpr, dpr);
        return { ctx, width: rect.width, height: rect.height };
    }

    function renderDailyQuizzesChart(data) {
        const canvas = document.getElementById("chart-daily-quizzes");
        if (!canvas) return;
        const { ctx, width, height } = setupCanvasDPI(canvas);

        ctx.clearRect(0, 0, width, height);
        const padding = { top: 20, right: 20, bottom: 40, left: 45 };
        const chartW = width - padding.left - padding.right;
        const chartH = height - padding.top - padding.bottom;

        if (!data || data.length === 0) {
            ctx.fillStyle = "#94A3B8";
            ctx.font = "13px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("Chưa có lượt bài tập nào trong khoảng thời gian này.", width / 2, height / 2);
            return;
        }

        const maxVal = Math.max(...data.map(d => d.count), 5);

        // Vẽ đường lưới Y
        ctx.strokeStyle = state.theme === "dark" ? "#334155" : "#E2E8F0";
        ctx.lineWidth = 1;
        ctx.fillStyle = "#94A3B8";
        ctx.font = "11px sans-serif";
        ctx.textAlign = "right";

        for (let i = 0; i <= 4; i++) {
            const yVal = Math.round((maxVal / 4) * i);
            const y = padding.top + chartH - (chartH * (i / 4));
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(width - padding.right, y);
            ctx.stroke();
            ctx.fillText(yVal, padding.left - 8, y + 4);
        }

        // Tọa độ các điểm
        const points = data.map((d, idx) => {
            const x = padding.left + (chartW / Math.max(data.length - 1, 1)) * idx;
            const y = padding.top + chartH - (chartH * (d.count / maxVal));
            return { x, y, day: d.day, count: d.count };
        });

        // Vẽ vùng diện tích Gradient
        const grad = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH);
        grad.addColorStop(0, "rgba(37, 99, 235, 0.25)");
        grad.addColorStop(1, "rgba(37, 99, 235, 0.0)");

        ctx.beginPath();
        ctx.moveTo(points[0].x, padding.top + chartH);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.lineTo(points[points.length - 1].x, padding.top + chartH);
        ctx.closePath();
        ctx.fillStyle = grad;
        ctx.fill();

        // Vẽ đường Line
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.strokeStyle = "#2563EB";
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Vẽ các chấm điểm
        ctx.fillStyle = "#FFFFFF";
        points.forEach(p => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
            ctx.fillStyle = "#FFFFFF";
            ctx.fill();
            ctx.strokeStyle = "#2563EB";
            ctx.lineWidth = 2;
            ctx.stroke();
        });

        // Nhãn trục X
        ctx.fillStyle = "#94A3B8";
        ctx.textAlign = "center";
        const step = Math.ceil(data.length / 6);
        points.forEach((p, idx) => {
            if (idx % step === 0 || idx === data.length - 1) {
                const label = p.day ? p.day.substring(5) : "";
                ctx.fillText(label, p.x, height - 12);
            }
        });
    }

    function renderDailyUsersChart(data) {
        const canvas = document.getElementById("chart-daily-users");
        if (!canvas) return;
        const { ctx, width, height } = setupCanvasDPI(canvas);

        ctx.clearRect(0, 0, width, height);
        const padding = { top: 20, right: 20, bottom: 40, left: 45 };
        const chartW = width - padding.left - padding.right;
        const chartH = height - padding.top - padding.bottom;

        if (!data || data.length === 0) {
            ctx.fillStyle = "#94A3B8";
            ctx.font = "13px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("Chưa có đăng ký mới trong khoảng thời gian này.", width / 2, height / 2);
            return;
        }

        const maxVal = Math.max(...data.map(d => d.count), 5);

        // Trục Y
        ctx.strokeStyle = state.theme === "dark" ? "#334155" : "#E2E8F0";
        ctx.fillStyle = "#94A3B8";
        ctx.font = "11px sans-serif";
        ctx.textAlign = "right";

        for (let i = 0; i <= 4; i++) {
            const yVal = Math.round((maxVal / 4) * i);
            const y = padding.top + chartH - (chartH * (i / 4));
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(width - padding.right, y);
            ctx.stroke();
            ctx.fillText(yVal, padding.left - 8, y + 4);
        }

        // Vẽ Bar
        const barWidth = Math.max(6, Math.min(24, (chartW / data.length) * 0.65));
        data.forEach((d, idx) => {
            const x = padding.left + (chartW / data.length) * idx + (chartW / data.length - barWidth) / 2;
            const barH = (chartH * (d.count / maxVal));
            const y = padding.top + chartH - barH;

            ctx.fillStyle = "#10B981";
            ctx.beginPath();
            ctx.roundRect(x, y, barWidth, barH, [4, 4, 0, 0]);
            ctx.fill();

            if (idx % Math.ceil(data.length / 6) === 0 || idx === data.length - 1) {
                ctx.fillStyle = "#94A3B8";
                ctx.textAlign = "center";
                ctx.fillText(d.day ? d.day.substring(5) : "", x + barWidth / 2, height - 12);
            }
        });
    }

    function renderScoreDistChart(dist) {
        const canvas = document.getElementById("chart-score-dist");
        if (!canvas) return;
        const { ctx, width, height } = setupCanvasDPI(canvas);

        ctx.clearRect(0, 0, width, height);
        const padding = { top: 20, right: 20, bottom: 40, left: 45 };
        const chartW = width - padding.left - padding.right;
        const chartH = height - padding.top - padding.bottom;

        const categories = ["0-2", "3-4", "5-6", "7-8", "9-10"];
        const values = categories.map(k => dist[k] || 0);
        const maxVal = Math.max(...values, 5);

        // Trục Y
        ctx.strokeStyle = state.theme === "dark" ? "#334155" : "#E2E8F0";
        ctx.fillStyle = "#94A3B8";
        ctx.font = "11px sans-serif";
        ctx.textAlign = "right";

        for (let i = 0; i <= 4; i++) {
            const yVal = Math.round((maxVal / 4) * i);
            const y = padding.top + chartH - (chartH * (i / 4));
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(width - padding.right, y);
            ctx.stroke();
            ctx.fillText(yVal, padding.left - 8, y + 4);
        }

        const barWidth = Math.min(42, (chartW / categories.length) * 0.55);
        const colors = ["#EF4444", "#F59E0B", "#FBBF24", "#3B82F6", "#10B981"];

        categories.forEach((cat, idx) => {
            const val = values[idx];
            const x = padding.left + (chartW / categories.length) * idx + (chartW / categories.length - barWidth) / 2;
            const barH = (chartH * (val / maxVal));
            const y = padding.top + chartH - barH;

            ctx.fillStyle = colors[idx] || "#2563EB";
            ctx.beginPath();
            ctx.roundRect(x, y, barWidth, barH, [4, 4, 0, 0]);
            ctx.fill();

            // Giá trị trên đầu cột
            if (val > 0) {
                ctx.fillStyle = state.theme === "dark" ? "#F8FAFC" : "#0F172A";
                ctx.font = "bold 11px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(val, x + barWidth / 2, y - 6);
            }

            // Nhãn cột
            ctx.fillStyle = "#94A3B8";
            ctx.font = "11.5px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText(cat + " đ", x + barWidth / 2, height - 12);
        });
    }

    function renderSurveyRatingsChart(ratings) {
        const canvas = document.getElementById("chart-survey-ratings");
        if (!canvas) return;
        const { ctx, width, height } = setupCanvasDPI(canvas);

        ctx.clearRect(0, 0, width, height);
        const padding = { top: 20, right: 20, bottom: 40, left: 45 };
        const chartW = width - padding.left - padding.right;
        const chartH = height - padding.top - padding.bottom;

        const stars = ["1", "2", "3", "4", "5"];
        const values = stars.map(s => ratings[s] || 0);
        const maxVal = Math.max(...values, 5);

        ctx.strokeStyle = state.theme === "dark" ? "#334155" : "#E2E8F0";
        ctx.fillStyle = "#94A3B8";
        ctx.font = "11px sans-serif";
        ctx.textAlign = "right";

        for (let i = 0; i <= 4; i++) {
            const yVal = Math.round((maxVal / 4) * i);
            const y = padding.top + chartH - (chartH * (i / 4));
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(width - padding.right, y);
            ctx.stroke();
            ctx.fillText(yVal, padding.left - 8, y + 4);
        }

        const barWidth = Math.min(38, (chartW / stars.length) * 0.55);
        stars.forEach((star, idx) => {
            const val = values[idx];
            const x = padding.left + (chartW / stars.length) * idx + (chartW / stars.length - barWidth) / 2;
            const barH = (chartH * (val / maxVal));
            const y = padding.top + chartH - barH;

            ctx.fillStyle = "#F59E0B";
            ctx.beginPath();
            ctx.roundRect(x, y, barWidth, barH, [4, 4, 0, 0]);
            ctx.fill();

            if (val > 0) {
                ctx.fillStyle = state.theme === "dark" ? "#F8FAFC" : "#0F172A";
                ctx.font = "bold 11px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(val, x + barWidth / 2, y - 6);
            }

            ctx.fillStyle = "#94A3B8";
            ctx.font = "11.5px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText(`${star} ⭐`, x + barWidth / 2, height - 12);
        });
    }

    // =========================================================================
    // 6. VIEW CONTROLLER: QUẢN LÝ NGƯỜI DÙNG (USERS)
    // =========================================================================

    async function loadUsersView() {
        const tbody = document.getElementById("tbody-users");
        if (!tbody) return;

        tbody.innerHTML = `<tr><td colspan="8" class="text-center">Đang tải danh sách người dùng...</td></tr>`;

        try {
            const params = new URLSearchParams({
                page: state.users.page,
                per_page: 15,
                search: state.users.search,
                status: state.users.status,
                role: state.users.role
            });

            const res = await apiCall(`/api/admin/users?${params.toString()}`);
            const users = res.users || [];
            state.users.totalPages = res.total_pages || 1;

            if (users.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center text-subtle">Không tìm thấy người dùng phù hợp.</td></tr>`;
                renderPagination("users-pagination", state.users.page, state.users.totalPages, (p) => {
                    state.users.page = p;
                    loadUsersView();
                });
                return;
            }

            tbody.innerHTML = users.map(u => {
                const isSelf = u.id === state.currentUser?.id;
                const isLocked = u.status === "locked" || u.status === "suspended";

                return `
                    <tr>
                        <td><strong>#${u.id}</strong></td>
                        <td>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div class="admin-avatar-bubble" style="width: 32px; height: 32px; font-size: 12px;">
                                    ${escapeHtml((u.ten || u.email || "U").charAt(0).toUpperCase())}
                                </div>
                                <div>
                                    <div style="font-weight: 600;">${escapeHtml(u.ten || "Người học")}</div>
                                    <div style="font-size: 12px; color: var(--color-text-muted);">${escapeHtml(u.email || "Chưa có email")}</div>
                                </div>
                            </div>
                        </td>
                        <td>
                            <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                                ${(u.identities || []).map(p => `<span class="provider-badge">${p === "google" ? "Google" : "Password"}</span>`).join("") || '<span class="text-subtle">--</span>'}
                            </div>
                        </td>
                        <td>
                            <span class="${u.role === "admin" ? "badge-role-admin" : "badge-role-user"}">${u.role}</span>
                        </td>
                        <td>
                            <span class="badge-status ${u.status}">${u.status}</span>
                        </td>
                        <td>
                            ${u.email_verified ? '<span style="color: #10B981;">Đã xác minh</span>' : '<span style="color: #94A3B8;">Chưa</span>'}
                        </td>
                        <td>${formatDateVN(u.ngay_tao)}</td>
                        <td class="text-right">
                            <div class="table-actions">
                                <button type="button" class="btn-table-action" onclick="window.adminApp.openUserDetail(${u.id})">Chi tiết</button>
                                <button type="button" class="btn-table-action ${isLocked ? "" : "danger"}" 
                                        ${isSelf ? 'disabled title="Không thể tự khóa tài khoản của chính mình"' : ""}
                                        onclick="window.adminApp.openUserStatusModal(${u.id}, '${u.email || u.ten}', '${u.status}')">
                                    ${isLocked ? "Mở khóa" : "Khóa / Đình chỉ"}
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join("");

            renderPagination("users-pagination", state.users.page, state.users.totalPages, (p) => {
                state.users.page = p;
                loadUsersView();
            });

        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Lỗi khi tải danh sách người dùng.</td></tr>`;
        }
    }

    async function openUserDetail(userId) {
        const modal = document.getElementById("modal-user-detail");
        const body = document.getElementById("modal-user-detail-body");
        if (!modal || !body) return;

        openModal(modal);
        body.innerHTML = `<div class="text-center">Đang tải hồ sơ...</div>`;

        try {
            const res = await apiCall(`/api/admin/users/${userId}`);
            const u = res.user || {};
            const stats = u.quiz_stats || {};

            body.innerHTML = `
                <div style="display: flex; gap: 16px; align-items: center; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--color-border);">
                    <div class="admin-avatar-bubble" style="width: 48px; height: 48px; font-size: 18px;">
                        ${escapeHtml((u.ten || u.email || "U").charAt(0).toUpperCase())}
                    </div>
                    <div>
                        <h4 style="font-size: 16px; margin: 0;">${escapeHtml(u.ten || "Người học")} (ID: #${u.id})</h4>
                        <p style="margin: 2px 0 0; color: var(--color-text-muted); font-size: 13px;">${escapeHtml(u.email || "Chưa có email")}</p>
                    </div>
                </div>

                <div class="profile-details-list">
                    <div class="detail-row">
                        <span class="detail-label">Vai trò:</span>
                        <span class="${u.role === "admin" ? "badge-role-admin" : "badge-role-user"}">${u.role}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Trạng thái:</span>
                        <span class="badge-status ${u.status}">${u.status}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Xác minh email:</span>
                        <strong>${u.email_verified ? "Đã xác minh" : "Chưa xác minh"}</strong>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Ngày tạo tài khoản:</span>
                        <span>${formatDateVN(u.ngay_tao)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Lần đăng nhập cuối:</span>
                        <span>${formatDateVN(u.lan_dang_nhap_cuoi)}</span>
                    </div>
                </div>

                <h4 style="margin: 18px 0 8px; font-size: 14.5px;">Thống kê Làm bài tập</h4>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; background: var(--color-bg-page); padding: 12px; border-radius: 8px;">
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: var(--color-text-muted);">Tổng bài nộp</div>
                        <div style="font-size: 18px; font-weight: 700;">${stats.total_attempts || 0}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: var(--color-text-muted);">Điểm trung bình</div>
                        <div style="font-size: 18px; font-weight: 700; color: #2563EB;">${(stats.average_score || 0).toFixed(1)}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: var(--color-text-muted);">Biển đã học</div>
                        <div style="font-size: 18px; font-weight: 700; color: #10B981;">${u.learned_signs_count || 0}</div>
                    </div>
                </div>
            `;
        } catch (err) {
            body.innerHTML = `<div class="text-danger">Lỗi khi tải thông tin chi tiết: ${escapeHtml(err.message)}</div>`;
        }
    }

    let activeStatusTargetUserId = null;

    function openUserStatusModal(userId, userIdentifier, currentStatus) {
        activeStatusTargetUserId = userId;
        const modal = document.getElementById("modal-user-status");
        const info = document.getElementById("modal-status-user-info");
        const select = document.getElementById("select-new-status");
        const reason = document.getElementById("textarea-status-reason");
        const warning = document.getElementById("modal-status-warning");

        if (!modal || !info || !select || !reason) return;

        info.innerHTML = `Đang cập nhật trạng thái cho người dùng <strong>${escapeHtml(userIdentifier)}</strong> (ID #${userId}).`;
        select.value = currentStatus === "locked" ? "active" : "suspended";
        reason.value = "";
        if (warning) warning.style.display = "none";

        openModal(modal);
    }

    async function submitUserStatusUpdate() {
        if (!activeStatusTargetUserId) return;
        const select = document.getElementById("select-new-status");
        const reasonInput = document.getElementById("textarea-status-reason");
        const warning = document.getElementById("modal-status-warning");

        const newStatus = select.value;
        const reason = (reasonInput.value || "").trim();

        if (reason.length < 3) {
            if (warning) {
                warning.textContent = "Vui lòng nhập lý do tối thiểu 3 ký tự.";
                warning.style.display = "block";
            }
            return;
        }

        try {
            const btn = document.getElementById("btn-confirm-status-update");
            if (btn) btn.disabled = true;

            const res = await apiCall(`/api/admin/users/${activeStatusTargetUserId}/status`, {
                method: "PATCH",
                body: { status: newStatus, reason: reason }
            });

            showToast("Thành công", res.thong_bao || "Đã cập nhật trạng thái người dùng.", "success");
            closeModal();
            loadUsersView();
        } catch (err) {
            if (warning) {
                warning.textContent = err.message || "Không thể cập nhật trạng thái.";
                warning.style.display = "block";
            }
        } finally {
            const btn = document.getElementById("btn-confirm-status-update");
            if (btn) btn.disabled = false;
        }
    }

    // =========================================================================
    // 7. VIEW CONTROLLER: NGÂN HÀNG CÂU HỎI (QUIZ)
    // =========================================================================

    async function loadQuizView() {
        const tbody = document.getElementById("tbody-quiz-questions");
        if (!tbody) return;

        tbody.innerHTML = `<tr><td colspan="7" class="text-center">Đang nạp ngân hàng câu hỏi...</td></tr>`;

        try {
            const params = new URLSearchParams({
                page: state.quiz.page,
                per_page: 15,
                search: state.quiz.search,
                kieu: state.quiz.kieu,
                nhom: state.quiz.nhom
            });

            const res = await apiCall(`/api/admin/quiz/questions?${params.toString()}`);
            const questions = res.questions || [];
            state.quiz.totalPages = res.total_pages || 1;

            if (questions.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center text-subtle">Không tìm thấy câu hỏi phù hợp.</td></tr>`;
                renderPagination("quiz-pagination", state.quiz.page, state.quiz.totalPages, (p) => {
                    state.quiz.page = p;
                    loadQuizView();
                });
                return;
            }

            tbody.innerHTML = questions.map(q => {
                const isActive = q.is_active === 1;
                return `
                    <tr>
                        <td>
                            <img src="${escapeHtml(q.sign_image || '/anh/icon_bien_bao.png')}" alt="Biển" style="width: 40px; height: 40px; object-fit: contain; background: #F1F5F9; border-radius: 4px; padding: 2px;">
                        </td>
                        <td><strong>${escapeHtml(q.sign_code)}</strong></td>
                        <td>
                            <div style="font-weight: 600;">${escapeHtml(q.sign_name)}</div>
                            <div style="font-size: 11px; color: var(--color-text-muted);">${escapeHtml(q.sign_group)}</div>
                        </td>
                        <td>
                            <span class="provider-badge">${q.kieu === "nhin-anh" ? "Nhìn ảnh" : "Đọc tên"}</span>
                        </td>
                        <td>
                            <div>${escapeHtml(q.prompt)}</div>
                            ${q.is_customized ? '<span style="font-size: 11px; color: #2563EB; font-weight: 600;">★ Đã tùy chỉnh</span>' : ""}
                        </td>
                        <td>
                            <span class="badge-status ${isActive ? 'active' : 'suspended'}">${isActive ? 'Đang dùng' : 'Đã ẩn'}</span>
                        </td>
                        <td class="text-right">
                            <button type="button" class="btn-table-action" onclick="window.adminApp.openEditQuestion('${escapeHtml(q.question_id)}')">Tùy chỉnh</button>
                        </td>
                    </tr>
                `;
            }).join("");

            renderPagination("quiz-pagination", state.quiz.page, state.quiz.totalPages, (p) => {
                state.quiz.page = p;
                loadQuizView();
            });

        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Lỗi khi tải câu hỏi trắc nghiệm.</td></tr>`;
        }
    }

    let activeEditingQuestionId = null;

    async function openEditQuestion(questionId) {
        activeEditingQuestionId = questionId;
        const modal = document.getElementById("modal-edit-question");
        const preview = document.getElementById("modal-question-preview");
        const chkActive = document.getElementById("check-question-active");
        const inputPrompt = document.getElementById("input-custom-prompt");
        const txtExp = document.getElementById("textarea-custom-explanation");

        if (!modal) return;
        openModal(modal);

        try {
            const res = await apiCall(`/api/admin/quiz/questions/${encodeURIComponent(questionId)}`);
            const q = res;
            const sign = q.sign || {};

            if (preview) {
                preview.innerHTML = `
                    <div style="display: flex; gap: 14px; align-items: center; margin-bottom: 12px;">
                        <img src="${escapeHtml(sign.anh || sign.anh_url || '/anh/icon_bien_bao.png')}" style="width: 52px; height: 52px; object-fit: contain; background: #F1F5F9; border-radius: 6px;">
                        <div>
                            <div style="font-weight: 700; font-size: 15px;">${escapeHtml(sign.ma)}: ${escapeHtml(sign.ten)}</div>
                            <div style="font-size: 12px; color: var(--color-text-muted);">Dạng: ${q.kieu === "nhin-anh" ? "Nhìn ảnh đoán tên biển" : "Đọc tên chọn biển"}</div>
                        </div>
                    </div>
                `;
            }

            if (chkActive) chkActive.checked = q.is_active === 1;
            if (inputPrompt) inputPrompt.value = q.custom_prompt || "";
            if (txtExp) txtExp.value = q.custom_explanation || "";

        } catch (err) {
            showToast("Lỗi", "Không thể tải chi tiết câu hỏi.", "error");
            closeModal();
        }
    }

    async function saveQuestionEdit() {
        if (!activeEditingQuestionId) return;
        const chkActive = document.getElementById("check-question-active");
        const inputPrompt = document.getElementById("input-custom-prompt");
        const txtExp = document.getElementById("textarea-custom-explanation");

        try {
            const res = await apiCall(`/api/admin/quiz/questions/${encodeURIComponent(activeEditingQuestionId)}`, {
                method: "PATCH",
                body: {
                    is_active: chkActive ? chkActive.checked : true,
                    custom_prompt: inputPrompt ? inputPrompt.value : null,
                    custom_explanation: txtExp ? txtExp.value : null
                }
            });

            showToast("Thành công", res.thong_bao || "Đã lưu tùy chỉnh câu hỏi.", "success");
            closeModal();
            loadQuizView();
        } catch (err) {
            showToast("Lỗi cập nhật", err.message || "Không thể lưu câu hỏi.", "error");
        }
    }

    // =========================================================================
    // 8. VIEW CONTROLLER: THƯ VIỆN BIỂN BÁO (SIGNS)
    // =========================================================================

    async function loadSignsView() {
        const container = document.getElementById("signs-grid-container");
        if (!container) return;

        container.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 40px;">Đang tải danh mục biển báo...</div>`;

        try {
            const params = new URLSearchParams({
                page: state.signs.page,
                per_page: 18,
                search: state.signs.search,
                nhom: state.signs.nhom
            });

            const res = await apiCall(`/api/admin/signs?${params.toString()}`);
            const signs = res.signs || [];
            state.signs.totalPages = res.total_pages || 1;

            if (signs.length === 0) {
                container.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--color-text-muted); padding: 40px;">Không có biển báo nào phù hợp bộ lọc.</div>`;
                renderPagination("signs-pagination", state.signs.page, state.signs.totalPages, (p) => {
                    state.signs.page = p;
                    loadSignsView();
                });
                return;
            }

            container.innerHTML = signs.map(s => {
                const isActive = s.is_active === 1;
                return `
                    <div class="sign-grid-card">
                        <div>
                            <div class="sign-card-top">
                                <img src="${escapeHtml(s.anh_url || '/anh/icon_bien_bao.png')}" alt="${escapeHtml(s.ma)}" class="sign-card-img">
                                <div class="sign-card-meta">
                                    <span class="sign-code-badge">${escapeHtml(s.ma)}</span>
                                    <h4 class="sign-name-title">${escapeHtml(s.ten)}</h4>
                                </div>
                            </div>
                            <div class="sign-card-pills">
                                <span class="provider-badge">${escapeHtml(s.nhom)}</span>
                                ${s.is_ai_supported ? '<span class="pill-ai-badge">AI YOLO/CNN</span>' : ""}
                                <span class="badge-status ${isActive ? 'active' : 'suspended'}">${isActive ? 'Hiển thị' : 'Đã ẩn'}</span>
                            </div>
                            <p style="font-size: 12.5px; color: var(--color-text-muted); line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                                ${escapeHtml(s.y_nghia || "Chưa có mô tả ý nghĩa.")}
                            </p>
                        </div>
                        <div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid var(--color-border); text-align: right;">
                            <button type="button" class="btn-table-action" onclick="window.adminApp.openEditSign('${escapeHtml(s.ma)}')">Tùy chỉnh</button>
                        </div>
                    </div>
                `;
            }).join("");

            renderPagination("signs-pagination", state.signs.page, state.signs.totalPages, (p) => {
                state.signs.page = p;
                loadSignsView();
            });

        } catch (err) {
            container.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: #EF4444; padding: 40px;">Lỗi khi tải thư viện biển báo.</div>`;
        }
    }

    let activeEditingSignCode = null;

    async function openEditSign(signCode) {
        activeEditingSignCode = signCode;
        const modal = document.getElementById("modal-edit-sign");
        const preview = document.getElementById("modal-sign-preview");
        const chkActive = document.getElementById("check-sign-active");
        const inputName = document.getElementById("input-custom-sign-name");
        const txtMeaning = document.getElementById("textarea-custom-sign-meaning");
        const txtNote = document.getElementById("textarea-custom-sign-note");

        if (!modal) return;
        openModal(modal);

        try {
            const res = await apiCall(`/api/admin/signs/${encodeURIComponent(signCode)}`);
            const s = res.sign || {};
            const meta = s.override_metadata || {};

            if (preview) {
                preview.innerHTML = `
                    <div style="display: flex; gap: 14px; align-items: center; margin-bottom: 12px;">
                        <img src="${escapeHtml(s.anh || s.anh_url || '/anh/icon_bien_bao.png')}" style="width: 58px; height: 58px; object-fit: contain; background: #F1F5F9; border-radius: 6px; padding: 4px;">
                        <div>
                            <div style="font-weight: 700; font-size: 16px;">${escapeHtml(s.ma)}: ${escapeHtml(s.ten)}</div>
                            <div style="font-size: 12px; color: var(--color-text-muted);">Quy chuẩn: ${escapeHtml(s.can_cu || "QCVN 41:2024/BGTVT")} | ${s.is_ai_supported ? "★ Có trong Model AI" : "Bổ sung"}</div>
                        </div>
                    </div>
                `;
            }

            if (chkActive) chkActive.checked = meta.is_active !== 0;
            if (inputName) inputName.value = meta.custom_ten || s.ten || "";
            if (txtMeaning) txtMeaning.value = meta.custom_y_nghia || s.y_nghia || "";
            if (txtNote) txtNote.value = meta.custom_ghi_chu || "";

        } catch (err) {
            showToast("Lỗi", "Không thể tải chi tiết biển báo.", "error");
            closeModal();
        }
    }

    async function saveSignEdit() {
        if (!activeEditingSignCode) return;
        const chkActive = document.getElementById("check-sign-active");
        const inputName = document.getElementById("input-custom-sign-name");
        const txtMeaning = document.getElementById("textarea-custom-sign-meaning");
        const txtNote = document.getElementById("textarea-custom-sign-note");

        try {
            const res = await apiCall(`/api/admin/signs/${encodeURIComponent(activeEditingSignCode)}`, {
                method: "PATCH",
                body: {
                    is_active: chkActive ? chkActive.checked : true,
                    custom_ten: inputName ? inputName.value : null,
                    custom_y_nghia: txtMeaning ? txtMeaning.value : null,
                    custom_ghi_chu: txtNote ? txtNote.value : null
                }
            });

            showToast("Thành công", res.thong_bao || "Đã lưu tùy chỉnh biển báo.", "success");
            closeModal();
            loadSignsView();
        } catch (err) {
            showToast("Lỗi cập nhật", err.message || "Không thể lưu thông tin biển báo.", "error");
        }
    }

    // =========================================================================
    // 9. VIEW CONTROLLER: KHẢO SÁT & GÓP Ý (SURVEYS)
    // =========================================================================

    async function loadSurveysView() {
        try {
            // 1. Tải tổng hợp
            const summaryRes = await apiCall("/api/admin/surveys/summary");
            const full = summaryRes.full_survey || {};
            const quick = summaryRes.quick_survey || {};

            const elFullCount = document.getElementById("survey-full-count");
            const elFullAvg = document.getElementById("survey-full-avg");
            if (elFullCount) elFullCount.textContent = `${full.total_participants || 0} lượt phản hồi`;
            if (elFullAvg) elFullAvg.textContent = (full.average_rating || 0).toFixed(1);

            const elQuickCount = document.getElementById("survey-quick-count");
            const elQuickAvg = document.getElementById("survey-quick-avg");
            if (elQuickCount) elQuickCount.textContent = `${quick.total || 0} lượt phản hồi`;
            if (elQuickAvg) elQuickAvg.textContent = (quick.average_rating || 0).toFixed(1);

            // Likert categories breakdown
            const likertList = document.getElementById("likert-categories-list");
            if (likertList && Array.isArray(full.categories)) {
                likertList.innerHTML = full.categories.map(c => `
                    <div class="likert-cat-row">
                        <span>${escapeHtml(c.title || c.category)}</span>
                        <strong>${(c.average || 0).toFixed(1)} / 5</strong>
                    </div>
                `).join("");
            }

            // Quick survey tags
            const tagsWrap = document.getElementById("quick-survey-tags-wrap");
            if (tagsWrap && quick.tags) {
                const tagEntries = Object.entries(quick.tags);
                if (tagEntries.length === 0) {
                    tagsWrap.innerHTML = `<span class="text-subtle">Chưa có nhãn phản hồi nào.</span>`;
                } else {
                    tagsWrap.innerHTML = tagEntries.map(([t, count]) => `
                        <span class="survey-tag-chip">${escapeHtml(t)} (${count})</span>
                    `).join("");
                }
            }

            // 2. Tải danh sách góp ý (Feedbacks)
            loadSurveyFeedbacks();

        } catch (err) {
            console.error("Lỗi tải khảo sát:", err);
            showToast("Lỗi khảo sát", "Không thể tải số liệu khảo sát người học.", "error");
        }
    }

    async function loadSurveyFeedbacks() {
        const tbody = document.getElementById("tbody-survey-feedbacks");
        if (!tbody) return;

        tbody.innerHTML = `<tr><td colspan="5" class="text-center">Đang tải góp ý...</td></tr>`;

        try {
            const res = await apiCall(`/api/admin/surveys/feedback?limit=${state.surveys.limit}&offset=${state.surveys.offset}`);
            const feedbacks = res.feedbacks || [];
            state.surveys.total = res.total || 0;

            if (feedbacks.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" class="text-center text-subtle">Chưa có ý kiến góp ý nào từ học viên.</td></tr>`;
                return;
            }

            tbody.innerHTML = feedbacks.map(f => {
                const isQuick = f.source === "quick_survey";
                const tags = Array.isArray(f.tags) ? f.tags : [];

                return `
                    <tr>
                        <td>${formatDateVN(f.updated_at)}</td>
                        <td>
                            <span class="provider-badge">${isQuick ? "Khảo sát nhanh" : "Khảo sát đầy đủ"}</span>
                        </td>
                        <td>
                            ${f.rating ? `<strong>${f.rating} ⭐</strong>` : '<span class="text-subtle">--</span>'}
                        </td>
                        <td>
                            <div style="line-height: 1.5;">${escapeHtml(f.feedback)}</div>
                        </td>
                        <td>
                            <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                                ${tags.map(t => `<span class="badge-neutral">${escapeHtml(t)}</span>`).join("") || '<span class="text-subtle">--</span>'}
                            </div>
                        </td>
                    </tr>
                `;
            }).join("");

            const totalPages = Math.ceil(state.surveys.total / state.surveys.limit) || 1;
            const currentPage = Math.floor(state.surveys.offset / state.surveys.limit) + 1;
            renderPagination("feedbacks-pagination", currentPage, totalPages, (p) => {
                state.surveys.offset = (p - 1) * state.surveys.limit;
                loadSurveyFeedbacks();
            });

        } catch {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Lỗi khi tải danh sách góp ý.</td></tr>`;
        }
    }

    // =========================================================================
    // 10. VIEW CONTROLLER: NHẬT KÝ HOẠT ĐỘNG (AUDIT LOGS)
    // =========================================================================

    async function loadAuditLogsView() {
        const tbody = document.getElementById("tbody-audit-logs");
        if (!tbody) return;

        tbody.innerHTML = `<tr><td colspan="6" class="text-center">Đang tải nhật ký hoạt động...</td></tr>`;

        try {
            const params = new URLSearchParams({
                limit: state.logs.limit,
                offset: state.logs.offset,
                action: state.logs.action
            });

            const res = await apiCall(`/api/admin/audit-logs?${params.toString()}`);
            const logs = res.logs || [];
            state.logs.total = res.total || 0;

            if (logs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center text-subtle">Chưa có bản ghi nhật ký nào.</td></tr>`;
                return;
            }

            tbody.innerHTML = logs.map(l => {
                const detailsJson = JSON.stringify(l.details || {}, null, 2);
                return `
                    <tr>
                        <td>${formatDateVN(l.created_at)}</td>
                        <td><strong>${escapeHtml(l.actor_email || `ID #${l.actor_user_id}`)}</strong></td>
                        <td><span class="badge-role-admin">${escapeHtml(l.action)}</span></td>
                        <td>${escapeHtml(l.target_type)}: ${escapeHtml(l.target_id || "--")}</td>
                        <td>
                            <button type="button" class="btn-table-action" onclick="window.adminApp.openLogDetail('${escapeHtml(encodeURIComponent(detailsJson))}')">
                                Xem chi tiết JSON
                            </button>
                        </td>
                        <td><code style="font-size: 11.5px;">${escapeHtml(l.ip_address || "127.0.0.1")}</code></td>
                    </tr>
                `;
            }).join("");

            const totalPages = Math.ceil(state.logs.total / state.logs.limit) || 1;
            const currentPage = Math.floor(state.logs.offset / state.logs.limit) + 1;
            renderPagination("logs-pagination", currentPage, totalPages, (p) => {
                state.logs.offset = (p - 1) * state.logs.limit;
                loadAuditLogsView();
            });

        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Lỗi khi tải nhật ký hoạt động.</td></tr>`;
        }
    }

    function openLogDetail(encodedJson) {
        const modal = document.getElementById("modal-log-detail");
        const codeBox = document.getElementById("modal-log-json-content");
        if (!modal || !codeBox) return;

        try {
            const parsed = decodeURIComponent(encodedJson);
            codeBox.textContent = parsed;
        } catch {
            codeBox.textContent = encodedJson;
        }

        openModal(modal);
    }

    // =========================================================================
    // 11. VIEW CONTROLLER: CÀI ĐẶT TÀI KHOẢN (SETTINGS & MFA)
    // =========================================================================

    async function loadSettingsView() {
        const u = state.currentUser || {};
        const elName = document.getElementById("settings-user-name");
        const elEmail = document.getElementById("settings-user-email");
        const elProviders = document.getElementById("settings-user-providers");
        const elBadge = document.getElementById("settings-mfa-badge");

        if (elName) elName.textContent = u.ten || "Quản trị viên";
        if (elEmail) elEmail.textContent = u.email || "Chưa có email";
        if (elProviders) elProviders.textContent = (u.identities || ["password"]).join(", ");

        try {
            const mfaRes = await apiCall("/api/admin/mfa/status");
            state.mfaStatus = mfaRes;
            if (elBadge) {
                if (mfaRes.mfa_enabled) {
                    elBadge.className = "mfa-badge enabled";
                    elBadge.textContent = "🟢 Đã kích hoạt bảo vệ 2FA";
                } else {
                    elBadge.className = "mfa-badge disabled";
                    elBadge.textContent = "⚠️ Chưa kích hoạt 2FA";
                }
            }
        } catch {
            if (elBadge) elBadge.textContent = "Không thể kiểm tra 2FA";
        }
    }

    async function openMfaSetupModal() {
        const modal = document.getElementById("modal-setup-mfa");
        const secretText = document.getElementById("mfa-secret-text");
        const backupList = document.getElementById("mfa-backup-codes-list");
        const inputCode = document.getElementById("input-mfa-setup-code");

        if (!modal) return;
        openModal(modal);

        if (secretText) secretText.textContent = "Đang tạo mã bí mật...";
        if (backupList) backupList.innerHTML = "Đang tạo mã dự phòng...";
        if (inputCode) inputCode.value = "";

        try {
            const res = await apiCall("/api/admin/mfa/setup", { method: "POST" });
            if (secretText) secretText.textContent = res.secret || "LỖI_TẠO_SECRET";

            if (backupList && Array.isArray(res.backup_codes)) {
                backupList.innerHTML = res.backup_codes.map(c => `
                    <div class="backup-code-item">${escapeHtml(c)}</div>
                `).join("");
            }
        } catch (err) {
            showToast("Lỗi khởi tạo 2FA", err.message || "Không thể tạo mã bí mật.", "error");
            closeModal();
        }
    }

    async function confirmMfaSetup() {
        const inputCode = document.getElementById("input-mfa-setup-code");
        const code = (inputCode?.value || "").trim();

        if (!code || code.length < 6) {
            showToast("Mã không hợp lệ", "Vui lòng nhập đủ 6 chữ số từ ứng dụng Authenticator.", "warning");
            return;
        }

        try {
            const res = await apiCall("/api/admin/mfa/verify", {
                method: "POST",
                body: { code: code }
            });

            showToast("Kích hoạt 2FA Thành công", res.thong_bao || "Tài khoản của bạn đã được bảo vệ bởi 2 lớp.", "success");
            closeModal();
            loadSettingsView();

            const bannerMfa = document.getElementById("banner-mfa-warning");
            if (bannerMfa) bannerMfa.style.display = "none";

        } catch (err) {
            showToast("Xác thực thất bại", err.message || "Mã OTP không chính xác.", "error");
        }
    }

    function openMfaGateModal() {
        const modal = document.getElementById("modal-mfa-gate");
        const input = document.getElementById("input-mfa-gate-code");
        const errBox = document.getElementById("mfa-gate-error");

        if (!modal) return;
        openModal(modal);
        if (input) {
            input.value = "";
            input.focus();
        }
        if (errBox) errBox.style.display = "none";
    }

    async function submitMfaGate() {
        const input = document.getElementById("input-mfa-gate-code");
        const errBox = document.getElementById("mfa-gate-error");
        const code = (input?.value || "").trim();

        if (!code) {
            if (errBox) {
                errBox.textContent = "Vui lòng nhập mã OTP 6 số hoặc mã backup 8 ký tự.";
                errBox.style.display = "block";
            }
            return;
        }

        try {
            const btn = document.getElementById("btn-submit-mfa-gate");
            if (btn) btn.disabled = true;

            const res = await apiCall("/api/admin/mfa/verify", {
                method: "POST",
                body: { code: code }
            });

            showToast("Xác thực thành công", res.thong_bao || "Chào mừng bạn trở lại Bảng Quản trị!", "success");
            closeModal();
            state.mfaStatus.mfa_verified_in_session = true;

            // Nạp view hiện tại
            handleHashChange();

        } catch (err) {
            if (errBox) {
                errBox.textContent = err.message || "Mã OTP không chính xác hoặc đã hết hạn.";
                errBox.style.display = "block";
            }
        } finally {
            const btn = document.getElementById("btn-submit-mfa-gate");
            if (btn) btn.disabled = false;
        }
    }

    async function handleChangePassword(e) {
        e.preventDefault();
        const curPwd = document.getElementById("pwd-current")?.value || "";
        const newPwd = document.getElementById("pwd-new")?.value || "";
        const cnfPwd = document.getElementById("pwd-confirm")?.value || "";

        if (newPwd !== cnfPwd) {
            showToast("Lỗi", "Mật khẩu mới và xác nhận mật khẩu không khớp nhau.", "warning");
            return;
        }

        try {
            const btn = document.getElementById("btn-submit-change-pwd");
            if (btn) btn.disabled = true;

            const res = await apiCall("/api/auth/change-password", {
                method: "POST",
                body: {
                    mat_khau_cu: curPwd,
                    mat_khau_moi: newPwd,
                    xac_nhan_mat_khau: cnfPwd
                }
            });

            showToast("Thành công", res.thong_diep || "Đã cập nhật mật khẩu mới an toàn.", "success");
            document.getElementById("form-change-password")?.reset();

        } catch (err) {
            showToast("Đổi mật khẩu thất bại", err.message || "Vui lòng kiểm tra lại mật khẩu hiện tại.", "error");
        } finally {
            const btn = document.getElementById("btn-submit-change-pwd");
            if (btn) btn.disabled = false;
        }
    }

    async function handleLogout() {
        if (!confirm("Bạn có chắc chắn muốn đăng xuất khỏi Bảng Quản trị?")) return;
        try {
            await apiCall("/auth/logout", { method: "POST" });
            window.location.href = "/login";
        } catch {
            window.location.href = "/login";
        }
    }

    // =========================================================================
    // 12. QUẢN LÝ MODALS & GIAO DIỆN
    // =========================================================================

    function openModal(modalEl) {
        const backdrop = document.getElementById("modal-backdrop");
        if (!backdrop || !modalEl) return;

        backdrop.querySelectorAll(".modal-dialog").forEach(d => d.style.display = "none");
        backdrop.style.display = "flex";
        modalEl.style.display = "flex";
    }

    function closeModal() {
        const backdrop = document.getElementById("modal-backdrop");
        if (backdrop) backdrop.style.display = "none";
    }

    function renderPagination(containerId, currentPage, totalPages, onPageClick) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (totalPages <= 1) {
            container.innerHTML = `<span class="text-subtle">Trang 1 / 1</span>`;
            return;
        }

        let html = `
            <div class="pagination-info">Trang <strong>${currentPage}</strong> / ${totalPages}</div>
            <div class="pagination-controls">
                <button type="button" class="btn-page" ${currentPage <= 1 ? "disabled" : ""} data-p="${currentPage - 1}">&larr; Trước</button>
        `;

        for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
            html += `<button type="button" class="btn-page ${i === currentPage ? "active" : ""}" data-p="${i}">${i}</button>`;
        }

        html += `
                <button type="button" class="btn-page" ${currentPage >= totalPages ? "disabled" : ""} data-p="${currentPage + 1}">Sau &rarr;</button>
            </div>
        `;

        container.innerHTML = html;
        container.querySelectorAll(".btn-page").forEach(btn => {
            btn.addEventListener("click", () => {
                const p = parseInt(btn.getAttribute("data-p"), 10);
                if (p && p !== currentPage && typeof onPageClick === "function") {
                    onPageClick(p);
                }
            });
        });
    }

    function applyTheme(theme) {
        state.theme = theme;
        document.body.classList.toggle("dark-mode", theme === "dark");
        localStorage.setItem("bienbao_admin_theme", theme);
    }

    function toggleTheme() {
        applyTheme(state.theme === "dark" ? "light" : "dark");
        // Vẽ lại biểu đồ khi đổi màu nền
        if (state.currentRoute === "overview") {
            loadOverviewView();
        }
    }

    function applySidebarState(isCollapsed) {
        state.sidebarCollapsed = isCollapsed;
        const layout = document.getElementById("admin-layout");
        if (layout) {
            layout.classList.toggle("sidebar-collapsed", isCollapsed);
        }
        localStorage.setItem("bienbao_admin_sidebar", isCollapsed ? "collapsed" : "expanded");
    }

    function toggleSidebar() {
        if (window.innerWidth <= 1024) {
            const layout = document.getElementById("admin-layout");
            if (layout) layout.classList.toggle("sidebar-mobile-open");
        } else {
            applySidebarState(!state.sidebarCollapsed);
        }
    }

    function closeMobileSidebar() {
        const layout = document.getElementById("admin-layout");
        if (layout) layout.classList.remove("sidebar-mobile-open");
    }

    // =========================================================================
    // 13. GẮN SỰ KIỆN (EVENT LISTENERS)
    // =========================================================================

    function bindEventListeners() {
        window.addEventListener("hashchange", handleHashChange);

        // Sidebar toggle & mobile drawer
        document.getElementById("btn-toggle-sidebar")?.addEventListener("click", toggleSidebar);
        document.getElementById("btn-sidebar-close")?.addEventListener("click", closeMobileSidebar);
        document.getElementById("sidebar-backdrop")?.addEventListener("click", closeMobileSidebar);

        // Nút theme & refresh
        document.getElementById("btn-theme-toggle")?.addEventListener("click", toggleTheme);
        document.getElementById("btn-refresh-data")?.addEventListener("click", () => {
            showToast("Đang làm mới", "Đang tải lại dữ liệu từ cơ sở dữ liệu...", "info");
            handleHashChange();
        });

        // Nút đăng xuất
        document.getElementById("btn-sidebar-logout")?.addEventListener("click", handleLogout);
        document.getElementById("btn-settings-logout")?.addEventListener("click", handleLogout);

        // Bộ lọc thời gian Overview
        document.querySelectorAll("#time-filter-buttons .btn-time-filter").forEach(btn => {
            btn.addEventListener("click", () => {
                document.querySelectorAll("#time-filter-buttons .btn-time-filter").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                state.overviewRange = btn.getAttribute("data-range") || "30";
                loadOverviewView();
            });
        });

        // Bộ lọc Người dùng
        let userSearchTimer;
        document.getElementById("users-search-input")?.addEventListener("input", (e) => {
            clearTimeout(userSearchTimer);
            userSearchTimer = setTimeout(() => {
                state.users.search = e.target.value.trim();
                state.users.page = 1;
                loadUsersView();
            }, 350);
        });

        document.getElementById("users-filter-status")?.addEventListener("change", (e) => {
            state.users.status = e.target.value;
            state.users.page = 1;
            loadUsersView();
        });

        document.getElementById("users-filter-role")?.addEventListener("change", (e) => {
            state.users.role = e.target.value;
            state.users.page = 1;
            loadUsersView();
        });

        document.getElementById("btn-users-reset-filter")?.addEventListener("click", () => {
            document.getElementById("users-search-input").value = "";
            document.getElementById("users-filter-status").value = "";
            document.getElementById("users-filter-role").value = "";
            state.users = { page: 1, search: "", status: "", role: "", totalPages: 1 };
            loadUsersView();
        });

        // Bộ lọc Câu hỏi
        let quizSearchTimer;
        document.getElementById("quiz-search-input")?.addEventListener("input", (e) => {
            clearTimeout(quizSearchTimer);
            quizSearchTimer = setTimeout(() => {
                state.quiz.search = e.target.value.trim();
                state.quiz.page = 1;
                loadQuizView();
            }, 350);
        });

        document.getElementById("quiz-filter-kieu")?.addEventListener("change", (e) => {
            state.quiz.kieu = e.target.value;
            state.quiz.page = 1;
            loadQuizView();
        });

        document.getElementById("quiz-filter-nhom")?.addEventListener("change", (e) => {
            state.quiz.nhom = e.target.value;
            state.quiz.page = 1;
            loadQuizView();
        });

        document.getElementById("btn-quiz-reset-filter")?.addEventListener("click", () => {
            document.getElementById("quiz-search-input").value = "";
            document.getElementById("quiz-filter-kieu").value = "";
            document.getElementById("quiz-filter-nhom").value = "";
            state.quiz = { page: 1, search: "", kieu: "", nhom: "", totalPages: 1 };
            loadQuizView();
        });

        // Bộ lọc Biển báo
        let signSearchTimer;
        document.getElementById("signs-search-input")?.addEventListener("input", (e) => {
            clearTimeout(signSearchTimer);
            signSearchTimer = setTimeout(() => {
                state.signs.search = e.target.value.trim();
                state.signs.page = 1;
                loadSignsView();
            }, 350);
        });

        document.getElementById("signs-filter-nhom")?.addEventListener("change", (e) => {
            state.signs.nhom = e.target.value;
            state.signs.page = 1;
            loadSignsView();
        });

        document.getElementById("btn-signs-reset-filter")?.addEventListener("click", () => {
            document.getElementById("signs-search-input").value = "";
            document.getElementById("signs-filter-nhom").value = "";
            state.signs = { page: 1, search: "", nhom: "", totalPages: 1 };
            loadSignsView();
        });

        // Bộ lọc Audit Log
        document.getElementById("logs-filter-action")?.addEventListener("change", (e) => {
            state.logs.action = e.target.value;
            state.logs.offset = 0;
            loadAuditLogsView();
        });

        document.getElementById("btn-logs-reset-filter")?.addEventListener("click", () => {
            document.getElementById("logs-filter-action").value = "";
            state.logs = { limit: 20, offset: 0, action: "", total: 0 };
            loadAuditLogsView();
        });

        // Đóng modals
        document.querySelectorAll("[data-close-modal]").forEach(btn => {
            btn.addEventListener("click", closeModal);
        });

        // Submit các hành động modal
        document.getElementById("btn-confirm-status-update")?.addEventListener("click", submitUserStatusUpdate);
        document.getElementById("btn-save-question-edit")?.addEventListener("click", saveQuestionEdit);
        document.getElementById("btn-save-sign-edit")?.addEventListener("click", saveSignEdit);

        // 2FA Setup
        document.getElementById("btn-open-mfa-setup")?.addEventListener("click", openMfaSetupModal);
        document.getElementById("btn-confirm-mfa-setup")?.addEventListener("click", confirmMfaSetup);
        document.getElementById("btn-copy-mfa-secret")?.addEventListener("click", () => {
            const text = document.getElementById("mfa-secret-text")?.textContent || "";
            navigator.clipboard.writeText(text).then(() => {
                showToast("Đã sao chép", "Khóa bí mật 2FA đã được lưu vào clipboard.", "success");
            });
        });

        // MFA Gate Submit
        document.getElementById("btn-submit-mfa-gate")?.addEventListener("click", submitMfaGate);
        document.getElementById("input-mfa-gate-code")?.addEventListener("keydown", (e) => {
            if (e.key === "Enter") submitMfaGate();
        });

        // Form đổi mật khẩu
        document.getElementById("form-change-password")?.addEventListener("submit", handleChangePassword);
    }

    // Expose public API cho các onclick handlers trong HTML template
    window.adminApp = {
        openUserDetail,
        openUserStatusModal,
        openEditQuestion,
        openEditSign,
        openLogDetail
    };

    // Khởi chạy ứng dụng khi DOM sẵn sàng
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initApp);
    } else {
        initApp();
    }
})();
