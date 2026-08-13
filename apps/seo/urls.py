from django.urls import path

from . import views

app_name = "seo"

urlpatterns = [
    path("robots.txt", views.robots_txt, name="robots"),
    path("llms.txt", views.llms_txt, name="llms"),
    path("llms-full.txt", views.llms_full_txt, name="llms_full"),
    path(".well-known/llms.txt", views.llms_txt, name="llms_wellknown"),
]
