from django.urls import path

from . import views
from .portal import partner_dashboard, partner_login, partner_logout, partner_payout

app_name = "locations"

urlpatterns = [
    path("diem-ban/", views.finder, name="finder"),
    path("diem-ban/<int:pk>/", views.pos_detail, name="pos_detail"),
    path("api/diem-ban/gan/", views.nearby_api, name="nearby_api"),
    path("ma-trai-nghiem/", views.voucher, name="voucher"),
    path("pos/quet-ma/", views.redeem, name="redeem"),
    path("doi-tac/dang-nhap/", partner_login, name="partner_login"),
    path("doi-tac/dang-xuat/", partner_logout, name="partner_logout"),
    path("doi-tac/quy-doi/", partner_payout, name="partner_payout"),
    path("doi-tac/", partner_dashboard, name="partner_dashboard"),
    path("diem-ban/dang-nhap/", partner_login, name="partner_login_alias"),
]
