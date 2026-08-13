from django.apps import AppConfig
from django.contrib import admin


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Cài đặt & giao diện"

    def ready(self):
        admin.site.site_header = "Keno CMS"
        admin.site.site_title = "Keno CMS"
        admin.site.index_title = "Tổng quan"
