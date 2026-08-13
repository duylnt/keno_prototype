# Keno — Mobile web & Community (Django prototype)

Website tra cứu Keno + cộng đồng + tìm điểm bán + CMS + báo cáo KPI (GA4 / Search Console).

Prototype mô phỏng kết quả theo nhịp 8 phút. **Không bán vé**, không phải kết quả chính thức Vietlott cho đến khi nối API thật.

---

## English — run locally

```bash
cd keno_prototype
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

- Public site: http://127.0.0.1:8000/
- CMS: http://127.0.0.1:8000/cms/
- Superuser: `admin` / `keno-admin-2026`
- POS owner portal: http://127.0.0.1:8000/doi-tac/ — `chudiem` / `keno-pos-2026`

Optional: `python manage.py test`

---

## Tiếng Việt — chạy local

1. Cài Python 3.11+ và tạo virtualenv.
2. `pip install -r requirements.txt`
3. Copy `.env.example` → `.env`
4. `python manage.py migrate`
5. `python manage.py seed_demo` (tạo admin, bài SEO, kỳ quay mô phỏng, điểm bán, KPI mẫu)
6. `python manage.py runserver`

Đăng nhập CMS tại `/cms/` bằng `admin` / `keno-admin-2026`.

Cổng chủ điểm bán: `/doi-tac/` — `chudiem` / `keno-pos-2026` (sau `seed_demo`).

---

## Fanpage Facebook (cộng đồng)

Cộng đồng trên site **nhúng Fanpage**, không thay Facebook làm diễn đàn chính.

1. CMS → **Cài đặt website** → card **Fanpage Facebook**: URL, Page ID, App ID, Page Access Token (ẩn), ghi chú vai trò.
2. Hoặc `.env`: `FACEBOOK_PAGE_URL`, `FACEBOOK_PAGE_ID`, `FACEBOOK_APP_ID`, `FACEBOOK_PAGE_ACCESS_TOKEN`.
3. `/cong-dong/` hiện Page Plugin khi có **URL + App ID**.
4. Đồng bộ bài viết (Graph API, không scrape HTML):

```bash
python manage.py sync_facebook_page
```

Token Page cần `pages_read_engagement` (đọc bài) và `pages_manage_posts` (ẩn/gỡ đăng). CMS **Kiểm duyệt Fanpage** (`/cms/cong-dong/fanpage/`) mở sẵn Facebook Moderation / Inbox; nếu Graph từ chối quyền thì báo lỗi, không giả lập thành công. Token không bao giờ in ra HTML.

---

## Cổng chủ điểm bán

- URL: `/doi-tac/` (đăng nhập `/doi-tac/dang-nhap/` hoặc `/diem-ban/dang-nhap/`)
- Demo: `chudiem` / `keno-pos-2026` (Hoàn Kiếm). Tài khoản thứ hai: `chudiem2` cùng mật khẩu (Quận 1).
- Xem hoa hồng khi mã O2O được quét tại **điểm của mình**, ví điểm thưởng, gửi yêu cầu quy đổi (CMS duyệt — mô phỏng, không chuyển khoản).
- Nhân viên dùng `/cms/`. Gán `owner` trên Điểm bán Keno; nhóm `pos_owner`.

---

## Kết nối Google Analytics 4 + Search Console

1. Tạo Google Cloud project, bật **Google Analytics Data API** và **Google Search Console API**.
2. Tạo **service account**, tải JSON key (không commit file này).
3. GA4: Admin → Property access → thêm email service account với quyền Viewer.
4. Search Console: Settings → Users → thêm cùng email với quyền Full user (hoặc Restricted).
5. Điền `.env`:

```
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
GSC_CREDENTIALS_PATH=/absolute/path/to/service-account.json
GA4_PROPERTY_ID=123456789
GSC_SITE_URL=https://your-keno-domain/
GA4_MEASUREMENT_ID=G-XXXXXXXX
GTM_CONTAINER_ID=GTM-XXXXXXX
```

6. Đồng bộ:

```bash
python manage.py sync_ga4 --days 28
python manage.py sync_gsc --days 28
```

Hoặc nút **Đồng bộ GA4 / Search Console** trên các trang Báo cáo trong CMS.

Nếu chưa có credentials, `seed_demo` đã tạo snapshot mẫu để xem báo cáo.

### CMS — Báo cáo (`/cms/`)

Đăng nhập `admin` / `keno-admin-2026`. Giao diện sáng (light). Nếu vẫn thấy theme cũ, hard refresh (Cmd+Shift+R / Ctrl+Shift+R).

| Trang | URL |
|---|---|
| Tổng quan | `/cms/` |
| Phễu tăng trưởng | `/cms/bao-cao/pheu/` |
| KPI Website | `/cms/bao-cao/website/` |
| Search Console | `/cms/bao-cao/seo/` |
| KPI Cộng đồng | `/cms/bao-cao/cong-dong/` |
| Ý định O2O | `/cms/bao-cao/o2o/` |

URL cũ `/cms/bao-cao-kpi/` vẫn mở phễu tăng trưởng.

Front-end cũng gửi sự kiện nội bộ (xem kết quả, dò vé, tìm điểm bán, chỉ đường…) tới `/api/analytics/collect/` để đo phễu ngay trên prototype.

---

## Cấu trúc chính

| App | Vai trò |
|---|---|
| `apps.core` | Cài đặt site, banner, dashboard CMS, POS Display |
| `apps.results` | Kỳ quay, live, lịch sử, thống kê, dò vé, chơi thử |
| `apps.content` | CMS bài SEO + trang tĩnh |
| `apps.community` | Nội quy, lọc thành viên, duyệt bài, minigame |
| `apps.locations` | Điểm bán, GPS, chỉ đường, mã O2O |
| `apps.analytics` | KPI, GA4, GSC, sự kiện nội bộ |

Admin theme: **django-unfold** tại `/cms/`.
