from django.core.management.base import BaseCommand

from apps.seo.links import check_internal_links


class Command(BaseCommand):
    help = "Kiểm tra link hỏng trên trang của chính site này (không quét site ngoài)."

    def handle(self, *args, **options):
        result = check_internal_links()
        self.stdout.write(
            self.style.SUCCESS(
                f"OK {result['ok']} · hỏng {result['broken']} · {result['checked_at']}"
            )
        )
