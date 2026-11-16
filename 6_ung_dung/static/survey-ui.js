"use strict";

// Biểu mẫu trong trang Giới thiệu. Bản nháp chỉ ở RAM của lần mở trang này.
(() => {
  let current = null;
  const length = text => [...text].length; // Cùng cách đếm Unicode code point của Python.
  const when = value => {
    const time = new Date(value);
    return Number.isNaN(+time) ? "" : time.toLocaleString("vi-VN", {
      timeZone: "Asia/Ho_Chi_Minh", day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit"
    });
  };

  window.dongKhaoSat = () => {
    current?.controller.abort();
    current = null;
  };

  window.hienThiKhaoSat = ({ root, ic, esc }) => {
    window.dongKhaoSat();
    const state = { root, controller: new AbortController(), meta: null, values: new Map(), ownerId: null,
      saved: null, ready: false, busy: false, loadingUser: false, loadedForOwner: false };
    current = state;
    const alive = () => current === state && !state.controller.signal.aborted && root.isConnected;
    const find = selector => root.querySelector(selector);
    const title = `<div class="ks-heading"><span class="ks-heading-icon">${ic("edit")}</span>
      <div><h2 id="ks-title">Đánh giá ứng dụng</h2><p>Chia sẻ trải nghiệm học và ôn tập biển báo của bạn.</p></div>
      <span class="ks-optional">Khảo sát tự nguyện</span></div>`;
    const loading = text => `<p class="ks-loading" role="status"><span class="ks-spinner" aria-hidden="true"></span>${esc(text)}</p>`;
    const loginLink = '<a class="nut chinh" href="/auth/google">Đăng nhập bằng Google để đánh giá</a>';

    async function api(url, options = {}) {
      const controller = new AbortController();
      const abort = () => controller.abort();
      state.controller.signal.addEventListener("abort", abort, { once: true });
      const timeout = setTimeout(abort, 15000);
      try {
        const response = await fetch(url, { ...options, credentials: "same-origin", cache: "no-store", signal: controller.signal });
        const data = await response.json().catch(() => null);
        if (!alive()) throw new DOMException("Đã rời trang khảo sát", "AbortError");
        if (!response.ok) {
          const fallback = response.status === 404 ? "API khảo sát chưa được nạp. Hãy khởi động lại Flask rồi tải lại trang."
            : response.status === 401 ? "Phiên đăng nhập đã kết thúc. Hãy đăng nhập Google để tiếp tục."
            : "Chưa xử lý được yêu cầu. Hãy thử lại.";
          const error = new Error(typeof data?.loi === "string" ? data.loi : `${fallback} (HTTP ${response.status})`);
          error.status = response.status;
          throw error;
        }
        if (!data || typeof data !== "object") throw new Error("Phản hồi từ máy chủ chưa đầy đủ. Hãy thử lại.");
        return data;
      } catch (error) {
        if (!alive()) throw error;
        if (error.name === "AbortError") throw new Error("Kết nối quá thời gian chờ. Chưa nhận được xác nhận từ máy chủ. Hãy thử lại.");
        if (error instanceof TypeError) throw new Error("Không kết nối được máy chủ. Nội dung đang nhập được giữ trên trang này; hãy thử lại.");
        throw error;
      } finally {
        clearTimeout(timeout);
        state.controller.signal.removeEventListener("abort", abort);
      }
    }

    function checkMetadata(meta) {
      const validScale = Array.isArray(meta.likert_scale) && meta.likert_scale.length === 5
        && new Set(meta.likert_scale.map(item => item.value)).size === 5
        && meta.likert_scale.every(item => Number.isInteger(item.value) && item.value >= 1 && item.value <= 5 && typeof item.label === "string");
      if (!Number.isInteger(meta.survey_version) || meta.survey_version < 1 || !validScale
          || !Number.isInteger(meta.feedback_max_length) || meta.feedback_max_length < 1 || meta.feedback_max_length > 1000
          || !Array.isArray(meta.questions) || !meta.questions.length
          || new Set(meta.questions.map(question => question.id)).size !== meta.questions.length
          || meta.questions.some(question => !Number.isInteger(question.id) || question.id < 1
            || !["likert", "text"].includes(question.question_type) || typeof question.question_text !== "string"
            || typeof question.is_required !== "boolean")
          || typeof meta.purpose !== "string" || typeof meta.privacy_notice !== "string") {
        throw new Error("Dữ liệu câu hỏi khảo sát chưa hợp lệ. Hãy thử tải lại.");
      }
    }

    function message(text, kind = "error") {
      const node = find("#ks-message");
      node.textContent = text;
      node.className = "ks-message " + kind;
      node.setAttribute("role", kind === "error" ? "alert" : "status");
      node.hidden = !text;
    }

    function frame() {
      const meta = state.meta;
      root.innerHTML = `${title}<p class="ks-purpose">${esc(meta.purpose)}</p>
        <div class="ks-privacy">${ic("info")}<div><b>Thông tin quyền riêng tư</b><p>${esc(meta.privacy_notice)}</p></div></div>
        <div id="ks-auth" aria-live="polite"></div><div id="ks-saved" class="ks-saved" role="status" hidden></div>
        <div class="ks-scale-heading"><h3>Thang đánh giá</h3><span>Chọn một mức cho mỗi tiêu chí.</span></div>
        <ol class="ks-scale">${meta.likert_scale.map(item => `<li><b>${item.value}</b><span>${esc(item.label)}</span></li>`).join("")}</ol>
        <form id="ks-form" novalidate><div class="ks-form-heading"><span>Các câu có dấu <b aria-hidden="true">*</b> là bắt buộc.</span><span id="ks-progress" aria-live="polite"></span></div>
          <div class="ks-questions">${meta.questions.map((question, index) => {
            const id = question.id, isRating = question.question_type === "likert";
            return `<fieldset class="ks-question" id="ks-question-${id}" disabled aria-describedby="ks-error-${id}">
              <legend><span class="ks-number">${index + 1}</span><span>${esc(question.question_text)} ${question.is_required ? '<b class="ks-required" aria-label="bắt buộc">*</b>' : '<small class="ks-question-optional">Không bắt buộc</small>'}</span></legend>
              ${isRating ? `<div class="ks-options">${meta.likert_scale.map(item => `<label class="ks-option"><input type="radio" name="ks-q-${id}" data-ks-question="${id}" value="${item.value}" ${question.is_required ? "required" : ""} aria-label="${item.value} – ${esc(item.label)}" aria-describedby="ks-error-${id}">
                <span class="ks-choice"><b>${item.value}</b><small>${esc(item.label)}</small></span></label>`).join("")}</div>`
              : `<textarea name="ks-q-${id}" data-ks-question="${id}" rows="4" aria-label="${esc(question.question_text)}" aria-describedby="ks-count-${id} ks-error-${id}" placeholder="Chia sẻ điều bạn thích hoặc mong muốn cải thiện…"></textarea>
                <div class="ks-text-hint"><span>Tối đa ${meta.feedback_max_length} ký tự.</span><span id="ks-count-${id}">0/${meta.feedback_max_length}</span></div>`}
              <p class="ks-field-error" id="ks-error-${id}" hidden></p></fieldset>`;
          }).join("")}</div>
          <p id="ks-message" class="ks-message" aria-live="polite" hidden></p>
          <div class="ks-actions"><button class="nut chinh" type="submit" id="ks-submit" disabled>${ic("check")}<span>Gửi đánh giá</span></button>
            <button class="nut ks-delete" type="button" data-ks-action="delete" id="ks-delete" hidden>${ic("trash")}Xóa đánh giá</button>
            <span id="ks-draft-note" class="ks-draft-note"></span></div>
        </form>
        <p class="ks-interpretation">${esc(meta.interpretation_notice)}</p>
        <dialog class="ks-delete-dialog" id="ks-delete-dialog" aria-labelledby="ks-delete-title"><h3 id="ks-delete-title">Xóa đánh giá của bạn?</h3>
          <p>Phiếu đánh giá và các câu trả lời đã lưu sẽ bị xóa. Bạn có thể gửi một đánh giá mới sau đó.</p>
          <div class="hang-nut"><button class="nut" type="button" data-ks-action="cancel-delete" autofocus>Giữ lại đánh giá</button>
          <button class="nut ks-delete" type="button" data-ks-action="confirm-delete">${ic("trash")}Xóa đánh giá</button></div></dialog>`;
      updateProgress();
    }

    function controls() {
      const locked = state.busy || state.loadingUser || !state.ready || !state.ownerId;
      find("#ks-form").setAttribute("aria-busy", String(!!state.busy || state.loadingUser));
      root.querySelectorAll(".ks-question").forEach(field => { field.disabled = locked; });
      find("#ks-submit").disabled = locked;
      find("#ks-submit span").textContent = state.busy === "submit" ? "Đang gửi…" : state.saved ? "Cập nhật đánh giá" : "Gửi đánh giá";
      find("#ks-delete").hidden = !state.saved;
      find("#ks-delete").disabled = locked;
      root.querySelectorAll("#ks-delete-dialog button").forEach(button => { button.disabled = !!state.busy; });
      const retry = find('[data-ks-action="retry-user"]');
      if (retry) retry.disabled = !!state.loadingUser || !!state.busy;
      const saved = find("#ks-saved");
      saved.hidden = !state.saved;
      saved.textContent = state.saved ? "Đã gửi đánh giá · Cập nhật gần nhất: " + when(state.saved.updated_at) + " (giờ Việt Nam)" : "";
    }

    function readDraft() {
      for (const question of state.meta.questions) {
        const name = `[name="ks-q-${question.id}"]`;
        if (question.question_type === "likert") {
          const checked = find(name + ":checked");
          if (checked) state.values.set(question.id, +checked.value);
          else state.values.delete(question.id);
        } else state.values.set(question.id, find(name).value);
      }
    }

    function fillDraft() {
      for (const question of state.meta.questions) {
        const value = state.values.get(question.id);
        root.querySelectorAll(`[name="ks-q-${question.id}"]`).forEach(input => {
          if (question.question_type === "likert") input.checked = +input.value === value;
          else input.value = typeof value === "string" ? value : "";
          input.removeAttribute("aria-invalid");
        });
        fieldError(question.id, "");
      }
      updateProgress();
    }

    function fieldError(id, text) {
      find("#ks-error-" + id).textContent = text;
      find("#ks-error-" + id).hidden = !text;
      find("#ks-question-" + id).classList.toggle("ks-invalid", !!text);
      root.querySelectorAll(`[name="ks-q-${id}"]`).forEach(input => input.setAttribute("aria-invalid", String(!!text)));
    }

    function updateProgress() {
      const required = state.meta.questions.filter(question => question.is_required && question.question_type === "likert");
      find("#ks-progress").textContent = `Đã chọn ${required.filter(question => state.values.has(question.id)).length}/${required.length} tiêu chí`;
      for (const question of state.meta.questions.filter(question => question.question_type === "text")) {
        const count = length(state.values.get(question.id) || "");
        const counter = find("#ks-count-" + question.id);
        counter.textContent = `${count}/${state.meta.feedback_max_length}`;
        counter.classList.toggle("ks-over-limit", count > state.meta.feedback_max_length);
      }
    }

    function validateDraft() {
      let first = null;
      for (const question of state.meta.questions) {
        const value = state.values.get(question.id);
        let error = "";
        if (question.question_type === "likert") {
          if (question.is_required && !state.meta.likert_scale.some(item => item.value === value)) error = "Vui lòng chọn một mức đánh giá cho tiêu chí này.";
        } else if (length(value || "") > state.meta.feedback_max_length) error = `Góp ý không được vượt quá ${state.meta.feedback_max_length} ký tự.`;
        else if (question.is_required && !value?.trim()) error = "Vui lòng trả lời câu hỏi này.";
        fieldError(question.id, error);
        if (error && first === null) first = question.id;
      }
      if (first !== null) {
        message("Vui lòng kiểm tra các câu được đánh dấu trước khi gửi đánh giá.");
        find(`[name="ks-q-${first}"]`).focus();
        return false;
      }
      return true;
    }

    function valuesFrom(response) {
      if (!response || !Array.isArray(response.answers) || !Number.isInteger(response.survey_version)) throw new Error("Phiếu máy chủ trả về chưa đầy đủ. Hãy thử lại.");
      const values = new Map();
      if (response.survey_version !== state.meta.survey_version) return values;
      for (const question of state.meta.questions) {
        const answer = response.answers.find(item => item.question_id === question.id && item.question_type === question.question_type);
        if (answer && (question.question_type === "text" ? typeof answer.value === "string" : state.meta.likert_scale.some(item => item.value === answer.value))) values.set(question.id, answer.value);
      }
      return values;
    }

    function becomeGuest() {
      state.ownerId = null; state.saved = null; state.ready = false; state.loadedForOwner = false;
      state.values.clear(); fillDraft();
      find("#ks-draft-note").textContent = "";
      find("#ks-auth").innerHTML = `<div class="ks-login"><p>Đăng nhập Google để gửi và quản lý đánh giá trên tài khoản của bạn.</p>${loginLink}</div>`;
      controls();
    }

    async function sessionNow() {
      const session = await api("/api/me");
      if (typeof session.da_dang_nhap !== "boolean" || (session.da_dang_nhap && !Number.isInteger(session.user?.id))) throw new Error("Chưa xác minh được phiên đăng nhập. Hãy thử lại.");
      return session;
    }

    async function loadUser(keepDraft = false, knownSession = null) {
      if (!alive() || state.loadingUser) return;
      state.loadingUser = true; state.ready = false;
      find("#ks-auth").innerHTML = loading("Đang tải phiếu đánh giá của bạn…");
      controls();
      try {
        const session = knownSession || await sessionNow();
        if (!alive()) return;
        if (!session.da_dang_nhap) { becomeGuest(); return; }
        const sameOwner = state.ownerId === session.user.id;
        if (!sameOwner) {
          state.values.clear(); state.saved = null; state.loadedForOwner = false;
          fillDraft(); find("#ks-draft-note").textContent = "";
        }
        state.ownerId = session.user.id;
        if (!(keepDraft && sameOwner && state.loadedForOwner)) {
          const mine = await api("/api/survey/me");
          if (!alive()) return;
          if (typeof mine.has_response !== "boolean" || (mine.has_response && !mine.response)) throw new Error("Chưa đọc được phiếu đánh giá. Hãy thử lại.");
          state.saved = mine.has_response ? mine.response : null;
          state.values = state.saved ? valuesFrom(state.saved) : new Map();
          fillDraft();
        }
        state.loadedForOwner = true; state.ready = true;
        find("#ks-auth").replaceChildren();
      } catch (error) {
        if (alive()) {
          if (error.status === 401) becomeGuest();
          else {
            find("#ks-auth").innerHTML = `<div class="ks-load-error" role="alert"><p>${esc(error.message)}</p><button class="nut" type="button" data-ks-action="retry-user">${ic("refresh")}Thử lại</button></div>`;
          }
        }
      } finally {
        state.loadingUser = false;
        if (alive()) controls();
      }
    }

    async function write(action) {
      if (!alive() || state.busy || !state.ready || !state.ownerId) return;
      readDraft();
      if (action === "submit" && !validateDraft()) return;
      state.busy = action; message(""); controls();
      try {
        const session = await sessionNow();
        if (!alive()) return;
        if (!session.da_dang_nhap) { becomeGuest(); message("Phiên đăng nhập đã kết thúc. Hãy đăng nhập Google để tiếp tục."); return; }
        if (session.user.id !== state.ownerId) {
          await loadUser(false, session);
          if (alive()) message("Tài khoản đã thay đổi. Phiếu của tài khoản hiện tại đã được tải lại; hãy kiểm tra trước khi gửi.");
          return;
        }
        if (typeof session.csrf_token !== "string" || !session.csrf_token) throw new Error("Phiên đăng nhập chưa có CSRF hợp lệ. Hãy đăng nhập lại rồi thử gửi.");
        const headers = { "X-CSRF-Token": session.csrf_token };
        if (action === "submit") {
          const answers = state.meta.questions.filter(question => state.values.has(question.id)).map(question => ({ question_id: question.id, value: state.values.get(question.id) }));
          const data = await api("/api/survey/submit", { method: "POST", headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ survey_version: state.meta.survey_version, answers }) });
          const confirmed = valuesFrom(data.response);
          if (!data.saved || data.response.survey_version !== state.meta.survey_version
              || state.meta.questions.some(question => question.is_required && !confirmed.has(question.id))) throw new Error("Chưa nhận được xác nhận lưu đầy đủ. Nội dung đang nhập vẫn được giữ; bạn có thể thử gửi lại.");
          state.saved = data.response; state.values = confirmed; fillDraft();
          find("#ks-draft-note").textContent = "Bạn có thể thay đổi lựa chọn và gửi cập nhật bất cứ lúc nào.";
          message(data.created ? "Đã gửi đánh giá. Cảm ơn bạn đã chia sẻ trải nghiệm!" : "Đã cập nhật đánh giá của bạn.", "success");
        } else {
          const data = await api("/api/survey/me", { method: "DELETE", headers });
          if (typeof data.deleted !== "boolean") throw new Error("Chưa xác nhận được việc xóa. Bạn có thể thử lại.");
          state.saved = null; state.values.clear(); fillDraft();
          find("#ks-draft-note").textContent = "";
          message("Đã xóa đánh giá của bạn. Bạn có thể gửi một đánh giá mới.", "success");
        }
      } catch (error) {
        if (alive()) {
          if (error.status === 401) becomeGuest();
          message(error.message);
        }
      } finally {
        state.busy = false;
        if (alive()) {
          find("#ks-delete-dialog").close();
          controls();
        }
      }
    }

    root.addEventListener("input", event => {
      if (!event.target.matches("[data-ks-question]")) return;
      readDraft(); updateProgress();
      const id = +event.target.dataset.ksQuestion;
      const question = state.meta.questions.find(item => item.id === id);
      fieldError(id, question.question_type === "text" && length(event.target.value) > state.meta.feedback_max_length ? `Góp ý không được vượt quá ${state.meta.feedback_max_length} ký tự.` : "");
      find("#ks-draft-note").textContent = state.saved ? "Bạn có thay đổi chưa gửi." : "";
      message("");
    });
    root.addEventListener("submit", event => { event.preventDefault(); write("submit"); });
    root.addEventListener("click", event => {
      const button = event.target.closest?.("[data-ks-action]");
      if (!button || !alive()) return;
      const action = button.dataset.ksAction;
      if (action === "retry-load") start();
      if (action === "retry-user" && !state.busy) loadUser(state.loadedForOwner);
      if (action === "delete" && state.saved && !state.busy) find("#ks-delete-dialog").showModal();
      if (action === "cancel-delete" && !state.busy) find("#ks-delete-dialog").close();
      if (action === "confirm-delete") write("delete");
    });
    state.refresh = () => { if (alive() && state.meta && !state.busy) loadUser(true); };

    let starting = false;
    async function start() {
      if (starting) return;
      starting = true;
      root.innerHTML = title + loading("Đang tải khảo sát…");
      try {
        const meta = await api("/api/survey/questions");
        checkMetadata(meta);
        state.meta = meta; frame();
        await loadUser();
      } catch (error) {
        if (alive()) root.innerHTML = `${title}<div class="ks-load-error" role="alert"><p>${esc(error.message)}</p><button class="nut" type="button" data-ks-action="retry-load">${ic("refresh")}Thử lại</button></div>`;
      } finally { starting = false; }
    }
    start();
  };

  document.addEventListener("visibilitychange", () => { if (!document.hidden) current?.refresh(); });
  window.addEventListener("pageshow", event => { if (event.persisted) current?.refresh(); });
})();
