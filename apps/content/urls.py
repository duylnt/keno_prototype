from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("thong-tin/", views.info_hub, name="info_hub"),
    path("bai-viet/", views.article_list, name="article_list"),
    path("bai-viet/<slug:slug>/", views.article_detail, name="article_detail"),
    path("trang/<slug:slug>/", views.static_page, name="static_page"),
    path("huong-dan/", views.how_to_play, name="how_to_play"),
]
