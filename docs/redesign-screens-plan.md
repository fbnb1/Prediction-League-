# Kế hoạch: Xây lại 6 màn hình World Cup Betting

## Context

Dự án hiện có frontend vanilla JS (3 file: `web/index.html`, `web/app.js`, `web/styles.css`) với 5 view rời rạc (Matches, My Groups, My Picks, Ledger, Admin). Người dùng muốn thiết kế lại trải nghiệm thành 6 màn hình hướng người dùng cuối: Trang chính (bảng xếp hạng group), Chi tiết người chơi, Danh sách trận, Chi tiết trận, Admin, Cài đặt group.

Backend là microservices: **Prediction** (Python/FastAPI — users, groups, picks), **Fixture** (Python/FastAPI — matches, odds, kết quả, read-model `match_picks`), **Ledger** (Java/Spring — sổ kế toán kép). Một số dữ liệu yêu cầu chưa có API (leaderboard tính sẵn, list toàn bộ user, đổi mật khẩu, đổi loại kèo). Vì vậy cần bổ sung backend.

**Quyết định đã chốt với người dùng:**
- Chuyển frontend sang **React + Vite** (có build tool).
- **Thêm API backend** cần thiết.
- **Thay thế hoàn toàn** cấu trúc cũ bằng 6 màn hình mới.
- Thêm cột `is_admin` vào bảng `users`; màn hình Admin chỉ hiện khi `is_admin=true`.
- Chi tiết trận tính **theo group đang chọn**.

---

## Phần A — Thay đổi Backend

### A1. Prediction service — quyền admin
- Migration Alembic mới: thêm cột `is_admin BOOLEAN NOT NULL DEFAULT false` vào `users` (`services/prediction-service/app/models.py`, thư mục migrations).
- Seed: đặt 1 tài khoản admin (`is_admin=true`) lúc khởi tạo.
- JWT payload thêm `is_admin`; `TokenOut` (schemas.py) thêm `is_admin`.
- `admin_auth.py`: guard admin chấp nhận **JWT có `is_admin=true`** HOẶC header `X-Admin-API-Key` (giữ tương thích).

### A2. Prediction service — endpoint admin mới (`app/api/admin.py`)
- `GET /admin/users` → list tất cả user `(id, username, display_name, is_admin)`.
- `PUT /admin/users/{user_id}/password` → đặt lại mật khẩu (body `{new_password}`), dùng `security.hash_password`.
- `POST /admin/groups` → tạo group `(name, bet_type)` — tái dùng `operations` tạo group.
- `PUT /admin/groups/{group_id}/bet-type` → đổi `bet_type` của group (`EUROPEAN`/`ASIAN`).
- `GET /admin/groups` → list toàn bộ group (đã có `GET /groups`, dùng lại được).

### A3. Fixture service — pick-results theo group (`app/api/fixtures.py`)
- Endpoint mới `GET /pick-results?group_id={id}`: trả về mọi `match_picks` của group, join với `matches` và `odds`, kèm:
  `match_id, user_id, predicted_outcome, auto_loss, stake_minor, bet_type, home_team, away_team, kickoff_at, status, outcome, home_score, away_score, result` (`WON`/`LOST`/`PENDING`).
- `result` tính bằng các hàm thuần có sẵn `settle_pick()` / `settle_pick_asian()` trong `app/domain/evaluation.py`.
- Thêm `lock_at` vào `MatchOut` (schemas.py) = `kickoff_at - LOCK_OFFSET_MINUTES` để frontend đếm ngược chính xác.

### A4. Ledger service — nạp tiền gắn với người chơi theo group
- **Đổi bút toán nạp tiền** trong `LedgerService` / `AdminController` `POST /admin/deposits`:
  hiện tại `DEBIT CASH_RECEIVED / CREDIT POOL(groupId)` → đổi thành `DEBIT CASH_RECEIVED / CREDIT PLAYER("{userId}:{groupId}")`.
  Lý do: cần số đã nạp theo từng người chơi trong từng group.
