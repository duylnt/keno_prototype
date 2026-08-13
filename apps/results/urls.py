from django.urls import path

from . import views

app_name = "results"

urlpatterns = [
    path("ket-qua/", views.live, name="live"),
    path("ket-qua/hom-nay/", views.today, name="today"),
    path("ket-qua/lich-su/", views.history, name="history"),
    path("thong-ke/", views.stats, name="stats"),
    path("thong-ke/lon-nho/", views.stats_size, name="stats_size"),
    path("thong-ke/chan-le/", views.stats_parity, name="stats_parity"),
    path("do-ve/", views.check_ticket_view, name="check_ticket"),
    path("choi-thu/", views.simulator, name="simulator"),
    path("api/live/", views.live_api, name="live_api"),
    path("api/live/stream/", views.live_sse, name="live_sse"),
    path("api/simulator/", views.simulator_play, name="simulator_play"),
]
