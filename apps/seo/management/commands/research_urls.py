from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.seo.crawler import analyze_urls, persist_result
from apps.seo.models import SeoStatus
from apps.seo.sample_market import SAMPLE_MARKET


class Command(BaseCommand):
    help = "Phân tích URL công khai (metadata + excerpt). Tôn trọng robots.txt, rate-limit."

    def add_arguments(self, parser):
        parser.add_argument("urls", nargs="*", help="Danh sách URL")
        parser.add_argument("--file", dest="file", help="File text, mỗi dòng một URL")
        parser.add_argument("--samples", action="store_true", help="Nạp URL mẫu minh họa (không crawl)")
        parser.add_argument("--product", default="", help="Gán sản phẩm: keno, power655, mega645, max3d, lotto535")

    def handle(self, *args, **options):
        if options["samples"]:
            n = 0
            for row in SAMPLE_MARKET:
                from apps.seo.models import ResearchUrl

                if ResearchUrl.objects.filter(url=row["url"]).exists():
                    continue
                persist_result({**row, "robots_allowed": True, "fetched_at": timezone.now()}, row["product_hint"])
                n += 1
            self.stdout.write(self.style.SUCCESS(f"Đã nạp {n} mẫu minh họa."))
            return
        urls = list(options["urls"] or [])
        if options["file"]:
            with open(options["file"], encoding="utf-8") as fh:
                urls.extend(ln.strip() for ln in fh if ln.strip() and not ln.startswith("#"))
        if not urls:
            self.stderr.write("Cần URL, --file hoặc --samples.")
            return
        results = analyze_urls(urls)
        for data in results:
            obj = persist_result(data, options["product"])
            self.stdout.write(f"{obj.status:8} {obj.http_status or '-':>3}  {obj.url}  {obj.title[:60]}")
        s = SeoStatus.load()
        s.research_at = timezone.now()
        s.save(update_fields=["research_at"])
        self.stdout.write(self.style.SUCCESS(f"Xong {len(results)} URL. Chỉ lưu metadata + excerpt."))
