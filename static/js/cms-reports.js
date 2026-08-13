(function () {
  function readJson(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  }

  function palette() {
    return {
      ink: "#18181b",
      muted: "#71717a",
      line: "#e4e4e7",
      accent: "#c41e3a",
      accentSoft: "rgba(196, 30, 58, 0.12)",
      inkSoft: "rgba(24, 24, 27, 0.55)",
    };
  }

  function applyDefaults() {
    if (typeof Chart === "undefined") return;
    var c = palette();
    Chart.defaults.color = c.muted;
    Chart.defaults.borderColor = c.line;
    Chart.defaults.font.family = "Inter, ui-sans-serif, system-ui, sans-serif";
    Chart.defaults.font.size = 11;
    Chart.defaults.plugins.legend.labels.boxWidth = 10;
    Chart.defaults.plugins.legend.labels.boxHeight = 10;
    Chart.defaults.plugins.legend.display = true;
    Chart.defaults.maintainAspectRatio = false;
  }

  function lineChart(canvasId, labels, datasets) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return;
    var c = palette();
    new Chart(canvas, {
      type: "line",
      data: { labels: labels, datasets: datasets },
      options: {
        interaction: { mode: "index", intersect: false },
        plugins: { legend: { position: "bottom" } },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: 8 } },
          y: { beginAtZero: true, grid: { color: c.line } },
        },
      },
    });
  }

  function barChart(canvasId, labels, values) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return;
    var c = palette();
    new Chart(canvas, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Giá trị",
            data: values,
            backgroundColor: c.accent,
            borderRadius: 4,
            maxBarThickness: 28,
          },
        ],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, grid: { color: c.line } },
        },
      },
    });
  }

  function initHome() {
    var ga4 = readJson("keno-ga4-series");
    if (ga4 && ga4.length) {
      lineChart(
        "keno-home-traffic",
        ga4.map(function (r) { return r.date.slice(5); }),
        [
          {
            label: "Người dùng hoạt động",
            data: ga4.map(function (r) { return r.active; }),
            borderColor: "#c41e3a",
            backgroundColor: "rgba(196,30,58,0.08)",
            fill: true,
            tension: 0.3,
            pointRadius: 0,
            borderWidth: 2,
          },
          {
            label: "Phiên organic",
            data: ga4.map(function (r) { return r.organic; }),
            borderColor: "#18181b",
            backgroundColor: "transparent",
            tension: 0.3,
            pointRadius: 0,
            borderWidth: 1.5,
          },
        ]
      );
    }
    var funnel = readJson("keno-funnel-series");
    if (funnel && funnel.length) {
      barChart(
        "keno-home-funnel",
        funnel.map(function (s) { return s.stage; }),
        funnel.map(function (s) { return s.primary; })
      );
    }
  }

  function initReports() {
    var ga4 = readJson("keno-ga4-series");
    if (ga4 && ga4.length) {
      lineChart(
        "keno-ga4-chart",
        ga4.map(function (r) { return r.date.slice(5); }),
        [
          {
            label: "Active users",
            data: ga4.map(function (r) { return r.active; }),
            borderColor: "#c41e3a",
            tension: 0.3,
            pointRadius: 0,
            borderWidth: 2,
          },
          {
            label: "Organic",
            data: ga4.map(function (r) { return r.organic; }),
            borderColor: "#71717a",
            tension: 0.3,
            pointRadius: 0,
            borderWidth: 1.5,
          },
          {
            label: "New users",
            data: ga4.map(function (r) { return r.new; }),
            borderColor: "#a1a1aa",
            tension: 0.3,
            pointRadius: 0,
            borderWidth: 1.5,
          },
        ]
      );
    }
    var gsc = readJson("keno-gsc-series");
    if (gsc && gsc.length) {
      lineChart(
        "keno-gsc-chart",
        gsc.map(function (r) { return r.date.slice(5); }),
        [
          {
            label: "Impressions",
            data: gsc.map(function (r) { return r.impressions; }),
            borderColor: "#c41e3a",
            tension: 0.3,
            pointRadius: 0,
            borderWidth: 2,
          },
          {
            label: "Clicks",
            data: gsc.map(function (r) { return r.clicks; }),
            borderColor: "#18181b",
            tension: 0.3,
            pointRadius: 0,
            borderWidth: 1.5,
          },
        ]
      );
    }
    var events = readJson("keno-event-bars");
    if (events && events.length) {
      barChart(
        "keno-events-chart",
        events.map(function (e) { return e.name; }),
        events.map(function (e) { return e.value; })
      );
    }
    var funnel = readJson("keno-funnel-series");
    if (funnel && funnel.length && document.getElementById("keno-funnel-chart")) {
      barChart(
        "keno-funnel-chart",
        funnel.map(function (s) { return s.stage; }),
        funnel.map(function (s) { return s.primary; })
      );
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    applyDefaults();
    initHome();
    initReports();
  });
})();
