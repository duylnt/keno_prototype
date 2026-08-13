from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("pos-display/", views.pos_display, name="pos_display"),
    path("man-hinh-quay/", views.pos_display, name="pos_tv"),
    path("ket-qua-truc-tiep/", views.pos_display, name="live_results"),
    path("truc-tiep/", views.pos_display, name="live_results_short"),
    path("api/pos-tv/", views.pos_tv_api, name="pos_tv_api"),
]
