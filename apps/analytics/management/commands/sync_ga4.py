from django.core.management.base import BaseCommand

from apps.analytics.google import sync_ga4


class Command(BaseCommand):
    help = "Đồng bộ chỉ số từ Google Analytics 4 Data API."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14)

    def handle(self, *args, **options):
        n = sync_ga4(days=options["days"])
        self.stdout.write(self.style.SUCCESS(f"Đã lưu {n} ngày GA4."))
