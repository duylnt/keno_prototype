(function () {
  const dataEl = document.getElementById("pos-tv-data");
  const stage = document.getElementById("pos-stage");
  const footer = document.getElementById("pos-tv-footer");
  if (!dataEl || !stage) return;

  const LOOP = [
    { id: "splash", ms: 8000, footer: false },
    { id: "stop-sales", ms: 7000, footer: false },
    { id: "grid80", ms: 0, footer: false, animate: "grid80" },
    { id: "live-draw", ms: 0, footer: false, animate: "live" },
    { id: "hold-ticket", ms: 5500, footer: false },
    { id: "result", ms: 9000, footer: false },
    { id: "recent3", ms: 10000, footer: true },
    { id: "charts", ms: 12000, footer: true },
    { id: "stats", ms: 12000, footer: true },
  ];
  const FOOTER_SCREENS = new Set(LOOP.filter((s) => s.footer).map((s) => s.id));
  const BALL_MS = 420;

  let data = {};
  try {
    data = JSON.parse(dataEl.textContent);
  } catch (e) {
    data = {};
  }

  const STORE = "keno_pos_tv_cycle";
  let idx = 0;
  let paused = false;
  let timer = null;
  let cycleAt = Date.now();
  let countdown = Number(data.countdown) || 0;
  let sizeChart = null;
  let parityChart = null;
  let animToken = 0;

  function pad(n) {
    return String(n).padStart(2, "0");
  }
  function fmt(sec) {
    const s = Math.max(0, Number(sec) || 0);
    return pad(Math.floor(s / 60)) + ":" + pad(s % 60);
  }
  function appear() {
    return (data.latest && data.latest.numbers) || [];
  }

  function paintCountdown() {
    stage.querySelectorAll("[data-pos-cd]").forEach((el) => {
      el.textContent = fmt(countdown);
    });
    stage.querySelectorAll("[data-pos-next]").forEach((el) => {
      if (data.next_draw_label) el.textContent = data.next_draw_label;
      else if (data.next_draw) el.textContent = data.next_draw;
    });
  }

  function showScreen(id) {
    animToken += 1;
    stage.querySelectorAll(".pos-screen").forEach((el) => {
      el.classList.toggle("is-on", el.getAttribute("data-screen") === id);
    });
    if (footer) footer.classList.toggle("is-on", FOOTER_SCREENS.has(id));
    stage.classList.toggle("has-footer-on", FOOTER_SCREENS.has(id));
    paintMeta();
    if (id === "result") renderResult();
    if (id === "recent3") renderRecent3();
    if (id === "stats") renderStats();
    if (id === "charts") requestAnimationFrame(drawCharts);
  }

  function paintMeta() {
    paintCountdown();
    stage.querySelectorAll("[data-pos-period]").forEach(function (el) {
      el.textContent = data.current_display || "—";
    });
  }

  function badge(label, count, key) {
    return (
      '<span class="pos-badge is-' +
      (key || "draw") +
      '">' +
      label +
      " (" +
      count +
      ")</span>"
    );
  }

  function renderResult() {
    const latest = data.latest;
    const grid = document.getElementById("pos-result-balls");
    const badges = document.getElementById("pos-result-badges");
    const lines = document.getElementById("pos-result-lines");
    if (!latest || !grid) return;
    grid.innerHTML = (latest.numbers || []).map(function (n) {
      return ballHtml(n);
    }).join("");
    if (badges) {
      badges.innerHTML =
        badge(latest.size_label, latest.size_count, latest.size_key) +
        badge(latest.parity_label, latest.parity_count, latest.parity_key);
    }
    if (lines) {
      lines.innerHTML =
        "<p>LỚN " +
        latest.big +
        " | NHỎ " +
        latest.small +
        "</p><p>CHẴN " +
        latest.even +
        " | LẺ " +
        latest.odd +
        "</p>";
    }
  }

  function renderRecent3() {
    const wrap = document.getElementById("pos-recent3");
    if (!wrap) return;
    const rows = data.recent3 || [];
    wrap.innerHTML = rows
      .map(function (d) {
        const balls = (d.numbers || [])
          .map(function (n) {
            return ballHtml(n);
          })
          .join("");
        return (
          '<article class="pos-draw-block"><div class="pos-draw-head"><span>Kỳ quay ' +
          (d.period_display || "") +
          "</span>" +
          badge(d.size_label, d.size_count, d.size_key) +
          badge(d.parity_label, d.parity_count, d.parity_key) +
          '</div><div class="pos-balls-20">' +
          balls +
          "</div></article>"
        );
      })
      .join("");
  }

  function metaBalls(items, white, unit) {
    return (items || [])
      .map(function (x) {
        return (
          '<span class="tv-ball-meta">' +
          ballHtml(x.number, white ? "is-white" : "") +
          "<small>" +
          x.count +
          " " +
          unit +
          "</small></span>"
        );
      })
      .join("");
  }

  function renderStats() {
    const map = {
      "pos-hot5": [data.hot5, false, "lần"],
      "pos-hot100": [data.hot100, false, "lần"],
      "pos-cold5": [data.cold5, true, "lần"],
      "pos-cold100": [data.cold100, true, "lần"],
      "pos-hits": [data.hit_streaks, false, "kỳ"],
      "pos-misses": [data.miss_streaks, true, "kỳ"],
    };
    Object.keys(map).forEach(function (id) {
      const el = document.getElementById(id);
      if (!el) return;
      const spec = map[id];
      el.innerHTML = metaBalls(spec[0], spec[1], spec[2]);
    });
  }

  function ballHtml(n, extra) {
    const cls = extra ? "tv-ball " + extra : "tv-ball";
    return '<span class="' + cls + '">' + pad(n) + "</span>";
  }

  function runLive() {
    const nums = appear();
    const slots = document.getElementById("pos-live-slots");
    const remain = document.getElementById("pos-remain");
    const cBig = document.getElementById("pos-c-big");
    const cSmall = document.getElementById("pos-c-small");
    const cEven = document.getElementById("pos-c-even");
    const cOdd = document.getElementById("pos-c-odd");
    if (!slots) return Promise.resolve();
    slots.innerHTML = "";
    for (let i = 0; i < 20; i++) {
      const d = document.createElement("div");
      d.className = "pos-slot";
      slots.appendChild(d);
    }
    let big = 0,
      small = 0,
      even = 0,
      odd = 0;
    const token = ++animToken;
    return new Promise((resolve) => {
      let i = 0;
      function step() {
        if (token !== animToken) return resolve();
        if (i >= nums.length) {
          if (remain) remain.textContent = "0 / 20";
          return setTimeout(resolve, 1400);
        }
        const n = nums[i];
        const slot = slots.children[i];
        if (slot) {
          slot.className = "";
          slot.innerHTML = ballHtml(n, "is-drop");
        }
        if (n >= 41) big += 1;
        else small += 1;
        if (n % 2 === 0) even += 1;
        else odd += 1;
        if (cBig) cBig.textContent = String(big);
        if (cSmall) cSmall.textContent = String(small);
        if (cEven) cEven.textContent = String(even);
        if (cOdd) cOdd.textContent = String(odd);
        if (remain) remain.textContent = 20 - (i + 1) + " / 20";
        i += 1;
        setTimeout(step, BALL_MS);
      }
      if (remain) remain.textContent = "20 / 20";
      if (cBig) cBig.textContent = "0";
      if (cSmall) cSmall.textContent = "0";
      if (cEven) cEven.textContent = "0";
      if (cOdd) cOdd.textContent = "0";
      setTimeout(step, 280);
    });
  }

  function runGrid80() {
    const grid = document.getElementById("pos-grid-80");
    const nums = appear();
    if (!grid) return Promise.resolve();
    grid.querySelectorAll(".tv-ball").forEach((el) => {
      el.className = "tv-ball is-ghost";
      el.textContent = "";
    });
    const token = ++animToken;
    return new Promise((resolve) => {
      let i = 0;
      function step() {
        if (token !== animToken) return resolve();
        if (i >= nums.length) return setTimeout(resolve, 1200);
        const n = nums[i];
        const cell = grid.querySelector('[data-n="' + n + '"]');
        if (cell) {
          cell.className = "tv-ball is-drop is-spark";
          cell.textContent = pad(n);
        }
        i += 1;
        setTimeout(step, BALL_MS);
      }
      setTimeout(step, 200);
    });
  }

  function numberedPlugin() {
    return {
      id: "posNumberedPoints",
      afterDatasetsDraw: function (chart) {
        const ctx = chart.ctx;
        const meta = chart.getDatasetMeta(0);
        const ds = chart.data.datasets[0];
        const nums = ds.pointNumbers || [];
        const colors = ds.pointColors || [];
        meta.data.forEach(function (pt, i) {
          const pos = pt.getProps(["x", "y"], true);
          const color = colors[i] || "#FFD000";
          const area = chart.chartArea || {};
          const span = Math.min(area.right - area.left || 240, area.bottom - area.top || 80);
          const inPip = !!(chart.canvas && chart.canvas.closest && chart.canvas.closest(".live-pip"));
          const r = inPip
            ? Math.max(3, Math.min(6, span / 28))
            : Math.max(4, Math.min(14, span / 22));
          const fontPx = inPip
            ? Math.max(4, Math.min(7, r * 0.85))
            : Math.max(6, Math.min(12, r * 0.85));
          ctx.save();
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, r, 0, Math.PI * 2);
          ctx.fillStyle = color;
          ctx.fill();
          ctx.lineWidth = Math.max(1, r / 8);
          ctx.strokeStyle = "#fff";
          ctx.stroke();
          ctx.fillStyle = color === "#111111" || color === "#111" ? "#fff" : "#111";
          ctx.font = "700 " + fontPx + "px Be Vietnam Pro, Arial, sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(String(nums[i] != null ? nums[i] : ""), pos.x, pos.y + 0.5);
          ctx.restore();
        });
      },
    };
  }

  function makeChart(canvas, payload, yLabels, yMax) {
    if (!window.Chart || !canvas || !payload) return null;
    const inPip = !!(window.KENO_POS && window.KENO_POS.pip) ||
      !!(canvas.closest && canvas.closest(".live-pip"));
    const w = canvas.clientWidth || (inPip ? 180 : 320);
    const h = canvas.clientHeight || (inPip ? 48 : 140);
    const tick = inPip ? Math.max(5, Math.min(7, w / 56)) : Math.max(7, Math.min(12, w / 48));
    const padR = inPip ? Math.max(4, Math.min(10, w / 28)) : Math.max(12, Math.min(28, w / 22));
    const padT = inPip ? Math.max(4, Math.min(8, h / 12)) : Math.max(16, Math.min(30, h / 7));
    return new window.Chart(canvas, {
      type: "line",
      data: {
        labels: (payload.values || []).map(function (_, i) {
          return i + 1;
        }),
        datasets: [
          {
            data: payload.values || [],
            borderColor: "rgba(255,255,255,0.85)",
            borderWidth: inPip ? 1 : 2,
            pointRadius: 0,
            pointHoverRadius: 0,
            tension: 0.15,
            pointNumbers: payload.counts || [],
            pointColors: payload.colors || [],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 600 },
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        layout: { padding: { top: padT, right: padR, left: inPip ? 2 : 4, bottom: inPip ? 2 : 6 } },
        scales: {
          x: { display: false },
          y: {
            min: -0.35,
            max: yMax + 0.35,
            ticks: {
              display: !inPip,
              stepSize: 1,
              color: "#fff",
              padding: 4,
              font: { weight: "700", size: tick },
              callback: function (v) {
                return yLabels[v] || "";
              },
            },
            grid: { color: "rgba(255,255,255,0.22)", drawBorder: false },
          },
        },
      },
      plugins: [numberedPlugin()],
    });
  }

  function drawCharts() {
    if (!window.Chart) return;
    const sizeCanvas = document.getElementById("pos-chart-size");
    const parityCanvas = document.getElementById("pos-chart-parity");
    if (sizeChart) {
      sizeChart.destroy();
      sizeChart = null;
    }
    if (parityChart) {
      parityChart.destroy();
      parityChart = null;
    }
    sizeChart = makeChart(sizeCanvas, data.chart_size, { 0: "NHỎ", 1: "HOÀ", 2: "LỚN" }, 2);
    parityChart = makeChart(
      parityCanvas,
      data.chart_parity,
      { 0: "LẺ", 1: "LẺ 11-12", 2: "HOÀ", 3: "CHẴN 11-12", 4: "CHẴN" },
      4
    );
  }

  function screenDuration(spec) {
    const n = appear().length || 20;
    if (spec.animate === "grid80") return 200 + n * BALL_MS + 1200;
    if (spec.animate === "live") return 280 + n * BALL_MS + 1400;
    return spec.ms || 400;
  }

  function loopDurations() {
    return LOOP.map(screenDuration);
  }

  function offsetTo(id) {
    let t = 0;
    const durs = loopDurations();
    for (let i = 0; i < LOOP.length; i++) {
      if (LOOP[i].id === id) return t;
      t += durs[i];
    }
    return 0;
  }

  function clockState() {
    const durs = loopDurations();
    const total = durs.reduce(function (a, b) {
      return a + b;
    }, 0) || 1;
    const elapsed = Math.max(0, Date.now() - cycleAt);
    let t = elapsed % total;
    for (let i = 0; i < LOOP.length; i++) {
      if (t < durs[i]) return { idx: i, into: t, remain: durs[i] - t };
      t -= durs[i];
    }
    return { idx: 0, into: 0, remain: durs[0] };
  }

  function persistCycle() {
    try {
      localStorage.setItem(
        STORE,
        JSON.stringify({ period: data.current_period || "", at: cycleAt })
      );
    } catch (e) {}
  }

  function restoreCycle() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORE) || "null");
      const period = data.current_period || "";
      if (saved && saved.period === period && saved.at) {
        cycleAt = saved.at;
        return;
      }
    } catch (e) {}
    cycleAt = Date.now();
    persistCycle();
  }

  function snapLive() {
    const nums = appear();
    const slots = document.getElementById("pos-live-slots");
    const remain = document.getElementById("pos-remain");
    const cBig = document.getElementById("pos-c-big");
    const cSmall = document.getElementById("pos-c-small");
    const cEven = document.getElementById("pos-c-even");
    const cOdd = document.getElementById("pos-c-odd");
    if (!slots) return;
    slots.innerHTML = "";
    let big = 0,
      small = 0,
      even = 0,
      odd = 0;
    for (let i = 0; i < 20; i++) {
      const d = document.createElement("div");
      if (i < nums.length) {
        const n = nums[i];
        d.innerHTML = ballHtml(n);
        if (n >= 41) big += 1;
        else small += 1;
        if (n % 2 === 0) even += 1;
        else odd += 1;
      } else {
        d.className = "pos-slot";
      }
      slots.appendChild(d);
    }
    if (remain) remain.textContent = "0 / 20";
    if (cBig) cBig.textContent = String(big);
    if (cSmall) cSmall.textContent = String(small);
    if (cEven) cEven.textContent = String(even);
    if (cOdd) cOdd.textContent = String(odd);
  }

  function snapGrid80() {
    const grid = document.getElementById("pos-grid-80");
    const nums = appear();
    if (!grid) return;
    grid.querySelectorAll(".tv-ball").forEach(function (el) {
      el.className = "tv-ball is-ghost";
      el.textContent = "";
    });
    nums.forEach(function (n) {
      const cell = grid.querySelector('[data-n="' + n + '"]');
      if (cell) {
        cell.className = "tv-ball";
        cell.textContent = pad(n);
      }
    });
  }

  function playCurrent() {
    if (paused) return;
    const spec = LOOP[idx];
    const st = clockState();
    showScreen(spec.id);
    if (spec.animate === "live") {
      if (st.into > 800) snapLive();
      else runLive();
    } else if (spec.animate === "grid80") {
      if (st.into > 800) snapGrid80();
      else runGrid80();
    }
    armNext();
  }

  function armNext() {
    clearTimeout(timer);
    if (paused) return;
    const wait = Math.max(120, clockState().remain);
    timer = setTimeout(function () {
      idx = clockState().idx;
      playCurrent();
    }, wait);
  }

  function jumpTo(id) {
    const found = LOOP.findIndex(function (s) {
      return s.id === id;
    });
    idx = found < 0 ? 0 : found;
    cycleAt = Date.now() - offsetTo(LOOP[idx].id);
    persistCycle();
    playCurrent();
  }

  function next() {
    jumpTo(LOOP[(idx + 1) % LOOP.length].id);
  }
  function prev() {
    jumpTo(LOOP[(idx - 1 + LOOP.length) % LOOP.length].id);
  }

  function applyPayload(nextData) {
    if (!nextData || nextData.heartbeat) {
      if (nextData && nextData.countdown != null) countdown = Number(nextData.countdown) || 0;
      paintCountdown();
      return;
    }
    const prevPeriod = data.current_period;
    data = nextData;
    countdown = Number(data.countdown) || 0;
    paintCountdown();
    if (data.current_period && prevPeriod && data.current_period !== prevPeriod) {
      jumpTo("live-draw");
    }
  }

  function poll() {
    const url = (window.KENO_POS && window.KENO_POS.api) || "";
    if (!url) return;
    fetch(url)
      .then(function (r) {
        return r.json();
      })
      .then(applyPayload)
      .catch(function () {});
  }

  if (document.body.classList.contains("page-live")) {
    document.addEventListener("keydown", function (ev) {
      const k = ev.key.toLowerCase();
      if (k === "arrowright" || k === "n") {
        ev.preventDefault();
        next();
      } else if (k === "arrowleft" || k === "p") {
        ev.preventDefault();
        prev();
      } else if (k === " " && ev.target === document.body) {
        ev.preventDefault();
        paused = !paused;
        if (!paused) playCurrent();
        else clearTimeout(timer);
      }
    });
  }

  restoreCycle();
  idx = clockState().idx;
  paintCountdown();
  setInterval(function () {
    if (countdown > 0) countdown -= 1;
    paintCountdown();
  }, 1000);
  setInterval(poll, 8000);
  playCurrent();
})();
