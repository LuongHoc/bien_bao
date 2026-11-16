"use strict";

// Hộp thoại khảo sát nhanh thông minh sau bài tập (Quick Survey)
(() => {
  let modalInstance = null;

  const TAGS_MAC_DINH = [
    "Giao diện dễ sử dụng",
    "Câu hỏi hữu ích",
    "Nội dung dễ hiểu",
    "Cần cải thiện giao diện",
    "Gặp lỗi khi sử dụng"
  ];

  const EMOJIS = [
    { value: 1, emoji: "😣", label: "Rất tệ" },
    { value: 2, emoji: "🙁", label: "Chưa tốt" },
    { value: 3, emoji: "😐", label: "Bình thường" },
    { value: 4, emoji: "🙂", label: "Tốt" },
    { value: 5, emoji: "😍", label: "Rất tốt" }
  ];

  function taoDialog() {
    let dialog = document.getElementById("hop-khao-sat-nhanh");
    if (!dialog) {
      dialog = document.createElement("dialog");
      dialog.id = "hop-khao-sat-nhanh";
      dialog.className = "ksn-dialog";
      dialog.setAttribute("aria-labelledby", "ksn-title");
      dialog.setAttribute("aria-modal", "true");
      document.body.appendChild(dialog);
    }
    return dialog;
  }

  window.kiemTraVaHienThiKhaoSatNhanh = async ({ attemptId = null } = {}) => {
    // 1. Chỉ thực hiện khi đang ở trang kết quả bài tập
    if (location.hash !== "#/bai-tap/ket-qua") return;

    // 2. Chờ 1.2 giây để người học kịp xem cúp và điểm số bài thi
    await new Promise(r => setTimeout(r, 1200));

    // 3. Kiểm tra lại điều kiện ngữ cảnh sau thời gian chờ
    if (location.hash !== "#/bai-tap/ket-qua") return;
    const dialogMo = document.querySelector("dialog[open]");
    if (dialogMo && dialogMo.id !== "hop-khao-sat-nhanh") return;

    // 4. Lấy phiên người dùng hiện tại
    let phien;
    try {
      phien = await (window.layPhienGoogle ? window.layPhienGoogle() : fetch("/api/me").then(r => r.json()));
    } catch {
      return;
    }
    if (!phien || !phien.da_dang_nhap) return;

    // 5. Hỏi máy chủ điều kiện hiển thị
    try {
      const url = attemptId ? `/api/survey/quick/check?attempt_id=${encodeURIComponent(attemptId)}` : "/api/survey/quick/check";
      const res = await fetch(url, { credentials: "same-origin", cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json();
      if (!data.should_prompt) return;

      // 6. Hiển thị hộp thoại khảo sát nhanh
      hienThiHopThoai({
        promptStep: data.prompt_step || 1,
        attemptId: attemptId,
        csrfToken: phien.csrf_token || ""
      });
    } catch (e) {
      // Bỏ qua lỗi mạng khi kiểm tra prompt
    }
  };

  function hienThiHopThoai({ promptStep = 1, attemptId = null, csrfToken = "" }) {
    const dialog = taoDialog();
    const state = {
      step: 1, // 1: Đánh giá nhanh, 2: Góp ý chi tiết, 3: Cảm ơn
      promptStep,
      attemptId,
      csrfToken,
      rating: null,
      tags: new Set(),
      feedback: "",
      submitting: false
    };
    modalInstance = state;

    function render() {
      if (state.step === 1) {
        renderManHinh1();
      } else if (state.step === 2) {
        renderManHinh2();
      } else if (state.step === 3) {
        renderManHinh3();
      }
    }

    function renderManHinh1() {
      const tieuDe = state.promptStep === 1
        ? "Bạn đã hoàn thành bài học đầu tiên! 🎉"
        : "Bạn đang tiến bộ rất nhanh! 🎉";

      dialog.innerHTML = `
        <div class="ksn-wrap">
          <button type="button" class="ksn-nut-dong" id="ksn-dong-x" aria-label="Đóng và để sau">
            <svg class="ic" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
          <div class="ksn-icon-dau">
            <span class="ksn-badge-nho">Khảo sát nhanh</span>
          </div>
          <h2 id="ksn-title" class="ksn-tieu-de">${tieuDe}</h2>
          <p class="ksn-mo-ta">Trải nghiệm luyện tập biển báo của bạn thế nào?</p>

          <div class="ksn-emojis" role="radiogroup" aria-label="Mức độ hài lòng">
            ${EMOJIS.map(item => `
              <button type="button" class="ksn-emoji-btn ${state.rating === item.value ? "active" : ""}"
                data-rating="${item.value}" role="radio" aria-checked="${state.rating === item.value}">
                <span class="ksn-emoji">${item.emoji}</span>
                <span class="ksn-emoji-nhan">${item.label}</span>
              </button>
            `).join("")}
          </div>

          <div class="ksn-hang-nut">
            <button type="button" class="nut" id="ksn-de-sau">Để sau</button>
            <button type="button" class="nut chinh" id="ksn-tiep-tuc" ${state.rating === null ? "disabled" : ""}>Tiếp tục</button>
          </div>
        </div>
      `;

      dialog.querySelectorAll(".ksn-emoji-btn").forEach(btn => {
        btn.onclick = () => {
          state.rating = +btn.dataset.rating;
          dialog.querySelectorAll(".ksn-emoji-btn").forEach(b => {
            const active = +b.dataset.rating === state.rating;
            b.classList.toggle("active", active);
            b.setAttribute("aria-checked", String(active));
          });
          const btnTiep = dialog.querySelector("#ksn-tiep-tuc");
          if (btnTiep) btnTiep.disabled = false;
        };
      });

      const btnDeSau = dialog.querySelector("#ksn-de-sau");
      if (btnDeSau) btnDeSau.onclick = () => xuLyDeSau();

      const btnDongX = dialog.querySelector("#ksn-dong-x");
      if (btnDongX) btnDongX.onclick = () => xuLyDeSau();

      const btnTiepTuc = dialog.querySelector("#ksn-tiep-tuc");
      if (btnTiepTuc) {
        btnTiepTuc.onclick = () => {
          if (state.rating === null) return;
          state.step = 2;
          render();
        };
      }
    }

    function renderManHinh2() {
      dialog.innerHTML = `
        <div class="ksn-wrap">
          <button type="button" class="ksn-nut-dong" id="ksn-dong-x2" aria-label="Đóng và để sau">
            <svg class="ic" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
          <h2 id="ksn-title" class="ksn-tieu-de">Cảm ơn bạn! Bạn muốn góp ý thêm điều gì?</h2>
          <p class="ksn-mo-ta">Chọn các điểm bạn thấy phù hợp hoặc ghi ý kiến riêng.</p>

          <div class="ksn-tags" role="group" aria-label="Các tiêu chí góp ý nhanh">
            ${TAGS_MAC_DINH.map(tag => `
              <button type="button" class="ksn-tag-btn ${state.tags.has(tag) ? "da-chon" : ""}" data-tag="${tag}">
                ${tag}
              </button>
            `).join("")}
          </div>

          <div class="ksn-textarea-wrap">
            <textarea id="ksn-feedback" rows="3" maxlength="1000"
              placeholder="Góp ý khác (không bắt buộc)...">${state.feedback || ""}</textarea>
            <div class="ksn-char-count"><span id="ksn-dem-ky-tu">${[...(state.feedback || "")].length}</span>/1000</div>
          </div>

          <div id="ksn-loi" class="ksn-thong-bao-loi" hidden></div>

          <div class="ksn-hang-nut">
            <button type="button" class="nut" id="ksn-bo-qua-gop-y" ${state.submitting ? "disabled" : ""}>Bỏ qua góp ý</button>
            <button type="button" class="nut chinh" id="ksn-hoan-tat" ${state.submitting ? "disabled" : ""}>Hoàn tất đánh giá</button>
          </div>
        </div>
      `;

      dialog.querySelectorAll(".ksn-tag-btn").forEach(btn => {
        btn.onclick = () => {
          const tag = btn.dataset.tag;
          if (state.tags.has(tag)) state.tags.delete(tag);
          else state.tags.add(tag);
          btn.classList.toggle("da-chon", state.tags.has(tag));
        };
      });

      const txt = dialog.querySelector("#ksn-feedback");
      const dem = dialog.querySelector("#ksn-dem-ky-tu");
      if (txt) {
        txt.oninput = () => {
          state.feedback = txt.value;
          if (dem) dem.textContent = [...txt.value].length;
        };
      }

      const btnDongX = dialog.querySelector("#ksn-dong-x2");
      if (btnDongX) btnDongX.onclick = () => xuLyDeSau();

      const btnBoQua = dialog.querySelector("#ksn-bo-qua-gop-y");
      if (btnBoQua) btnBoQua.onclick = () => guiDanhGia({ chiDiem: true });

      const btnHoanTat = dialog.querySelector("#ksn-hoan-tat");
      if (btnHoanTat) btnHoanTat.onclick = () => guiDanhGia({ chiDiem: false });
    }

    function renderManHinh3() {
      dialog.innerHTML = `
        <div class="ksn-wrap ksn-wrap-cam-on">
          <div class="ksn-cam-on-icon">
            <svg class="ic" viewBox="0 0 24 24" style="width:48px;height:48px;color:var(--la)">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke-width="2.5"/>
              <polyline points="22 4 12 14.01 9 11.01" stroke-width="2.5"/>
            </svg>
          </div>
          <h2 id="ksn-title" class="ksn-tieu-de">Cảm ơn bạn đã đánh giá!</h2>
          <p class="ksn-mo-ta">Ý kiến của bạn sẽ giúp chúng tôi hoàn thiện và cải tiến ứng dụng ngày càng tốt hơn.</p>
          <div class="ksn-hang-nut" style="justify-content:center;margin-top:16px">
            <button type="button" class="nut chinh" id="ksn-dong-cam-on">Tiếp tục học tập</button>
          </div>
        </div>
      `;

      const btnDong = dialog.querySelector("#ksn-dong-cam-on");
      if (btnDong) {
        btnDong.onclick = () => {
          dialog.close();
        };
      }
    }

    async function xuLyDeSau() {
      try {
        await fetch("/api/survey/quick/dismiss", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": state.csrfToken
          },
          body: JSON.stringify({ attempt_id: state.attemptId })
        });
      } catch {
        // Lỗi mạng khi dismiss không chặn việc đóng hộp thoại
      }
      dialog.close();
    }

    async function guiDanhGia({ chiDiem = false }) {
      if (state.submitting) return;
      state.submitting = true;
      const loiBox = dialog.querySelector("#ksn-loi");
      if (loiBox) loiBox.hidden = true;

      const payload = {
        rating: state.rating,
        tags: chiDiem ? [] : Array.from(state.tags),
        feedback: chiDiem ? null : (state.feedback ? state.feedback.trim() : null),
        attempt_id: state.attemptId
      };

      try {
        const res = await fetch("/api/survey/quick/submit", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": state.csrfToken
          },
          body: JSON.stringify(payload)
        });
        const data = await res.json().catch(() => null);
        if (!res.ok) {
          throw new Error(data?.loi || `Lỗi máy chủ (HTTP ${res.status}). Hãy thử lại.`);
        }
        state.step = 3;
        render();
      } catch (err) {
        state.submitting = false;
        if (loiBox) {
          loiBox.textContent = err.message || "Không gửi được đánh giá. Hãy thử lại.";
          loiBox.hidden = false;
        }
        const btnBoQua = dialog.querySelector("#ksn-bo-qua-gop-y");
        const btnHoanTat = dialog.querySelector("#ksn-hoan-tat");
        if (btnBoQua) btnBoQua.disabled = false;
        if (btnHoanTat) btnHoanTat.disabled = false;
      }
    }

    // Xử lý đóng dialog bằng phím ESC hoặc click bên ngoài backdrop
    dialog.oncancel = (e) => {
      e.preventDefault();
      xuLyDeSau();
    };
    dialog.onclick = (e) => {
      if (e.target === dialog) xuLyDeSau();
    };

    render();
    if (!dialog.open) {
      dialog.showModal();
    }
  }
})();
