from django.core.management.base import BaseCommand

from apps.analytics.google import sync_gsc


class Command(BaseCommand):
    help = "Đồng bộ Google Search Console (clicks, impressions, từ khóa)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14)

    def handle(self, *args, **options):
        d, q = sync_gsc(days=options["days"])
        self.stdout.write(self.style.SUCCESS(f"Đã lưu {d} ngày và {q} từ khóa GSC."))
