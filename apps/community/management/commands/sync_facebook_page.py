from django.core.management.base import BaseCommand

from apps.community.facebook import sync_facebook_page


class Command(BaseCommand):
    help = "Đồng bộ bài viết Fanpage qua Graph API (không scrape HTML)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=25)

    def handle(self, *args, **options):
        result = sync_facebook_page(limit=options["limit"])
        if result["ok"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Đồng bộ Fanpage: +{result['created']} mới, {result['updated']} cập nhật."
                )
            )
            return
        self.stdout.write(self.style.WARNING(result["error"]))
        if result.get("permission"):
            self.stdout.write(f"Quyền cần cấp: {result['permission']}")
