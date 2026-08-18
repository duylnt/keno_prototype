(function () {
  const cfg = window.KENO || {};

  function pad(n) {
    return String(n).padStart(2, "0");
  }
  function formatCountdown(total) {
    const s = Math.max(0, Number(total) || 0);
    const m = Math.floor(s / 60);
    const r = s % 60;
    return pad(m) + ":" + pad(r);
  }
  function applyCountdown() {
    document.querySelectorAll("[data-countdown]").forEach((el) => {
      const raw = el.getAttribute("data-seconds") || el.textContent;
      const n = parseInt(raw, 10);
      if (!Number.isNaN(n) && n > 1000) {
        el.setAttribute("data-seconds", String(n));
        el.textContent = formatCountdown(n);
      } else if (el.getAttribute("data-seconds")) {
        el.textContent = formatCountdown(el.getAttribute("data-seconds"));
      } else {
        el.setAttribute("data-seconds", String(n));
        el.textContent = formatCountdown(n);
      }
    });
  }
  function tick() {
    document.querySelectorAll("[data-countdown]").forEach((el) => {
      let n = parseInt(el.getAttribute("data-seconds") || "0", 10);
      if (n > 0) {
        n -= 1;
        el.setAttribute("data-seconds", String(n));
        el.textContent = formatCountdown(n);
      }
    });
  }
  applyCountdown();
  setInterval(tick, 1000);

  function renderBoard(data) {
    if (!data || data.heartbeat) {
      if (data && data.countdown != null) {
        document.querySelectorAll("[data-countdown]").forEach((el) => {
          el.setAttribute("data-seconds", String(data.countdown));
          el.textContent = formatCountdown(data.countdown);
        });
      }
      return;
    }
    const balls = document.querySelector("[data-balls]");
    if (balls && data.numbers) {
      balls.innerHTML = data.numbers
        .map((n) => `<li class="${n % 2 === 0 ? "is-even" : "is-odd"}">${pad(n)}</li>`)
        .join("");
    }
    const total = document.querySelector("[data-total]");
    if (total && data.total) total.textContent = data.total;
    const size = document.querySelector("[data-size]");
    if (size && data.size_label) size.textContent = data.size_label;
    const parity = document.querySelector("[data-parity]");
    if (parity && data.parity_label) parity.textContent = data.parity_label;
    const period = document.querySelector("[data-period]");
    if (period && data.period_code) period.textContent = data.period_code;
    if (data.countdown != null) {
      document.querySelectorAll("[data-countdown]").forEach((el) => {
        el.setAttribute("data-seconds", String(data.countdown));
        el.textContent = formatCountdown(data.countdown);
      });
    }
  }

  function poll() {
    if (!cfg.liveApi) return;
    fetch(cfg.liveApi)
      .then((r) => r.json())
      .then(renderBoard)
      .catch(() => {});
  }
  poll();
  setInterval(poll, 5000);
  if (cfg.sse && window.EventSource && /sse=1/.test(location.search)) {
    try {
      const es = new EventSource(cfg.sse);
      es.onmessage = (ev) => {
        try {
          renderBoard(JSON.parse(ev.data));
        } catch (e) {}
      };
    } catch (e) {}
  }

  function track(event, meta) {
    if (!cfg.track) return;
    fetch(cfg.track, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event, meta: meta || {}, path: location.pathname }),
    }).catch(() => {});
  }
  document.querySelectorAll("[data-track]").forEach((el) => {
    el.addEventListener("click", () => track(el.getAttribute("data-track")));
  });

  const picker = document.getElementById("picker");
  if (picker) {
    const selected = new Set();
    const pickedInput = document.getElementById("picked-numbers");
    const pickCount = document.getElementById("pick-count");
    function syncPicked() {
      if (pickedInput) pickedInput.value = Array.from(selected).join(",");
      if (pickCount) pickCount.textContent = "Đã chọn " + selected.size + " số";
    }
    for (let i = 1; i <= 80; i++) {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = pad(i);
      b.addEventListener("click", () => {
        if (selected.has(i)) selected.delete(i);
        else if (selected.size < 10) selected.add(i);
        b.classList.toggle("on", selected.has(i));
        syncPicked();
      });
      picker.appendChild(b);
    }
    document.getElementById("quick-pick").addEventListener("click", () => {
      selected.clear();
      picker.querySelectorAll("button").forEach((x) => x.classList.remove("on"));
      const pool = Array.from({ length: 80 }, (_, i) => i + 1);
      for (let k = 0; k < 5; k++) {
        const idx = Math.floor(Math.random() * pool.length);
        const n = pool.splice(idx, 1)[0];
        selected.add(n);
        picker.children[n - 1].classList.add("on");
      }
      syncPicked();
    });
    function prizeBlock(item, kicker) {
      if (!item) return "";
      const state = item.won ? "is-win" : "is-miss";
      return (
        '<article class="sim-prize-item ' +
        state +
        '"><p class="sim-prize-kicker">' +
        kicker +
        "</p><p class=\"sim-prize-status\">" +
        (item.headline || "") +
        "</p><p class=\"sim-prize-kind\">" +
        (item.name || "") +
        "</p><p class=\"sim-prize-amount\">" +
        (item.amount_label || "0 ₫") +
        "</p><p class=\"sim-prize-detail\">" +
        (item.detail || "") +
        "</p></article>"
      );
    }
    function highlightPrizeCell(pick, match) {
      document.querySelectorAll(".sim-prize-table td.is-hit").forEach((td) => td.classList.remove("is-hit"));
      if (!pick) return;
      const td = document.querySelector(
        '.sim-prize-table td[data-pick="' + pick + '"][data-match="' + match + '"]'
      );
      if (td) td.classList.add("is-hit");
    }
    function renderSimPrize(prize) {
      const box = document.getElementById("sim-prize");
      if (!box) return;
      const basic = prize.basic || {};
      box.innerHTML =
        prizeBlock(basic, "Giải của bạn") +
        '<div class="sim-prize-sides">' +
        prizeBlock(prize.size, "Cửa kỳ này") +
        prizeBlock(prize.parity, "Cửa kỳ này") +
        "</div>" +
        '<p class="muted">' +
        (prize.note || "Mô phỏng trên Chơi thử — không chi trả tiền thật.") +
        "</p>";
      highlightPrizeCell(basic.pick_count, basic.match_count);
      const lead = document.getElementById("sim-prize-notice-lead");
      if (lead) lead.textContent = prize.notice_lead || "";
      const heading = document.getElementById("sim-prize-notice-title");
      if (heading) heading.textContent = prize.notice_title || "Kết quả kỳ quay vừa rồi";
    }
    const prizeDialog = document.getElementById("sim-prize-dialog");
    const prizeNotice = document.getElementById("sim-prize-notice");
    let revealPrizeNotice = true;
    let prizeBackdrop = document.getElementById("sim-prize-backdrop");
    if (prizeDialog && prizeDialog.parentElement !== document.body) {
      document.body.appendChild(prizeDialog);
    }
    function ensurePrizeBackdrop() {
      if (prizeBackdrop) return prizeBackdrop;
      prizeBackdrop = document.createElement("div");
      prizeBackdrop.id = "sim-prize-backdrop";
      prizeBackdrop.className = "sim-prize-backdrop";
      prizeBackdrop.hidden = true;
      prizeBackdrop.addEventListener("click", () => closePrizeDialog());
      document.body.appendChild(prizeBackdrop);
      return prizeBackdrop;
    }
    function fillPrizeDialog(prize) {
      if (!prizeDialog) return;
      const title = document.getElementById("sim-prize-dialog-title");
      const body = document.getElementById("sim-prize-dialog-body");
      const note = document.getElementById("sim-prize-dialog-note");
      const won = !!prize.won;
      prizeDialog.classList.toggle("is-win", won && !prize.loading);
      prizeDialog.classList.toggle("is-lose", !won && !prize.loading);
      if (title) {
        title.textContent = prize.popup_title || (won ? "Chúc mừng bạn đã thắng" : "Chúc may mắn lần sau");
      }
      if (body) {
        body.textContent = prize.popup_body || "";
        body.hidden = !prize.popup_body;
      }
      if (note) note.textContent = prize.note || "Mô phỏng trên Chơi thử — không chi trả tiền thật.";
    }
    function forcePrizeDialogVisible() {
      if (!prizeDialog) return;
      prizeDialog.setAttribute("open", "");
      prizeDialog.classList.add("is-fallback");
      const backdrop = ensurePrizeBackdrop();
      backdrop.hidden = false;
      document.body.classList.add("sim-prize-modal-open");
    }
    function closePrizeDialog() {
      if (!prizeDialog) return;
      if (prizeDialog.open && typeof prizeDialog.close === "function") {
        try {
          prizeDialog.close();
          return;
        } catch (e) {}
      }
      prizeDialog.removeAttribute("open");
      prizeDialog.classList.remove("is-fallback");
      if (prizeBackdrop) prizeBackdrop.hidden = true;
      document.body.classList.remove("sim-prize-modal-open");
      if (revealPrizeNotice && prizeNotice) prizeNotice.hidden = false;
    }
    function openPrizeDialog(prize) {
      if (prizeNotice) prizeNotice.hidden = true;
      if (!prize.loading) renderSimPrize(prize);
      fillPrizeDialog(prize);
      if (!prizeDialog) {
        if (prizeNotice) prizeNotice.hidden = false;
        return;
      }
      if (prizeDialog.open) return;
      revealPrizeNotice = true;
      let opened = false;
      if (typeof prizeDialog.showModal === "function") {
        try {
          prizeDialog.showModal();
          opened = window.getComputedStyle(prizeDialog).display !== "none";
        } catch (e) {
          opened = false;
        }
      }
      if (!opened) forcePrizeDialogVisible();
      if (!prize.loading && prizeNotice && window.getComputedStyle(prizeDialog).display === "none") {
        prizeNotice.hidden = false;
      }
    }
    if (prizeDialog) {
      prizeDialog.addEventListener("click", (ev) => {
        if (ev.target === prizeDialog) closePrizeDialog();
      });
      prizeDialog.addEventListener("close", () => {
        prizeDialog.classList.remove("is-fallback");
        if (prizeBackdrop) prizeBackdrop.hidden = true;
        document.body.classList.remove("sim-prize-modal-open");
        if (revealPrizeNotice && prizeNotice) prizeNotice.hidden = false;
      });
    }
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && prizeDialog && prizeDialog.classList.contains("is-fallback")) {
        closePrizeDialog();
      }
    });
    function paintSimResult(data) {
      const box = document.getElementById("sim-result");
      if (box) box.hidden = false;
      const balls = document.getElementById("sim-balls");
      if (balls && data.drawn) {
        balls.innerHTML = data.drawn
          .map((n) => `<li class="${(data.matched || []).includes(n) ? "is-hit" : ""}">${pad(n)}</li>`)
          .join("");
      }
      const summary = document.getElementById("sim-summary");
      if (summary) {
        summary.textContent =
          data.summary ||
          "Trùng " + data.match_count + " số · Tổng " + data.total + " · " + data.size_label + " · " + data.parity_label;
      }
    }
    function restorePicks(numbers) {
      if (!numbers || !numbers.length) return;
      selected.clear();
      picker.querySelectorAll("button").forEach((x) => x.classList.remove("on"));
      numbers.forEach((n) => {
        const num = Number(n);
        if (num >= 1 && num <= 80) {
          selected.add(num);
          picker.children[num - 1].classList.add("on");
        }
      });
      syncPicked();
    }
    const simForm = document.getElementById("sim-form");
    function playSim(ev) {
      if (ev) ev.preventDefault();
      syncPicked();
      openPrizeDialog({
        loading: true,
        popup_title: "Đang quay thử…",
        popup_body: "",
        note: "Mô phỏng trên Chơi thử — không chi trả tiền thật.",
      });
      fetch("/api/simulator/", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": cfg.csrf || "" },
        credentials: "same-origin",
        body: JSON.stringify({ numbers: Array.from(selected) }),
      })
        .then((r) => {
          if (!r.ok) throw new Error("simulator");
          return r.json();
        })
        .then((data) => {
          paintSimResult(data);
          fillPrizeDialog(data.prize || {});
          renderSimPrize(data.prize || {});
          if (prizeDialog && !prizeDialog.open) openPrizeDialog(data.prize || {});
        })
        .catch(() => {
          if (simForm) {
            simForm.removeEventListener("submit", playSim);
            simForm.submit();
          }
        });
    }
    if (simForm) simForm.addEventListener("submit", playSim);
    else document.getElementById("play-sim").addEventListener("click", playSim);
    const bootEl = document.getElementById("sim-play-boot");
    if (bootEl) {
      try {
        const boot = JSON.parse(bootEl.textContent);
        restorePicks(boot.picked);
        paintSimResult(boot);
        openPrizeDialog(boot.prize || {});
      } catch (e) {}
    }
  }

  function chartDefaults() {
    if (!window.Chart) return;
    Chart.defaults.color = "#5d6180";
    Chart.defaults.borderColor = "rgba(0, 20, 82, 0.08)";
    Chart.defaults.font.family = "Be Vietnam Pro";
    Chart.defaults.plugins.legend.labels.boxWidth = 10;
    Chart.defaults.plugins.legend.labels.padding = 14;
    Chart.defaults.plugins.tooltip.backgroundColor = "#001452";
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
  }
  function readJson(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  }
  const doughnutOpts = {
    maintainAspectRatio: false,
    cutout: "68%",
    plugins: { legend: { position: "bottom" } },
  };
  chartDefaults();
  const series = readJson("keno-series");
  const freq = readJson("keno-freq");
  const homeStats = readJson("keno-home-stats");
  if (series && window.Chart) {
    const sizeEl = document.getElementById("sizeChart");
    if (sizeEl) {
      new Chart(sizeEl, {
        type: "doughnut",
        data: {
          labels: ["Nhỏ", "Lớn"],
          datasets: [{ data: [series.size_counts.small, series.size_counts.big], backgroundColor: ["#faa61a", "#ed1b2f"], borderWidth: 0 }],
        },
        options: doughnutOpts,
      });
    }
    const parityEl = document.getElementById("parityChart");
    if (parityEl) {
      new Chart(parityEl, {
        type: "doughnut",
        data: {
          labels: ["Chẵn", "Lẻ", "Hòa"],
          datasets: [{
            data: [series.parity_counts.even, series.parity_counts.odd, series.parity_counts.draw],
            backgroundColor: ["#faa61a", "#f15922", "#001452"],
            borderWidth: 0,
          }],
        },
        options: doughnutOpts,
      });
    }
    const sizeTrend = document.getElementById("sizeTrend");
    if (sizeTrend) {
      new Chart(sizeTrend, {
        type: "bar",
        data: {
          labels: series.labels,
          datasets: [{ label: "Lớn=1 / Nhỏ=0", data: series.sizes, backgroundColor: "#ed1b2f", borderRadius: 6 }],
        },
        options: { maintainAspectRatio: false, plugins: { legend: { display: false } } },
      });
    }
    const parityTrend = document.getElementById("parityTrend");
    if (parityTrend) {
      new Chart(parityTrend, {
        type: "line",
        data: {
          labels: series.labels,
          datasets: [{ label: "Chẵn 1 / Hòa 0 / Lẻ -1", data: series.parities, borderColor: "#f15922", backgroundColor: "rgba(250, 166, 26, 0.18)", tension: 0.2, fill: true, pointRadius: 2 }],
        },
        options: { maintainAspectRatio: false, plugins: { legend: { display: false } } },
      });
    }
  }
  if (freq && window.Chart) {
    const freqEl = document.getElementById("freqChart");
    if (freqEl) {
      new Chart(freqEl, {
        type: "bar",
        data: {
          labels: freq.map((x) => x.number),
          datasets: [{ label: "Số lần", data: freq.map((x) => x.count), backgroundColor: "rgba(237, 27, 47, 0.82)", borderRadius: 3 }],
        },
        options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { maxRotation: 0, autoSkip: true } } } },
      });
    }
  }
  if (homeStats && window.Chart) {
    const mq = window.matchMedia("(min-width: 1024px)");
    const paintHomeCharts = () => {
      if (!mq.matches || window.__kenoHomeCharts) return;
      const homeSize = document.getElementById("homeSizeChart");
      if (!homeSize) return;
      window.__kenoHomeCharts = true;
      new Chart(homeSize, {
        type: "doughnut",
        data: {
          labels: ["Nhỏ", "Lớn"],
          datasets: [{
            data: [homeStats.size_counts.small, homeStats.size_counts.big],
            backgroundColor: ["#faa61a", "#ed1b2f"],
            borderWidth: 0,
          }],
        },
        options: doughnutOpts,
      });
      const homeParity = document.getElementById("homeParityChart");
      if (homeParity) {
        new Chart(homeParity, {
          type: "doughnut",
          data: {
            labels: ["Chẵn", "Lẻ", "Hòa"],
            datasets: [{
              data: [homeStats.parity_counts.even, homeStats.parity_counts.odd, homeStats.parity_counts.draw],
              backgroundColor: ["#faa61a", "#f15922", "#001452"],
              borderWidth: 0,
            }],
          },
          options: doughnutOpts,
        });
      }
      const homeSpark = document.getElementById("homeSparkChart");
      if (homeSpark) {
        new Chart(homeSpark, {
          type: "line",
          data: {
            labels: homeStats.spark_labels,
            datasets: [{
              label: "Tổng",
              data: homeStats.spark_totals,
              borderColor: "#ed1b2f",
              backgroundColor: "rgba(237, 27, 47, 0.12)",
              fill: true,
              tension: 0.35,
              pointRadius: 0,
              pointHoverRadius: 4,
              borderWidth: 2.5,
            }],
          },
          options: {
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: { callbacks: { title: (items) => "Kỳ " + (items[0] && items[0].label) } },
            },
            scales: {
              x: { grid: { display: false }, ticks: { maxTicksLimit: 8, maxRotation: 0 } },
              y: {
                suggestedMin: 600,
                suggestedMax: 1100,
                grid: { color: "rgba(0, 20, 82, 0.06)" },
              },
            },
          },
        });
      }
    };
    paintHomeCharts();
    if (mq.addEventListener) mq.addEventListener("change", paintHomeCharts);
    else if (mq.addListener) mq.addListener(paintHomeCharts);
  }

  const mapEl = document.getElementById("map");
  const posData = readJson("keno-pos");
  if (mapEl && window.L && posData) {
    const map = L.map(mapEl).setView([16.0, 106.5], 5);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OSM" }).addTo(map);
    setTimeout(() => map.invalidateSize(), 200);
    const markers = [];
    posData.forEach((p) => {
      const m = L.marker([p.lat, p.lng]).addTo(map).bindPopup(
        `<b>${p.name}</b><br>${p.address}<br><a href="${p.directions}" target="_blank">Chỉ đường</a>`
      );
      markers.push({ m, city: p.city });
    });
    const cityFilter = document.getElementById("city-filter");
    if (cityFilter) {
      cityFilter.addEventListener("change", () => {
        const v = cityFilter.value;
        document.querySelectorAll("#pos-list li").forEach((li) => {
          li.style.display = !v || li.getAttribute("data-city") === v ? "" : "none";
        });
      });
    }
    function showGeoFallback() {
      const fallback = document.getElementById("geo-fallback");
      if (fallback) fallback.hidden = false;
    }
    function applyNearby(data) {
      const list = document.getElementById("pos-list");
      if (!list) return;
      list.innerHTML = (data.results || [])
        .map(
          (p) => `<li><a href="${p.url}"><strong>${p.name}</strong></a><p>${p.address} · ${p.km} km</p>
          <a class="text-link" href="${p.directions}" target="_blank" data-track="get_directions">Chỉ đường Google Maps</a></li>`
        )
        .join("");
      if (data.results && data.results[0]) {
        map.setView([data.results[0].lat, data.results[0].lng], 13);
      }
      list.querySelectorAll("[data-track]").forEach((el) => {
        el.addEventListener("click", () => track(el.getAttribute("data-track")));
      });
    }
    function requestNearby(lat, lng) {
      fetch("/api/diem-ban/gan/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": cfg.csrf || "",
        },
        body: JSON.stringify({ lat: lat, lng: lng }),
      })
        .then((r) => r.json())
        .then(applyNearby)
        .catch(showGeoFallback);
    }
    function runGeo() {
      if (!navigator.geolocation) {
        showGeoFallback();
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => requestNearby(pos.coords.latitude, pos.coords.longitude),
        showGeoFallback,
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 30000 }
      );
    }
    const geoBtn = document.getElementById("use-geo");
    if (geoBtn) {
      geoBtn.addEventListener("click", runGeo);
      if (geoBtn.getAttribute("data-auto-gps") === "1") runGeo();
    }
  }

  const buyDialog = document.getElementById("buy-ticket-dialog");
  document.querySelectorAll("[data-buy-ticket]").forEach((btn) => {
    btn.addEventListener("click", (ev) => {
      ev.preventDefault();
      if (buyDialog && buyDialog.showModal) buyDialog.showModal();
    });
  });

  const more = document.querySelector(".desk-nav-more");
  const moreBtn = document.querySelector(".desk-nav-more-btn");
  const moreMenu = document.querySelector(".desk-nav-more-menu");
  if (more && moreBtn && moreMenu) {
    const closeMore = () => {
      moreMenu.setAttribute("hidden", "");
      moreBtn.setAttribute("aria-expanded", "false");
      more.classList.remove("is-open");
    };
    moreBtn.addEventListener("click", () => {
      const open = moreMenu.hasAttribute("hidden");
      if (open) moreMenu.removeAttribute("hidden");
      else moreMenu.setAttribute("hidden", "");
      moreBtn.setAttribute("aria-expanded", open ? "true" : "false");
      more.classList.toggle("is-open", open);
    });
    document.addEventListener("click", (ev) => {
      if (!more.contains(ev.target)) closeMore();
    });
  }

  const infoDd = document.querySelector(".desk-nav-dd");
  const infoTrigger = document.querySelector(".desk-nav-dd-trigger");
  if (infoDd && infoTrigger) {
    const setInfoOpen = (open) => {
      infoDd.classList.toggle("is-open", open);
      infoTrigger.setAttribute("aria-expanded", open ? "true" : "false");
    };
    infoDd.addEventListener("mouseenter", () => setInfoOpen(true));
    infoDd.addEventListener("mouseleave", () => setInfoOpen(false));
    infoDd.addEventListener("focusin", () => setInfoOpen(true));
    infoDd.addEventListener("focusout", (ev) => {
      if (!infoDd.contains(ev.relatedTarget)) setInfoOpen(false);
    });
    infoTrigger.addEventListener("click", (ev) => {
      if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
      if (!infoDd.classList.contains("is-open")) {
        ev.preventDefault();
        setInfoOpen(true);
      }
    });
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") setInfoOpen(false);
    });
  }
})();
