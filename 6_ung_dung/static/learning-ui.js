"use strict";

// Trang #/thong-ke hiện có. Chỉ đọc API; không đọc/ghi kho học tập cục bộ.
(() => {
  let current = null;
  const number = (value, digits = 0) => value == null ? "–" : Number(value).toLocaleString("vi-VN", {
    minimumFractionDigits: digits, maximumFractionDigits: digits
  });
  const percent = value => value == null ? "–" : number(value, 1) + "%";
  const date = value => {
    if (!value) return "–";
    // API lịch sử cũ trả timestamp SQLite không có hậu tố; quy ước lưu là UTC.
    const normalized = /(?:Z|[+-]\d\d:\d\d)$/i.test(value) ? value : value.replace(" ", "T") + "Z";
    const parsed = new Date(normalized);
    return Number.isNaN(+parsed) ? "–" : parsed.toLocaleString("vi-VN", {
      timeZone: "Asia/Ho_Chi_Minh", day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit"
    });
  };
  const duration = value => {
    if (value == null) return "–";
    const seconds = Math.max(0, Math.round(value));
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  };
  const groupCode = code => code.startsWith("DP") ? "p" : code[0]?.toLowerCase();
  const quizTypes = { "tong-hop": "Tổng hợp", nhom: "Theo nhóm biển", hang: "Theo hạng bằng",
    "bien-don": "Một biển báo", "on-sai": "Ôn câu sai" };

  // Cận dưới Wilson 95%: lỗi lặp lại có trọng số hơn một quan sát đơn lẻ.
  function reviewPriority(sign) {
    const n = sign.question_count, p = sign.incorrect_count / n, z2 = 1.96 ** 2;
    return (p + z2 / (2 * n) - 1.96 * Math.sqrt((p * (1 - p) + z2 / (4 * n)) / n)) / (1 + z2 / n);
  }

  window.dongThongKe = () => {
    if (current) { current.controller.abort(); current.observer?.disconnect(); }
    current = null;
  };

  window.hienThiThongKe = ({ main, ic, esc, S }) => {
    window.dongThongKe();
    const state = { controller: new AbortController(), period: "30d", trends: new Map(), pending: new Map(),
      details: new Map(), detailId: null, history: null, expanded: false, mistakes: null, progress: null };
    current = state;
    const alive = () => current === state && !state.controller.signal.aborted;
    const heading = `<header class="dau-trang tk-heading"><div><h1>${ic("chart")}Thống kê học tập</h1>
      <p>Theo dõi kết quả luyện tập và sự tiến bộ của bạn.</p></div>
      <a class="nut chinh" href="#/bai-tap">${ic("target")}Luyện tập ngay</a></header>`;
    main.innerHTML = `<div class="tk-page">${heading}<div id="tk-body" aria-live="polite"></div></div>`;
    const root = main.querySelector(".tk-page");
    const find = selector => root.querySelector(selector);
    const empty = (icon, title, message, action = "") => `<div class="tk-empty">${ic(icon)}
      <b>${esc(title)}</b><p>${esc(message)}</p>${action}</div>`;
    const exercise = `<a class="nut" href="#/bai-tap">${ic("target")}Làm bài tập</a>`;
    const loading = () => `<div class="tk-loading" role="status"><span class="tk-spinner" aria-hidden="true"></span>Đang tải dữ liệu…</div>`;
    const retry = (message, action) => `<div class="tk-error" role="alert">${ic("alert")}<div><b>Chưa tải được dữ liệu</b>
      <p>${esc(message)}</p><button class="nut" type="button" data-tk-action="${action}">${ic("refresh")}Thử lại</button></div></div>`;
    const login = () => {
      if (!alive()) return;
      state.controller.abort();
      state.observer?.disconnect();
      state.details.clear(); state.trends.clear(); state.history = state.mistakes = state.progress = null;
      find("#tk-body").innerHTML = `<section class="the tk-login">${empty("user", "Kết quả học tập của bạn",
        "Đăng nhập bằng Google để theo dõi kết quả học tập trên tài khoản của bạn.",
        '<a class="nut chinh" href="/auth/google">Đăng nhập bằng Google</a>')}</section>`;
    };

    function api(url) {
      if (!state.pending.has(url)) {
        const promise = requestApi(url).finally(() => state.pending.delete(url));
        state.pending.set(url, promise);
      }
      return state.pending.get(url);
    }
    async function requestApi(url) {
      const controller = new AbortController();
      const abort = () => controller.abort();
      state.controller.signal.addEventListener("abort", abort, { once: true });
      const timeout = setTimeout(abort, 15000);
      try {
        const response = await fetch(url, { credentials: "same-origin", cache: "no-store", signal: controller.signal });
        const data = await response.json().catch(() => null);
        if (!alive()) throw new DOMException("Đã rời trang thống kê", "AbortError");
        if (response.status === 401) { login(); throw new DOMException("Cần đăng nhập", "AbortError"); }
        if (response.status === 403) {
          state.observer?.disconnect();
          state.details.clear(); state.trends.clear(); state.history = state.mistakes = state.progress = null;
          find("#tk-body").innerHTML = `<section class="the">${retry("Bạn chưa được phép xem dữ liệu này. Hãy kiểm tra tài khoản và thử lại.", "reload")}</section>`;
          state.controller.abort();
          throw new DOMException("Không có quyền truy cập", "AbortError");
        }
        if (!response.ok) {
          const message = response.status === 404 ? "Không tìm thấy dữ liệu hoặc API. Hãy kiểm tra Flask đã chạy phiên bản mới."
            : response.status >= 500 ? "Máy chủ chưa đọc được dữ liệu. Hãy thử lại sau."
            : "Yêu cầu chưa được chấp nhận. Hãy thử lại.";
          throw new Error(`${message} (HTTP ${response.status})`);
        }
        if (!data || typeof data !== "object") throw new Error("Phản hồi từ máy chủ không hợp lệ.");
        return data;
      } catch (error) {
        if (!alive()) throw error;
        if (error.name === "AbortError") throw new Error("Kết nối quá thời gian chờ. Hãy thử lại.");
        if (error instanceof TypeError) throw new Error("Không kết nối được máy chủ. Hãy kiểm tra kết nối và thử lại.");
        throw error;
      } finally {
        clearTimeout(timeout);
        state.controller.signal.removeEventListener("abort", abort);
      }
    }

    function shell(overview) {
      state.overview = overview;
      const card = (icon, title, value, description, id = "") => `<article class="the tk-card" ${id ? `id="${id}"` : ""}>
        <div class="tk-card-top"><span>${title}</span><span class="tk-icon">${ic(icon)}</span></div>
        <strong>${value}</strong><small>${description}</small></article>`;
      find("#tk-body").innerHTML = `<div class="tk-source">${ic("check-circle")}Kết quả đã lưu trên tài khoản
        <span>${overview.last_attempt_at ? `Bài gần nhất: ${esc(date(overview.last_attempt_at))}` : "Chưa có bài đã lưu"}</span></div>
        <div class="tk-cards">
          ${card("target", "Bài đã hoàn thành", number(overview.completed_attempts), "Bài đã nộp và lưu thành công")}
          ${card("percent", "Tỷ lệ trả lời đúng", percent(overview.overall_accuracy_percent), `${number(overview.correct_answers)} đúng / ${number(overview.total_questions)} câu hỏi`)}
          ${card("chart", "Điểm trung bình", overview.average_score_percent == null ? "–" : `${number(overview.average_score_percent / 10, 1)}<span>/10</span>`, "Trung bình các bài · làm tròn 1 chữ số")}
          ${card("refresh", "Nội dung cần ôn", "–", "Đang tải số biển có câu trả lời sai", "tk-review-count")}
        </div>
        <div class="tk-grid">
          <section class="the tk-trend"><div class="tk-section-head"><div><h2>Tiến bộ qua các bài luyện tập</h2><p>Mỗi điểm là một bài đã hoàn thành.</p></div>
            <div class="nhom-nut tk-periods" role="group" aria-label="Khoảng thời gian biểu đồ">${[["7d", "7 ngày"], ["30d", "30 ngày"], ["all", "Tất cả"]].map(([key, label]) =>
              `<button type="button" data-tk-action="period" data-period="${key}" aria-pressed="${key === state.period}">${label}</button>`).join("")}</div></div>
            <div id="tk-trend-data" aria-live="polite">${loading()}</div></section>
          <section class="the tk-groups"><div class="tk-section-head"><div><h2>Kết quả theo nhóm biển báo</h2><p>Tỷ lệ đúng trên tổng lượt xuất hiện trong câu hỏi.</p></div></div>
            <div id="tk-group-data">${loading()}</div></section>
        </div>
        <section class="the"><div class="tk-section-head"><div><h2>Biển báo cần ôn tập</h2><p>Ưu tiên lỗi lặp lại, có xét tỷ lệ sai và số lượt xuất hiện.</p></div><span class="tk-tag">Tối đa 5 biển</span></div>
          <div id="tk-review-data">${loading()}</div></section>
        <section class="the"><div class="tk-section-head"><div><h2>Lịch sử luyện tập</h2><p>Bài mới nhất hiển thị trước · Giờ Việt Nam.</p></div><span class="tk-tag" id="tk-history-total">Đang tải…</span></div>
          <div id="tk-history-data">${loading()}</div></section>
        <footer class="tk-notes"><p>${ic("info")}Tỷ lệ đúng = tổng câu đúng / tổng câu hỏi, gồm cả câu bỏ qua. Điểm trung bình = trung bình điểm từng bài trên thang 10.</p>
          <p id="tk-progress-note">Tiến độ học lý thuyết chưa có chức năng đồng bộ lên tài khoản. Không suy ra biển đã học từ câu trả lời đúng.</p></footer>
        <dialog class="tk-dialog" id="tk-detail" aria-labelledby="tk-detail-title"><div id="tk-detail-content"></div></dialog>`;
      find("#tk-detail").onclick = event => { if (event.target === find("#tk-detail")) event.target.close(); };
      find("#tk-detail").onclose = () => { state.detailId = null; };
      let chartWidth = find("#tk-trend-data").clientWidth;
      state.observer = new ResizeObserver(() => {
        if (!alive()) return;
        const width = find("#tk-trend-data").clientWidth;
        const data = state.trends.get(state.period);
        if (width !== chartWidth && data && !find("#tk-trend-data .tk-loading")) {
          find("#tk-trend-data").innerHTML = chart(data.attempts);
        }
        chartWidth = width;
      });
      state.observer.observe(find(".tk-trend"));
    }

    function chart(attempts) {
      if (!attempts.length) return empty("chart", "Chưa có bài trong khoảng thời gian này",
        "Hoàn thành một bài luyện tập để bắt đầu theo dõi tiến bộ.", exercise);
      const W = Math.max(300, find("#tk-trend-data").clientWidth, attempts.length * 24 + 60), H = 260, L = 46, R = 20, T = 24, B = 38;
      const x = i => attempts.length === 1 ? (W + L - R) / 2 : L + (W - L - R) * i / (attempts.length - 1);
      const y = value => T + (H - T - B) * (1 - value / 100);
      const path = attempts.map((item, i) => `${i ? "L" : "M"}${x(i).toFixed(2)},${y(item.accuracy_percent).toFixed(2)}`).join(" ");
      const labelStep = Math.max(1, Math.ceil((attempts.length - 1) / 5));
      return `<div class="tk-chart-wrap"><div class="tk-chart-scroll"><svg class="tk-chart" style="width:${W}px" viewBox="0 0 ${W} ${H}" role="group" aria-label="Biểu đồ tỷ lệ đúng từng bài, từ 0 đến 100 phần trăm">
        <defs>
          <linearGradient id="tk-chart-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#2563EB" stop-opacity="0.28"/>
            <stop offset="100%" stop-color="#2563EB" stop-opacity="0.01"/>
          </linearGradient>
        </defs>
        ${[0, 25, 50, 75, 100].map(v => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/><text x="${L - 10}" y="${y(v) + 4}" text-anchor="end">${v}%</text>`).join("")}
        ${attempts.length > 1 ? `<path d="${path} L${x(attempts.length - 1)},${y(0)} L${x(0)},${y(0)} Z" class="tk-chart-area" fill="url(#tk-chart-grad)"/>` : ""}
        <path d="${path}" class="tk-chart-line"/>
        ${attempts.map((item, i) => {
          const tooltip = `${date(item.finished_at)} · ${item.correct_count}/${item.question_count} câu đúng · ${percent(item.accuracy_percent)}`;
          return `${attempts.length === 1 ? `<circle cx="${x(i)}" cy="${y(item.accuracy_percent)}" r="12" class="tk-chart-pulse"/>` : ""}
            <circle cx="${x(i)}" cy="${y(item.accuracy_percent)}" r="${attempts.length === 1 ? 7 : 5}" tabindex="0" role="button" data-tk-point="${i}" aria-label="${esc(tooltip)}"><title>${esc(tooltip)}</title></circle>
            ${i % labelStep === 0 || i === attempts.length - 1 ? `<text x="${x(i)}" y="${H - 12}" text-anchor="middle">Bài ${i + 1}</text>` : ""}`;
        }).join("")}</svg></div><div class="tk-tooltip" role="status" hidden></div></div>
        <p class="tk-chart-caption">${attempts.length === 1 ? '1 bài luyện tập · Hoàn thành thêm bài tập để theo dõi xu hướng tiến bộ.' : `${number(attempts.length)} bài luyện tập · Chạm hoặc trỏ vào một điểm để xem kết quả.`}</p>`;
    }

    let trendRequest = 0;
    async function loadTrend() {
      const period = state.period, requestId = ++trendRequest;
      find("#tk-trend-data").innerHTML = loading();
      root.querySelectorAll("[data-period]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.period === period)));
      try {
        if (!state.trends.has(period)) {
          const data = await api("/api/learning/trend?period=" + period);
          if (!Array.isArray(data.attempts) || data.attempts.some(item => !Number.isInteger(item.correct_count))) {
            throw new Error("API tiến bộ chưa cung cấp đầy đủ số câu đúng. Hãy khởi động lại Flask rồi thử lại.");
          }
          state.trends.set(period, data);
        }
        if (alive() && requestId === trendRequest) find("#tk-trend-data").innerHTML = chart(state.trends.get(period).attempts);
      } catch (error) {
        if (alive() && requestId === trendRequest) find("#tk-trend-data").innerHTML = retry(error.message, "trend");
      }
    }

    function drawGroups() {
      if (!state.mistakes || !state.progress) return;
      const groups = state.progress.groups.map(group => ({ ...group, questions: 0, answered: 0, correct: 0, skipped: 0 }));
      let unmapped = state.mistakes.unmapped_questions;
      for (const item of state.mistakes.signs) {
        const sign = S.theoMa[item.sign_code];
        const group = sign && (groups.find(g => g.group_code === groupCode(sign.ma)) || groups.find(g => g.group_code === "other"));
        if (!group) { unmapped += item.question_count; continue; }
        group.questions += item.question_count; group.answered += item.answered_count;
        group.correct += item.correct_count; group.skipped += item.skipped_count;
      }
      find("#tk-group-data").innerHTML = `<div class="tk-group-list">${groups.map(group => {
        const accuracy = group.questions ? 100 * group.correct / group.questions : null;
        const colorClass = accuracy == null ? "" : accuracy >= 80 ? "cao" : accuracy >= 50 ? "trung-binh" : "thap";
        return `<div class="tk-group"><div><b>${esc(group.group_name)}</b><strong class="${colorClass}">${percent(accuracy)}</strong></div>
          <p>${number(group.answered)} lượt trả lời${group.skipped ? ` · ${number(group.skipped)} bỏ qua` : ""}${!group.questions ? " · Chưa có dữ liệu" : ""}</p>
          <div class="tk-progress ${colorClass}" role="meter" aria-label="${esc(group.group_name)}: ${accuracy == null ? "chưa có dữ liệu" : percent(accuracy)}" aria-valuemin="0" aria-valuemax="100" ${accuracy == null ? "" : `aria-valuenow="${accuracy}"`}><span style="width:${accuracy ?? 0}%"></span></div></div>`;
      }).join("")}</div><p class="tk-small-note">Lượt trả lời không gồm bỏ qua. Tỷ lệ đúng vẫn tính trên tất cả câu hỏi.${unmapped ? ` ${number(unmapped)} câu chưa ánh xạ được vào nhóm hiện tại.` : ""}</p>`;
    }

    function safeImage(url) {
      // Chỉ dùng đường dẫn ảnh cùng website, kể cả ảnh trong snapshot cũ.
      if (typeof url !== "string" || !/^\/(?!\/)/.test(url)) return null;
      try {
        const parsed = new URL(url, location.origin);
        return parsed.origin === location.origin ? parsed.pathname + parsed.search : null;
      } catch { return null; }
    }
    function signImage(sign) {
      const url = safeImage(sign?.anh);
      return url ? `<img src="${esc(url)}" alt="${esc(sign.ten || sign.ma)}" loading="lazy">` : `<span class="nhan-ma">${esc(sign?.ma || "Không có ảnh")}</span>`;
    }
    function drawReview() {
      const wrong = state.mistakes.signs.filter(item => item.incorrect_count > 0);
      const candidates = wrong.filter(item => S.theoMa[item.sign_code]).sort((a, b) =>
        reviewPriority(b) - reviewPriority(a) || b.incorrect_count - a.incorrect_count || a.sign_code.localeCompare(b.sign_code));
      
      const unmapped = state.overview?.incorrect_answers > 0 && wrong.length === 0;
      if (unmapped) {
        find("#tk-review-count strong").textContent = "Chưa đủ dữ liệu";
        find("#tk-review-count strong").title = "Các câu trả lời sai chưa ánh xạ được mã biển trong thư viện";
        find("#tk-review-count small").textContent = "Câu sai chưa ánh xạ được mã biển tương ứng";
      } else {
        find("#tk-review-count strong").textContent = number(wrong.length);
        find("#tk-review-count strong").removeAttribute("title");
        find("#tk-review-count small").textContent = wrong.length ? "Mã biển có ít nhất một câu trả lời sai" : "Chưa ghi nhận câu trả lời sai";
      }

      find("#tk-review-data").innerHTML = candidates.length ? `<div class="tk-review-list">${candidates.slice(0, 5).map(item => {
        const sign = S.theoMa[item.sign_code];
        return `<article class="tk-review-item"><div class="tk-sign-image">${signImage(sign)}</div><div class="tk-review-info"><span class="tk-sign-code">${esc(sign.ma)}</span>
          <h3>${esc(sign.ten)}</h3><p><span>${number(item.incorrect_count)} lần sai</span> · ${number(item.correct_count)} lần đúng</p>
          <small>${percent(item.incorrect_rate_percent)} sai / ${number(item.question_count)} lượt xuất hiện${item.skipped_count ? ` · ${number(item.skipped_count)} bỏ qua` : ""}</small></div>
          <a class="nut" href="#/hoc/${encodeURIComponent(sign.ma)}">Xem biển báo${ic("arrow-right")}</a></article>`;
      }).join("")}</div>${wrong.length > candidates.length ? '<p class="tk-small-note">Một số mã biển trong lịch sử không còn trong thư viện hiện tại.</p>' : ""}`
        : empty("check-circle", wrong.length ? "Chưa có biển tương ứng trong thư viện" : "Chưa ghi nhận biển trả lời sai",
          wrong.length ? "Bạn vẫn có thể xem câu hỏi đã lưu trong lịch sử luyện tập." : "Các biển có câu trả lời sai sẽ xuất hiện ở đây để bạn dễ ôn lại.");
    }
    async function loadMistakes() {
      find("#tk-review-data").innerHTML = loading();
      try {
        state.mistakes = await api("/api/learning/mistakes");
        if (alive()) { drawReview(); drawGroups(); }
      } catch (error) {
        if (alive()) {
          find("#tk-review-data").innerHTML = retry(error.message, "mistakes");
          find("#tk-review-count small").textContent = "Chưa tải được dữ liệu · thử lại bên dưới";
          find("#tk-group-data").innerHTML = retry(error.message, "mistakes");
        }
      }
    }
    async function loadProgress() {
      try {
        state.progress = await api("/api/learning/progress");
        if (alive()) {
          find("#tk-progress-note").textContent = state.progress.message + " Kết quả theo nhóm ở trên chỉ phản ánh bài tập.";
          drawGroups();
        }
      } catch (error) { if (alive()) find("#tk-group-data").innerHTML = retry(error.message, "progress"); }
    }

    function drawHistory() {
      const history = state.history;
      // Không dùng chuỗi timestamp để so sánh thứ tự giữa các định dạng UTC.
      const timestamp = value => Date.parse(/(?:Z|[+-]\d\d:\d\d)$/i.test(value) ? value : value.replace(" ", "T") + "Z");
      const attempts = [...history.attempts].sort((a, b) => timestamp(b.finished_at) - timestamp(a.finished_at) || b.id - a.id);
      find("#tk-history-total").textContent = `${number(history.total)} bài đã lưu`;
      find("#tk-history-data").innerHTML = attempts.length ? `<div class="tk-table-wrap"><table class="bang tk-table"><thead><tr>
        <th scope="col">Ngày làm bài</th><th scope="col">Loại bài tập</th><th scope="col">Số câu đúng</th><th scope="col">Tỷ lệ đúng</th><th scope="col">Thời gian</th><th scope="col"><span class="tk-sr-only">Chi tiết</span></th></tr></thead><tbody>
        ${attempts.map(item => {
          const rate = 100 * item.correct_count / item.question_count;
          const scoreClass = rate >= 80 ? "cao" : rate >= 50 ? "trung-binh" : "thap";
          return `<tr><td data-label="Ngày làm bài"><time>${esc(date(item.finished_at))}</time></td><td data-label="Loại bài tập"><b>${esc(quizTypes[item.quiz_type] || item.quiz_type)}</b><small>${esc(item.quiz_title)}</small></td>
          <td data-label="Số câu đúng">${number(item.correct_count)}/${number(item.question_count)} câu</td><td data-label="Tỷ lệ đúng"><span class="tk-score ${scoreClass}">${percent(rate)}</span></td>
          <td data-label="Thời gian">${duration(item.duration_seconds)}</td><td data-label="Thao tác"><button class="nut tk-detail-button" type="button" data-tk-action="detail" data-id="${esc(item.id)}" aria-label="Xem chi tiết bài ${esc(item.id)}">Xem chi tiết${ic("chevron-right")}</button></td></tr>`;
        }).join("")}
        </tbody></table></div>${history.attempts.length < history.total ? `<div class="tk-history-more"><button class="nut" type="button" data-tk-action="history-more">${state.expanded ? "Xem thêm" : "Xem tất cả"}${ic("chevron-down")}</button>
          <span>Đang hiển thị ${number(history.attempts.length)}/${number(history.total)} bài</span></div>` : ""}`
        : empty("calendar", "Chưa có lịch sử luyện tập", "Bài tập sẽ xuất hiện khi bạn nộp và lưu thành công trên tài khoản.", exercise);
    }
    async function loadHistory(more = false) {
      const previous = state.history;
      const offset = more && state.expanded ? previous.attempts.length : 0;
      if (more) state.expanded = true;
      find("#tk-history-data").innerHTML = loading();
      try {
        const data = await api(`/api/quiz/history?limit=${state.expanded ? 20 : 5}&offset=${offset}`);
        if (!alive()) return;
        const unique = new Map([...(offset ? previous.attempts : []), ...data.attempts].map(item => [item.id, item]));
        state.history = { ...data, attempts: [...unique.values()] };
        drawHistory();
      } catch (error) {
        if (alive()) {
          state.history = previous;
          find("#tk-history-data").innerHTML = retry(error.message, more ? "history-more" : "history");
        }
      }
    }

    function detailMarkup(data) {
      const item = data.attempt;
      return `<div class="tk-dialog-head"><div><span class="tk-sign-code">Bài luyện tập đã lưu</span><h2 id="tk-detail-title">${esc(item.quiz_title)}</h2><p>${esc(date(item.finished_at))} · ${esc(quizTypes[item.quiz_type] || item.quiz_type)}</p></div>
        <button class="quay-lai" type="button" data-tk-action="close-detail" aria-label="Đóng chi tiết">${ic("x")}</button></div>
        <div class="tk-detail-summary"><b>${number(item.correct_count)}/${number(item.question_count)} câu đúng · ${percent(100 * item.correct_count / item.question_count)}</b>
          <span>${number(item.incorrect_count)} sai · ${number(item.skipped_count)} bỏ qua · ${duration(item.duration_seconds)}</span></div>
        <ol class="tk-answer-list">${data.answers.map(answer => {
          const snapshot = answer.question_snapshot, target = snapshot.dap_an;
          const label = { correct: "Đúng", incorrect: "Sai", skipped: "Bỏ qua" }[answer.status] || answer.status;
          return `<li class="tk-answer"><div class="tk-answer-head"><b>Câu ${number(answer.question_order)}</b><span class="tk-answer-status ${esc(answer.status)}">${esc(label)}</span>${answer.marked_for_review ? `<span class="tk-tag">${ic("bookmark")}Đã đánh dấu</span>` : ""}</div>
            <h3>${esc(snapshot.noi_dung || "Câu hỏi đã lưu")}</h3>
            ${snapshot.kieu === "nhin-anh" ? `<div class="tk-answer-image">${signImage(target)}</div>` : ""}
            <ul class="tk-answer-options">${answer.options_snapshot.map((option, index) => `<li class="${index === answer.correct_answer ? "tk-option-correct" : index === answer.selected_answer ? "tk-option-wrong" : ""}">
              ${snapshot.kieu === "doc-ten" ? `<div class="tk-option-image">${signImage(option)}</div>` : ""}
              <span><b>${String.fromCharCode(65 + index)}.</b> ${esc(option.ten || option.ma)}</span>
              ${index === answer.selected_answer ? '<small>Bạn đã chọn</small>' : ""}${index === answer.correct_answer ? '<small>Đáp án đúng</small>' : ""}</li>`).join("")}</ul>
            ${answer.status === "skipped" ? '<p class="tk-small-note">Bạn đã bỏ qua câu này.</p>' : ""}
            ${target?.y_nghia ? `<div class="tk-explanation"><b>Giải thích · ${esc(target.ma)}</b><p>${esc(target.y_nghia)}</p></div>` : '<p class="tk-small-note">Bản lưu chưa có nội dung giải thích.</p>'}</li>`;
        }).join("")}</ol>`;
    }
    async function loadDetail(id) {
      if (state.detailId === id && find("#tk-detail").open) return;
      state.detailId = id;
      const dialog = find("#tk-detail");
      find("#tk-detail-content").innerHTML = `<div class="tk-dialog-head"><h2 id="tk-detail-title">Chi tiết bài làm</h2><button class="quay-lai" type="button" data-tk-action="close-detail" aria-label="Đóng chi tiết">${ic("x")}</button></div>${loading()}`;
      if (!dialog.open) dialog.showModal();
      try {
        if (!state.details.has(id)) state.details.set(id, await api("/api/quiz/history/" + id));
        if (alive() && state.detailId === id) find("#tk-detail-content").innerHTML = detailMarkup(state.details.get(id));
      } catch (error) {
        if (alive() && state.detailId === id) {
          find("#tk-detail-content").innerHTML = `<div class="tk-dialog-head"><h2 id="tk-detail-title">Chi tiết bài làm</h2><button class="quay-lai" type="button" data-tk-action="close-detail" aria-label="Đóng chi tiết">${ic("x")}</button></div>${retry(error.message, "detail-retry")}`;
        }
      }
    }

    function tooltip(event) {
      const point = event.target.closest?.("[data-tk-point]");
      const box = find(".tk-tooltip");
      if (!point || !box) return;
      box.textContent = point.getAttribute("aria-label");
      box.hidden = false;
    }
    root.onpointerover = tooltip;
    root.addEventListener("focusin", tooltip);
    root.onpointerout = event => { if (event.target.matches?.("[data-tk-point]")) { const box = find(".tk-tooltip"); if (box) box.hidden = true; } };
    root.addEventListener("focusout", root.onpointerout);
    root.onclick = event => {
      const button = event.target.closest("[data-tk-action]");
      if (!button) { tooltip(event); return; }
      const action = button.dataset.tkAction;
      if (action === "reload") { window.hienThiThongKe({ main, ic, esc, S }); return; }
      if (action === "close-detail") { find("#tk-detail").close(); return; }
      if (!alive()) return;
      if (action === "period" && state.period !== button.dataset.period) { state.period = button.dataset.period; loadTrend(); }
      if (action === "trend") loadTrend();
      if (action === "mistakes") loadMistakes();
      if (action === "progress") loadProgress();
      if (action === "history" || action === "history-more") loadHistory(action === "history-more");
      if (action === "detail") loadDetail(button.dataset.id);
      if (action === "detail-retry") { const id = state.detailId; state.detailId = null; loadDetail(id); }
    };
    async function start() {
      find("#tk-body").innerHTML = `<section class="the">${loading()}</section>`;
      try {
        const data = await api("/api/learning/overview");
        if (!alive()) return;
        shell(data);
        await Promise.allSettled([loadTrend(), loadMistakes(), loadProgress(), loadHistory()]);
      } catch (error) { if (alive()) find("#tk-body").innerHTML = `<section class="the">${retry(error.message, "reload")}</section>`; }
    }
    start();
  };

  // Đổi tài khoản/đăng xuất ở tab khác: bỏ dữ liệu cũ khi quay lại tab này.
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && current && location.hash === "#/thong-ke") {
      window.dongThongKe();
      if (typeof veThongKe === "function") veThongKe();
    }
  });
  window.addEventListener("pageshow", event => {
    if (event.persisted && location.hash === "#/thong-ke" && typeof veThongKe === "function") veThongKe();
  });
})();
