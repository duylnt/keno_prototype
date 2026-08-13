from django.urls import path

from . import views

app_name = "community"

urlpatterns = [
    path("cong-dong/", views.hub, name="hub"),
    path("cong-dong/gui-bai/", views.submit_post, name="submit_post"),
    path("cong-dong/noi-quy/", views.guidelines, name="guidelines"),
    path("cong-dong/tham-gia/", views.join_intent, name="join"),
]
