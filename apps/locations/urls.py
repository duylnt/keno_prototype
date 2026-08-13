from django.urls import path

from . import views

app_name = "locations"

urlpatterns = [
    path("diem-ban/", views.finder, name="finder"),
    path("diem-ban/<int:pk>/", views.pos_detail, name="pos_detail"),
    path("api/diem-ban/gan/", views.nearby_api, name="nearby_api"),
    path("ma-trai-nghiem/", views.voucher, name="voucher"),
    path("pos/quet-ma/", views.redeem, name="redeem"),
]
