from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="facebook_app_id",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Cần cho Facebook Comments / JS SDK.",
                max_length=64,
                verbose_name="Facebook App ID",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="facebook_comments_url",
            field=models.URLField(
                blank=True,
                default="",
                help_text="Canonical URL cho plugin bình luận — thường là trang Trực tiếp kết quả.",
                verbose_name="URL bình luận Facebook",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="facebook_page_url",
            field=models.URLField(
                blank=True,
                default="",
                help_text="Trang Facebook để nhúng Page Plugin trên cộng đồng / trực tiếp.",
                verbose_name="Link Facebook Page",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="zalo_group_url",
            field=models.URLField(
                blank=True,
                default="",
                help_text="Group Zalo để mua vé / hỏi điểm bán. Website không bán vé.",
                verbose_name="Link nhóm Zalo",
            ),
        ),
    ]