- Settlement (`MatchSettledConsumer`): bút toán thua đổi `DEBIT PLAYER(userId)` → `DEBIT PLAYER("{userId}:{groupId}")` để số dư PLAYER tách theo group.
- Hệ quả: số dư account `PLAYER("{userId}:{groupId}")` = tiền còn nợ (debit losses − credit deposits). Reason của journal entry nạp tiền giữ tiền tố `DEPOSIT` để lọc lịch sử.

### A5. Prediction service — endpoint tổng hợp cho màn hình (`app/api/` + `ledger_client.py` mới)
Prediction đã có `fixture_client.py`; thêm `ledger_client.py`. Các endpoint tổng hợp (gọi nội bộ Fixture + Ledger), trả 1 lần cho frontend:
- `GET /groups/{group_id}/leaderboard` → mỗi thành viên: `money_lost` (Σ stake LOST từ pick-results), `total_picks`, `wins`, `losses`, `win_rate`, `form` (mảng 5 W/L gần nhất theo kickoff), `money_deposited`, `money_owed = money_lost − money_deposited`.
- `GET /groups/{group_id}/members/{user_id}/summary` → lịch sử pick (mọi trận, mới→cũ) kèm result + tiền mất; tổng `money_lost/deposited/owed`; lịch sử nạp tiền của người đó.
- `GET /matches/{match_id}/detail?group_id={id}` → kết quả trận; phân bố pick (số người chọn HOME/AWAY/DRAW) trong group; danh sách người thua + tổng tiền thu về.
- `GET /groups/{group_id}/deposits` → lịch sử nạp tiền toàn bộ thành viên group `(user, display_name, amount, posted_at)`.
- `POST /admin/groups/{group_id}/deposits` (hoặc gọi thẳng Ledger từ frontend) — chốt: Prediction proxy sang Ledger để có sẵn ngữ cảnh thành viên.

### A6. Gateway
- `gateway/nginx.conf`: giữ proxy `/api/*`; phần phục vụ web tĩnh trỏ tới thư mục build React (`dist`).

---

## Phần B — Frontend React

### B1. Khởi tạo & toolchain
- Tạo project Vite + React tại `web/` (giữ thư mục), `package.json`, `vite.config.js` (proxy `/api` → gateway khi dev).
- Thêm `react-router-dom`. Pie chart **vẽ bằng SVG thủ công** (component `PieChart`), không thêm thư viện chart.
- `web/Dockerfile`: multi-stage — `node` build → copy `dist` vào `nginx`. Cập nhật `docker-compose.yml` service web.

### B2. Hạ tầng dùng chung (`web/src/`)
- `api/client.js`: wrapper `fetch`, base `/api/{prediction|fixture|ledger}`, gắn `Authorization: Bearer`, `X-Admin-API-Key` khi cần; class lỗi `ApiError`.
- `context/AuthContext.jsx`: token + user (`is_admin`) trong `localStorage`.
- `context/GroupContext.jsx`: group đang chọn (mặc định group đầu tiên của user), lưu lại lựa chọn.
- Components dùng lại: `GroupSelector`, `PieChart`, `Countdown` (đếm ngược tới `lock_at`), `MatchCard`, `WinLossBadge`, `FormStrip` (5 ô W/L), `DataTable`, `Toast`.
- `styles/`: port lại design token từ `web/styles.css` cũ (biến CSS, font Inter/Sora).

### B3. Routing & màn hình
- `/login` — đăng nhập/đăng ký (giữ logic username/password hiện có).
- `/` **Trang chính**:
  - `GroupSelector` (auto chọn group đầu tiên).
  - Bảng xếp hạng: cột tên, tiền thua, tỷ lệ dự đoán, form 5 trận; filter/sort theo từng cột. Click tên → `/players/:userId?group=`.
  - Section trận: 3 trận vừa kết thúc + 3 trận tới (kèm `Countdown`). Click trận → `/matches/:matchId?group=`.
  - Section lịch sử nạp tiền toàn group (`GET /groups/{id}/deposits`).
- `/players/:userId` **Chi tiết người chơi** (`?group=`):
  - Lịch sử pick cuộn dọc (mới→cũ) kèm W/L + tiền mất.
  - `PieChart` tỷ lệ thắng/thua.
  - Section tiền: đã mất / đã nộp / còn phải đóng.
  - Section lịch sử nạp tiền của người đó.
  - Nguồn: `GET /groups/{id}/members/{userId}/summary`.
