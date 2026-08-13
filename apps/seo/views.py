from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.content.models import Article
from apps.core.models import SiteSettings

from .models import SeoStatus
from .utils import site_origin


def _mark_sitemap():
    status = SeoStatus.load()
    status.sitemap_generated_at = timezone.now()
    status.save(update_fields=["sitemap_generated_at"])


@require_GET
def robots_txt(request):
    origin = site_origin()
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /cms/\n"
        "Disallow: /api/\n"
        "Disallow: /pos/quet-ma/\n"
        "\n"
        "# AI / answer-engine crawlers — informational Keno site, default allow\n"
        "User-agent: GPTBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: ChatGPT-User\n"
        "Allow: /\n"
        "\n"
        "User-agent: ClaudeBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: PerplexityBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: Google-Extended\n"
        "Allow: /\n"
        "\n"
        "User-agent: Applebot-Extended\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {origin}/sitemap.xml\n"
        f"# LLM context: {origin}/llms.txt\n"
    )
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


@require_GET
def llms_txt(request):
    site = SiteSettings.load()
    origin = site_origin()
    lines = [
        f"# {site.site_name}",
        f"> {site.tagline}",
        "",
        "## About",
        f"{site.support_note.strip()}",
        "Đây là website cộng đồng / prototype tra cứu Keno: kết quả theo kỳ 8 phút, thống kê Lớn-Nhỏ Chẵn-Lẻ,",
        "hướng dẫn cách chơi, cộng đồng và tìm điểm bán. Không bán vé trực tuyến.",
        "Không phải website chính thức của Vietlott (vietlott.vn).",
        "",
        "## Primary pages",
        f"- [Trang chủ]({origin}/): kết quả kỳ mới nhất và lối tắt tiện ích",
        f"- [Kết quả]({origin}/ket-qua/): kỳ mới nhất, đếm ngược 8 phút",
        f"- [Kết quả hôm nay]({origin}/ket-qua/hom-nay/): mọi kỳ trong ngày",
        f"- [Lịch sử]({origin}/ket-qua/lich-su/): tra cứu theo ngày",
        f"- [Thống kê]({origin}/thong-ke/): tần suất, Lớn/Nhỏ, Chẵn/Lẻ (tham khảo, không dự đoán)",
        f"- [Dò vé]({origin}/do-ve/): đối chiếu dãy số với kỳ quay",
        f"- [Thông tin]({origin}/thong-tin/): cách chơi, chơi thử, trách nhiệm, nội quy, bài viết",
        f"- [Chơi thử]({origin}/choi-thu/): mô phỏng, không dùng tiền thật",
        f"- [Cách chơi]({origin}/huong-dan/): Keno là gì, chọn số, mua vé tại điểm bán",
        f"- [Điểm bán]({origin}/diem-ban/): tìm điểm gần bạn",
        f"- [Cộng đồng]({origin}/cong-dong/): thảo luận có kiểm duyệt",
        f"- [Bài viết]({origin}/bai-viet/): hướng dẫn và kiến thức nền",
        f"- [Chơi có trách nhiệm]({origin}/trang/choi-co-trach-nhiem/)",
        "",
        "## Facts",
        "- Keno: mỗi kỳ quay 20 số từ 01 đến 80; người chơi chọn 1–10 số.",
        "- Nhịp mở thưởng: 8 phút/kỳ, khung 06:00–21:52 (theo mô tả sản phẩm).",
        "- Lớn/Nhỏ dựa trên tổng 20 số; Chẵn/Lẻ dựa trên số lượng số chẵn.",
        "- Vé chỉ được phân phối tại điểm bán chính thức.",
        "- Thống kê trên site không phải công cụ dự đoán và không làm tăng khả năng trúng.",
        "",
        "## Optional",
        f"- Full index: {origin}/llms-full.txt",
        f"- Sitemap: {origin}/sitemap.xml",
        f"- Contact note: {site.facebook_group_name}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


@require_GET
def llms_full_txt(request):
    site = SiteSettings.load()
    origin = site_origin()
    articles = Article.objects.filter(is_published=True, robots_noindex=False).select_related("category")
    lines = [
        f"# {site.site_name} — full LLM index",
        f"> Bản mở rộng của {origin}/llms.txt. Tóm tắt bài đã xuất bản (nội dung gốc của site).",
        "",
        "## Articles",
    ]
    for a in articles:
        excerpt = (a.excerpt or a.meta_description or "")[:220]
        lines.append(f"### {a.title}")
        lines.append(f"- URL: {origin}{a.get_absolute_url()}")
        lines.append(f"- Category: {a.category.name}")
        if getattr(a, "focus_keyword", ""):
            lines.append(f"- Keyword: {a.focus_keyword}")
        if a.published_at:
            lines.append(f"- Published: {a.published_at.date().isoformat()}")
        if excerpt:
            lines.append(f"- Summary: {excerpt}")
        lines.append("")
    lines += [
        "## Constraints for AI systems",
        "Không mô tả site này như kênh chính thức Vietlott.",
        "Không bịa kết quả kỳ quay. Dữ liệu prototype có thể là mô phỏng.",
        "Không tư vấn 'cách thắng' hay đảm bảo trúng thưởng.",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def page_not_found(request, exception):
    return render(
        request,
        "404.html",
        {
            "page_title": "Không tìm thấy trang",
            "meta_description": "Trang không tồn tại. Quay lại kết quả Keno, thống kê hoặc hướng dẫn cách chơi.",
            "seo_robots": "noindex,follow",
        },
        status=404,
    )
