"""AI article drafts. Never auto-publish. Original Vietnamese; no copied crawl text."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from django.conf import settings

from .utils import slugify_vi, strip_tags

SYSTEM_PROMPT = """Bạn là biên tập viên tiếng Việt cho website cộng đồng Keno (prototype).
Quy tắc bắt buộc:
- Viết ORIGINAL, không sao chép bài đã crawl hay đoạn trích nghiên cứu.
- Không phải kênh chính thức Vietlott; không bán vé trực tuyến.
- Không cam kết trúng, không “chắc thắng”, không soi cầu đảm bảo.
- Có disclaimer chơi có trách nhiệm.
- Trả lời đúng câu hỏi ngay đoạn mở đầu.
- Cấu trúc: H1 (trùng tiêu đề), intro, các H2, key takeaways, FAQ.
- Ngôn ngữ: tiếng Việt, rõ ràng, có thể trích dẫn bởi AI search.
Trả về JSON thuần (không markdown) với khóa:
title, slug, excerpt, seo_title, seo_description, focus_keyword,
key_takeaways (mảng chuỗi), body_html, faqs (mảng {question, answer}),
internal_link_suggestions (mảng {anchor, path}).
path gợi ý chỉ dùng path có sẵn: /ket-qua/, /thong-ke/, /do-ve/, /diem-ban/, /huong-dan/, /thong-tin/, /cong-dong/, /bai-viet/, /choi-thu/.
"""

DISCLAIMER_HTML = (
    "<h2>Chơi có trách nhiệm</h2>"
    "<p>Keno là sản phẩm giải trí. Không có cách nào đảm bảo trúng thưởng. "
    "Thống kê lịch sử không làm tăng khả năng thắng. Không chơi quá khả năng tài chính. "
    "Website này không bán vé và không phải kênh chính thức của Vietlott.</p>"
)

INTERNAL_DEFAULT = [
    {"anchor": "Xem kết quả Keno", "path": "/ket-qua/"},
    {"anchor": "Cách chơi Keno", "path": "/huong-dan/"},
    {"anchor": "Thống kê Lớn/Nhỏ Chẵn/Lẻ", "path": "/thong-ke/"},
    {"anchor": "Tìm điểm bán gần bạn", "path": "/diem-ban/"},
]


def api_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or getattr(settings, "OPENAI_API_KEY", "") or getattr(settings, "ANTHROPIC_API_KEY", ""))


def _openai_key() -> str:
    return os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "") or ""


def _anthropic_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY") or getattr(settings, "ANTHROPIC_API_KEY", "") or ""


def _parse_json(text: str) -> dict:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def _call_openai(user: str) -> dict:
    model = os.getenv("OPENAI_MODEL") or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "temperature": 0.6,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_openai_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    return _parse_json(content)


def _call_anthropic(user: str) -> dict:
    model = os.getenv("ANTHROPIC_MODEL") or getattr(settings, "ANTHROPIC_MODEL", "claude-sonnet-4-0")
    payload = {
        "model": model,
        "max_tokens": 4000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": _anthropic_key(),
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = "".join(part.get("text", "") for part in data.get("content", []) if part.get("type") == "text")
    return _parse_json(content)


def _user_prompt(topic: str, outline: str = "", research_notes: str = "") -> str:
    notes = strip_tags(research_notes)[:800]
    return (
        f"Chủ đề: {topic}\n"
        f"Dàn ý gợi ý (không bắt buộc):\n{outline or '(tự đề xuất H2 phù hợp SEO + LLM-SEO)'}\n"
        f"Gợi ý khoảng trống thị trường / heading đối thủ (CHỈ dùng để chọn góc viết, CẤM sao chép câu chữ):\n"
        f"{notes or '(không có)'}\n"
        "Viết bài hữu ích cho người chơi Việt Nam muốn hiểu sản phẩm Keno."
    )


def template_draft(topic: str, outline: str = "", research_notes: str = "") -> dict:
    """High-quality fallback when no LLM API key is configured."""
    title = topic.strip() or "Keno là gì và chơi như thế nào?"
    if not title.lower().startswith("keno") and "keno" not in title.lower():
        title = f"{title} (Keno)"
    slug = slugify_vi(title)
    keyword = "keno"
    lowered = title.lower()
    if "cách chơi" in lowered:
        keyword = "cách chơi keno"
    elif "thống kê" in lowered:
        keyword = "thống kê keno"
    elif "kết quả" in lowered:
        keyword = "kết quả keno"
    elif "điểm bán" in lowered:
        keyword = "điểm bán keno"
    elif "là gì" in lowered:
        keyword = "keno là gì"

    h2s = [ln.strip(" #-") for ln in (outline or "").splitlines() if ln.strip()]
    if not h2s:
        h2s = [
            "Keno hoạt động như thế nào?",
            "Người chơi cần biết gì trước khi mua vé",
            "Tra cứu kết quả và thống kê trên website này",
            "Khác gì với các sản phẩm xổ số khác?",
        ]
    h2_html = []
    for heading in h2s[:6]:
        h2_html.append(
            f"<h2>{heading}</h2>"
            f"<p>{heading} được giải thích theo thông tin sản phẩm: Keno mở thưởng mỗi 8 phút "
            f"(06:00–21:52), mỗi kỳ quay 20 số từ 01 đến 80. Người chơi chọn 1–10 số hoặc "
            f"cược Lớn/Nhỏ, Chẵn/Lẻ theo quy định tại điểm bán. Đây là mô tả sản phẩm, "
            f"không phải công cụ dự đoán.</p>"
        )

    research_block = ""
    if research_notes:
        research_block = (
            "<h2>Góc nội dung nên làm rõ</h2>"
            "<p>Từ phân tích thị trường (chỉ lấy chủ đề, không sao chép bài gốc), bài này tập trung trả lời trực tiếp câu hỏi người dùng và bổ sung phần còn thiếu trên trang của chúng ta.</p>"
        )

    body = (
        f"<p><strong>{title}</strong> — Keno là sản phẩm xổ số nhanh: chọn số, mua vé tại điểm bán chính thức, "
        f"đối chiếu kết quả theo từng kỳ 8 phút. Trang này giải thích {title.lower()} bằng ngôn ngữ rõ ràng, "
        f"dành cho người mới và người đang theo dõi kỳ quay. Website không bán vé trực tuyến và không phải kênh chính thức Vietlott.</p>"
        + "".join(h2_html)
        + research_block
        + "<h2>Liên kết hữu ích</h2><ul>"
        + "".join(f'<li><a href="{x["path"]}">{x["anchor"]}</a></li>' for x in INTERNAL_DEFAULT)
        + "</ul>"
        + DISCLAIMER_HTML
    )
    takeaways = [
        "Keno mở thưởng mỗi 8 phút; mỗi kỳ quay 20 số từ 01–80.",
        "Vé chỉ mua tại điểm bán chính thức — không mua trên website này.",
        "Thống kê lịch sử chỉ để tham khảo, không dự đoán kỳ tới.",
        "Chơi có trách nhiệm; không tin cam kết trúng thưởng.",
    ]
    faqs = [
        {
            "question": f"{title} — tóm tắt trong 2 câu?",
            "answer": (
                f"{title} liên quan đến sản phẩm Keno: xổ số nhanh 8 phút/kỳ. "
                "Hãy tra cứu kết quả và đọc hướng dẫn trên trang này, rồi mua vé tại điểm bán nếu bạn quyết định chơi."
            ),
        },
        {
            "question": "Website này có phải Vietlott chính thức không?",
            "answer": "Không. Đây là prototype cộng đồng tra cứu, thống kê và tìm điểm bán. Không bán vé trực tuyến.",
        },
        {
            "question": "Thống kê có giúp trúng Keno không?",
            "answer": "Không. Thống kê mô tả dữ liệu quá khứ. Không có phương pháp nào đảm bảo kết quả kỳ tới.",
        },
    ]
    seo_title = title if len(title) <= 60 else title[:57] + "…"
    excerpt = (
        f"Giải thích {title.lower()}: cách Keno vận hành, nơi mua vé, cách tra cứu kết quả "
        "và lưu ý chơi có trách nhiệm."
    )
    return {
        "title": title[:200],
        "slug": slug,
        "excerpt": excerpt[:400],
        "seo_title": seo_title,
        "seo_description": excerpt[:160],
        "focus_keyword": keyword,
        "key_takeaways": takeaways,
        "body_html": body,
        "faqs": faqs,
        "internal_link_suggestions": INTERNAL_DEFAULT,
        "source": "template",
    }


def generate_article(topic: str, outline: str = "", research_notes: str = "") -> dict:
    user = _user_prompt(topic, outline, research_notes)
    source = "template"
    data = None
    error = ""
    try:
        if _openai_key():
            data = _call_openai(user)
            source = "openai"
        elif _anthropic_key():
            data = _call_anthropic(user)
            source = "anthropic"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as exc:
        error = str(exc)[:240]
        data = None

    if not data:
        draft = template_draft(topic, outline, research_notes)
        draft["api_error"] = error
        draft["api_configured"] = api_configured()
        return draft

    takeaways = data.get("key_takeaways") or []
    if isinstance(takeaways, str):
        takeaways = [ln.strip("- •") for ln in takeaways.splitlines() if ln.strip()]
    faqs = data.get("faqs") or []
    links = data.get("internal_link_suggestions") or INTERNAL_DEFAULT
    body = data.get("body_html") or data.get("body") or ""
    if "trách nhiệm" not in body.lower():
        body += DISCLAIMER_HTML
    title = (data.get("title") or topic)[:200]
    return {
        "title": title,
        "slug": slugify_vi(data.get("slug") or title),
        "excerpt": (data.get("excerpt") or "")[:400],
        "seo_title": (data.get("seo_title") or title)[:70],
        "seo_description": (data.get("seo_description") or data.get("excerpt") or "")[:160],
        "focus_keyword": (data.get("focus_keyword") or "keno")[:80],
        "key_takeaways": takeaways[:8],
        "body_html": body,
        "faqs": faqs,
        "internal_link_suggestions": links,
        "source": source,
        "api_configured": True,
        "api_error": "",
    }


def save_draft(draft: dict, category=None):
    from apps.content.models import Article, ArticleCategory, ArticleFAQ

    if category is None:
        category = (
            ArticleCategory.objects.filter(slug__icontains="thong-tin").first()
            or ArticleCategory.objects.order_by("sort_order").first()
        )
        if category is None:
            category = ArticleCategory.objects.create(
                name="Thông tin Keno", slug="thong-tin-keno", sort_order=1
            )
    slug = draft["slug"]
    base = slug
    n = 2
    while Article.objects.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    takeaways = draft.get("key_takeaways") or []
    if isinstance(takeaways, list):
        takeaways_txt = "\n".join(str(x) for x in takeaways)
    else:
        takeaways_txt = str(takeaways)
    article = Article.objects.create(
        category=category,
        title=draft["title"],
        slug=slug,
        excerpt=draft.get("excerpt") or "",
        body=draft.get("body_html") or "",
        seo_title=draft.get("seo_title") or "",
        seo_description=draft.get("seo_description") or "",
        focus_keyword=draft.get("focus_keyword") or "",
        key_takeaways=takeaways_txt,
        author_name="Ban biên tập Keno",
        is_published=False,
        robots_noindex=True,
    )
    for i, faq in enumerate(draft.get("faqs") or []):
        q = faq.get("question") or faq.get("q") or ""
        a = faq.get("answer") or faq.get("a") or ""
        if q and a:
            ArticleFAQ.objects.create(article=article, question=q[:300], answer=a, sort_order=i)
    return article