- `/matches` **Danh sách trận**: list toàn bộ trận; trận xong hiện kết quả, trận chưa đá hiện `Countdown` tới giờ khóa. Click → chi tiết.
- `/matches/:matchId` **Chi tiết trận** (`?group=`): kết quả; `PieChart` % chọn đội A/B; danh sách người thua + tổng tiền thu về. Nguồn: `GET /matches/{id}/detail?group_id=`.
- `/admin` **Admin** (chỉ khi `is_admin`, route guard):
  - List toàn bộ user + nút đổi mật khẩu (`PUT /admin/users/{id}/password`).
  - List group; click → `/admin/groups/:groupId`.
  - Nút "Thêm group" (`POST /admin/groups`).
- `/admin/groups/:groupId` **Cài đặt group**:
  - Chọn kèo Á/Âu → `PUT /admin/groups/{id}/bet-type`.
  - Section thành viên + thêm thành viên: ô chọn có **autocomplete** (gõ ký tự lọc theo prefix, hoặc xổ toàn bộ list để chọn) — nguồn `GET /admin/users`; thêm qua `POST /admin/groups/{id}/members`.
  - Section lịch sử nạp tiền group + form nạp tiền: ô chọn thành viên autocomplete **chỉ lọc trong group**; nhập số tiền + OK → gọi nạp tiền; sau khi xong refresh lịch sử ở cả trang group và sẽ phản ánh ở trang chi tiết người chơi.

---

## File chính sẽ tạo/sửa

**Backend:**
- `services/prediction-service/app/models.py`, `schemas.py`, `security.py`, `admin_auth.py`, `operations.py`
- `services/prediction-service/app/api/admin.py`, `groups.py` + file mới cho endpoint tổng hợp
- `services/prediction-service/app/ledger_client.py` (mới), `fixture_client.py`
- `services/prediction-service/app/migrations/versions/` (migration `is_admin`)
- `services/fixture-service/app/api/fixtures.py`, `schemas.py`, `operations.py`
- `services/ledger-service/.../service/LedgerService.java`, `service/SettlementService.java`, `messaging/MatchSettledConsumer.java`, `service/AccountRef.java`
- `gateway/nginx.conf`, `docker-compose.yml`

**Frontend (mới, thay toàn bộ `web/`):**
- `web/package.json`, `vite.config.js`, `Dockerfile`, `index.html`
- `web/src/main.jsx`, `App.jsx`, `api/client.js`, `context/*`, `components/*`, `pages/*`, `styles/*`

---

## Verification (kiểm thử end-to-end)

1. `docker compose up --build` — toàn bộ service + web build chạy.
2. Chạy migration; xác nhận có tài khoản admin (`is_admin=true`).
3. Đăng nhập admin → màn hình Admin hiện; đăng nhập user thường → không hiện.
4. Admin: tạo group mới, đổi kèo Á/Âu, thêm thành viên (test autocomplete), đổi mật khẩu 1 user → đăng nhập lại bằng mật khẩu mới OK.
5. Admin nạp tiền cho 1 thành viên → kiểm tra lịch sử nạp hiện ở Cài đặt group, Trang chính, và Chi tiết người chơi; "còn phải đóng" giảm đúng.
6. Tạo vài pick, force-lock, nhập kết quả trận → leaderboard cập nhật tiền thua/win-rate/form; Chi tiết trận hiện pie chart % chọn đội + danh sách người thua + tổng tiền.
7. Trang chính: đổi group trong `GroupSelector` → bảng xếp hạng đổi theo; filter/sort các cột hoạt động; đếm ngược trận sắp tới chạy đúng tới giờ khóa.
8. Chi tiết người chơi: pie thắng/thua, lịch sử pick cuộn dọc, 3 con số tiền khớp với leaderboard.
9. Chạy lại test backend hiện có (pytest cho prediction/fixture, `mvn test` cho ledger) để bắt regression sau khi đổi bút toán Ledger.
