(function () {
  function $(id) {
    return document.getElementById(id);
  }
  function val(id) {
    var el = $(id);
    return el ? (el.value || "") : "";
  }
  function textOf(el) {
    if (!el) return "";
    if (el.tagName === "TRIX-EDITOR") return el.innerHTML || "";
    return el.value || "";
  }
  function bodyHtml() {
    var trix = document.querySelector("trix-editor");
    if (trix) return trix.innerHTML || "";
    return val("id_body");
  }
  function strip(html) {
    var tmp = document.createElement("div");
    tmp.innerHTML = html || "";
    return (tmp.textContent || tmp.innerText || "").replace(/\s+/g, " ").trim();
  }
  function firstParagraph(html) {
    var m = (html || "").match(/<p\b[^>]*>([\s\S]*?)<\/p>/i);
    return strip(m ? m[1] : html).slice(0, 320).toLowerCase();
  }
  function countLinks(html) {
    var matches = html.match(/href=["'](\/[^"']*|https?:\/\/[^"']+)/gi) || [];
    return matches.filter(function (h) {
      return /href=["']\//i.test(h) && !/href=["']\/\//i.test(h);
    }).length;
  }
  function missingAlt(html) {
    var imgs = html.match(/<img\b[^>]*>/gi) || [];
    return imgs.filter(function (tag) {
      var m = tag.match(/\balt\s*=\s*(['"])(.*?)\1/i);
      return !m || !m[2].trim();
    }).length;
  }
  function slugifyHint(s) {
    return (s || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  }
  function setCounter(inputId, max, warnAt) {
    var el = $(inputId);
    if (!el) return;
    var wrap = el.closest(".form-row") || el.parentElement;
    var id = inputId + "-count";
    var badge = document.getElementById(id);
    if (!badge) {
      badge = document.createElement("span");
      badge.id = id;
      badge.className = "keno-char-count";
      wrap.appendChild(badge);
    }
    var n = (el.value || "").length;
    badge.textContent = n + " / " + max;
    badge.classList.toggle("is-warn", n > warnAt);
    badge.classList.toggle("is-bad", n > max);
  }
  function check(label, ok, detail) {
    return (
      '<li class="' +
      (ok ? "ok" : "warn") +
      '"><span>' +
      (ok ? "✓" : "!") +
      "</span> " +
      label +
      (detail ? " <em>" + detail + "</em>" : "") +
      "</li>"
    );
  }
  function refresh() {
    var title = val("id_seo_title") || val("id_title") || "Tiêu đề bài viết";
    var desc = val("id_seo_description") || val("id_excerpt") || "";
    var slug = val("id_slug") || "slug";
    var kw = (val("id_focus_keyword") || "").trim().toLowerCase();
    var html = bodyHtml();
    var urlEl = $("seo-serp-url");
    var titleEl = $("seo-serp-title");
    var descEl = $("seo-serp-desc");
    var checks = $("seo-checks");
    var panel = $("keno-seo-panel");
    if (urlEl) urlEl.textContent = window.location.origin + "/bai-viet/" + slug + "/";
    if (titleEl) titleEl.textContent = title.slice(0, 70);
    if (descEl) descEl.textContent = desc.slice(0, 160);
    setCounter("id_seo_title", 60, 60);
    setCounter("id_seo_description", 160, 155);
    if (!checks) return;
    var first = firstParagraph(html);
    var links = countLinks(html);
    var alts = missingAlt(html);
    var cover = $("id_cover_alt");
    var coverFile = $("id_cover");
    var hasCover = coverFile && coverFile.value;
    var slugKw = kw ? slugifyHint(kw) : "";
    var items = [
      check("Có H1 / tiêu đề", !!val("id_title")),
      check("Từ khóa trong title", !!kw && (title.toLowerCase().indexOf(kw) !== -1), kw || "chưa nhập"),
      check("Từ khóa trong slug", !!kw && slug.indexOf(slugKw) !== -1),
      check("Từ khóa đoạn đầu", !!kw && first.indexOf(kw) !== -1),
      check("Liên kết nội bộ", links >= 1, String(links)),
      check("Ảnh trong bài có alt", alts === 0, alts ? alts + " thiếu" : ""),
      check("Alt ảnh bìa", !hasCover || !!(cover && cover.value)),
      check("SEO title ≤ 60", title.length <= 60, String(title.length)),
      check("Meta description 40–160", desc.length >= 40 && desc.length <= 160, String(desc.length)),
    ];
    checks.innerHTML = items.join("");
    if (panel) panel.setAttribute("data-ready", "1");
  }
  document.addEventListener("DOMContentLoaded", function () {
    if (!$("keno-seo-panel")) return;
    ["id_title", "id_slug", "id_excerpt", "id_seo_title", "id_seo_description", "id_focus_keyword", "id_body", "id_cover_alt"].forEach(function (id) {
      var el = $(id);
      if (el) el.addEventListener("input", refresh);
    });
    document.addEventListener("trix-change", refresh);
    refresh();
  });
})();
