# Kế hoạch: Redesign 6 màn hình World Cup Betting (React + BFF)

## Context

`docs/redesign-screens-plan.md` mô tả việc thay frontend vanilla (3 file) bằng React + Vite gồm 6 màn hình hướng người dùng cuối: Trang chính (leaderboard group), Chi tiết người chơi, Danh sách trận, Chi tiết trận, Admin, Cài đặt group. Đồng thời bổ sung quyền admin (cột `is_admin`), endpoint admin còn thiếu (đổi password, tạo group, đổi bet-type), endpoint tổng hợp đọc dữ liệu từ cả 3 service, và đổi mô hình account Ledger từ POOL(groupId) sang PLAYER("{userId}:{groupId}") để có "tiền đã nạp" tách theo từng người chơi trong từng group.

Khảo sát code xác nhận: `is_admin` chưa có; JWT payload chưa chứa `is_admin`; `admin_auth.py` chỉ dùng `X-Admin-API-Key`; bút toán deposit (`LedgerService.java:40-55`) đang DEBIT CASH_RECEIVED / CREDIT POOL(groupId); settlement (`SettlementService.java:32-56`) DEBIT PLAYER(userId); fixture-service chưa có endpoint `pick-results` tổng hợp; chưa có endpoint leaderboard nào. Web hiện là 3 file tĩnh mount thẳng vào nginx (không có build tool).

**Quyết định đã chốt với người dùng (qua AskUserQuestion):**
- Reset DB khi deploy (không cần migration backfill cho Ledger).
- Thêm **service BFF mới** (`services/bff-service/`, Python + FastAPI) chuyên trách aggregation reads.
- BFF tự verify JWT (giữ `jwt_secret` chung với prediction qua env var), không round-trip về prediction.
- Admin write-endpoints vẫn nằm ở prediction-service.
- Frontend hiển thị tiền: `amount_minor / 100` với separator hàng nghìn, hậu tố `₫`.

---

## Phần A — Backend

### A1. Prediction service — quyền admin (`services/prediction-service/`)

- Migration Alembic `0004_user_is_admin.py`: `ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT false`. Thêm cột vào `app/models.py:User` (sau `password_hash`).
- Seed admin: trong `app/main.py` (hoặc init script tương đương) đặt `users.is_admin=true` cho username `admin` khi khởi tạo (giữ idempotent).
- `app/security.py:create_token`: payload thêm `is_admin: bool`; `decode_token` trả về dict đầy đủ. `get_current_user` phải load user từ DB hoặc tin claim — chọn **tin claim** để giữ stateless (`is_admin` đổi rất ít, chấp nhận TTL).
- `app/schemas.py:TokenOut`: thêm `is_admin: bool`. `app/api/auth.py:login` truyền cờ vào `create_token` và `TokenOut`.
- `app/admin_auth.py`: đổi `require_admin_key` → `require_admin` chấp nhận **JWT có `is_admin=true`** HOẶC header `X-Admin-API-Key` (giữ tương thích để job/cli vẫn chạy được). Inject qua `Depends(...)`.

### A2. Prediction service — endpoint admin mới (`app/api/admin.py`)

Thêm vào router hiện có (`prefix="/admin"`, dùng `Depends(require_admin)`):

- `GET /admin/users` → list `{id, username, display_name, is_admin}`.
- `PUT /admin/users/{user_id}/password` body `{new_password}` → gọi `security.hash_password` rồi update. Trả `204`.
- `POST /admin/groups` body `{name, bet_type, owner_user_id?}` → tái dùng `operations.create_group`.
- `PUT /admin/groups/{group_id}/bet-type` body `{bet_type}` → validate `EUROPEAN|ASIAN`, update column `groups.bet_type`.
- `GET /admin/groups` reuse `api/groups.py:list_groups` (đã có) — không cần thêm.
- `POST /admin/groups/{group_id}/members` đã có, giữ nguyên.

### A3. Fixture service — pick-results theo group + lock_at

- `app/api/fixtures.py`: thêm `GET /pick-results?group_id={id}` trả về list:
  `{match_id, user_id, predicted_outcome, auto_loss, stake_minor, bet_type, home_team, away_team, kickoff_at, status, outcome, home_score, away_score, result}` (`result ∈ {WON, LOST, PENDING}`).
  - JOIN `MatchPick` × `Match` × `Odds` (cần `handicap` cho ASIAN), filter `group_id`.
  - Tính `result`: nếu `status != FINAL` → `PENDING`; nếu `bet_type == EUROPEAN` → `settle_pick(predicted_outcome, outcome_from_scores(...))`; nếu `ASIAN` → `settle_pick_asian(...)`. Tái dùng `app/domain/evaluation.py:settle_pick, settle_pick_asian, outcome_from_scores`.
- `app/schemas.py:MatchOut`: thêm `lock_at: datetime` = `kickoff_at - LOCK_OFFSET_MINUTES`. Thêm `lock_offset_minutes: int = 15` vào `app/config.py` (đồng bộ default với prediction). Tính `lock_at` ở response mapping (computed field hoặc trong endpoint).

### A4. Ledger service — bút toán theo `userId:groupId`

- `service/AccountRef.java`: thêm overload `player(String userId, String groupId)` trả về ownerId `userId + ":" + groupId`. Loại bỏ cách dùng `player(userId)` ở settlement + deposit; giữ method cũ để test legacy không vỡ, nhưng codepath production không gọi.
- `service/LedgerService.java:40-55 deposit()`: đổi posting `CREDIT POOL(groupId)` → `CREDIT player(depositor, groupId)`. Reason giữ tiền tố `"DEPOSIT"`.
- `service/SettlementService.java:32-56 settleLosingPick()`: đổi `DEBIT player(userId)` → `DEBIT player(userId, groupId)` (đã có sẵn `groupId` ở signature). Idempotency key giữ nguyên.
- `api/AccountController` (hoặc tương đương): thêm endpoint `GET /accounts/player?userId=&groupId=` trả về `{ownerId, debitMinor, creditMinor, balanceMinor}` để BFF tính tiền đã nạp / đã thua.
- Endpoint mới `GET /journal-entries?reason_prefix=DEPOSIT&owner_id=...` để filter lịch sử nạp theo người/group. Hoặc gọn hơn: `GET /deposits?groupId=&userId=` — trả `(entryId, amountMinor, postedAt, depositor, groupId)`.
- Cập nhật `LedgerIT.java`, `PostingServiceTest.java`: assertions ownerId của PLAYER account đổi sang dạng `"userId:groupId"`.

### A5. BFF service mới — `services/bff-service/` (Python + FastAPI)

Tạo từ template prediction-service (FastAPI + httpx + pydantic). Không có DB riêng.

- Files: `app/main.py`, `app/config.py` (env: `JWT_SECRET`, `PREDICTION_URL`, `FIXTURE_URL`, `LEDGER_URL`), `app/auth.py` (verify JWT, expose `get_current_user`, `require_admin`), `app/clients/{prediction.py, fixture.py, ledger.py}` (httpx wrappers), `app/api/{leaderboard.py, players.py, matches.py, deposits.py}`, `app/schemas.py`, `Dockerfile`, `requirements.txt`, `tests/` (pytest + httpx mocks).
- Endpoint:
  - `GET /groups/{group_id}/leaderboard` → cho mỗi member của group: `display_name`, `money_lost_minor` (Σ stake `LOST` từ `/pick-results?group_id=`), `total_picks`, `wins`, `losses`, `win_rate`, `form` (5 W/L gần nhất theo `kickoff_at` desc), `money_deposited_minor` (từ ledger PLAYER credit), `money_owed_minor = lost − deposited`.
  - `GET /groups/{group_id}/members/{user_id}/summary` → lịch sử pick (mới→cũ) + `result` + `stake_minor`; tổng `lost/deposited/owed`; lịch sử nạp tiền của user trong group.
  - `GET /matches/{match_id}/detail?group_id=` → match info + score; phân bố pick `{HOME, AWAY, DRAW}` trong group; danh sách người LOST + `total_collected_minor` (Σ stake của những người thua).
  - `GET /groups/{group_id}/deposits` → toàn bộ deposit của group `(user_id, display_name, amount_minor, posted_at)`.
  - `POST /admin/groups/{group_id}/deposits` (require_admin) → proxy thẳng tới `POST /admin/deposits` của Ledger (body `{depositor, amount_minor}`); chèn `group_id` từ path. Sau khi 201, không cần invalidate cache (BFF stateless).
- Frontend gọi BFF qua gateway prefix `/api/bff/`.

### A6. Gateway & docker-compose

- `gateway/nginx.conf`: thêm `location /api/bff/` proxy → `bff-service:8000`. Đổi `location /` từ `root /usr/share/nginx/html` (đang phục vụ web tĩnh trực tiếp) sang phục vụ thư mục `dist/` build từ React.
- `docker-compose.yml`:
  - Service `web`: đổi từ mount `./web` vào `nginx:1.27-alpine` → build từ `web/Dockerfile` multi-stage (node build → nginx serve `dist`).
  - Service mới `bff-service`: build từ `services/bff-service/Dockerfile`, env `JWT_SECRET`, `PREDICTION_URL=http://prediction-service:8000`, etc., depends_on prediction/fixture/ledger.

---

## Phần B — Frontend (`web/` — thay toàn bộ)

### B1. Toolchain

- `package.json`: `react`, `react-dom`, `react-router-dom`, `vite`, `@vitejs/plugin-react`. Không thêm chart lib (vẽ SVG `PieChart` thủ công).
- `vite.config.js`: dev proxy `/api/* → http://localhost:8080` (gateway).
- `Dockerfile` multi-stage (node:20-alpine build → nginx:1.27-alpine serve `dist`).
- `index.html` (entry Vite), `src/main.jsx`, `src/App.jsx`.

### B2. Hạ tầng dùng chung (`web/src/`)

- `api/client.js`: wrapper `fetch`, base prefix theo service (`/api/prediction`, `/api/fixture`, `/api/ledger`, `/api/bff`), gắn `Authorization: Bearer <token>`; class `ApiError(status, body)`.
- `context/AuthContext.jsx`: lưu `token`, `user {id, display_name, is_admin}` trong `localStorage`. Hàm `login/logout`.
- `context/GroupContext.jsx`: lưu `selectedGroupId` (persist `localStorage`), default = group đầu tiên trả về từ `/groups`.
- Components dùng lại: `GroupSelector`, `PieChart` (SVG), `Countdown` (đếm ngược tới `lock_at`), `MatchCard`, `WinLossBadge`, `FormStrip` (5 ô W/L), `DataTable` (sortable cols), `Toast`, `Money` (format `amount_minor/100` với `Intl.NumberFormat('vi-VN')` + `₫`).
- `styles/tokens.css`: port các biến CSS từ `web/styles.css` cũ (`--brand #00a862`, `--font Inter`, `--display Sora`, `--radius 14px`, v.v.). Import font Inter/Sora.

### B3. Routing & màn hình

- `/login` — username + password. Lưu token, chuyển `/`.
- `/` **Trang chính**:
  - `GroupSelector` (auto chọn group đầu).
  - Bảng leaderboard: cột `display_name`, `money_lost`, `win_rate`, `form` (5 ô W/L); sort/filter từng cột (client-side trên `DataTable`). Click tên → `/players/:userId?group=`.
  - Section "Trận": 3 trận FINAL gần nhất + 3 trận tới (`Countdown` đến `lock_at`). Click → `/matches/:matchId?group=`.
  - Section "Lịch sử nạp tiền group" (`GET /api/bff/groups/{id}/deposits`).
- `/players/:userId?group=` **Chi tiết người chơi**:
  - Lịch sử pick cuộn dọc, mới→cũ, kèm `result` + `Money(stake)`.
  - `PieChart` W/L.
  - 3 thẻ tiền: đã mất / đã nộp / còn phải đóng.
  - Lịch sử nạp tiền của user trong group này.
  - Nguồn: `GET /api/bff/groups/{id}/members/{userId}/summary`.
- `/matches` **Danh sách trận**: toàn bộ trận từ `GET /api/fixture/fixtures`; trận FINAL hiện kết quả, trận chưa đá hiện `Countdown`. Click → chi tiết.
- `/matches/:matchId?group=` **Chi tiết trận**: score; `PieChart` phân bố pick HOME/AWAY/DRAW trong group; danh sách người LOST + `total_collected`. Nguồn: `GET /api/bff/matches/{id}/detail?group_id=`.
- `/admin` **Admin** (route guard `user.is_admin`):
  - List user + nút "Đổi mật khẩu" (modal `PUT /api/prediction/admin/users/{id}/password`).
  - List group, click → `/admin/groups/:groupId`.
  - Nút "Thêm group" (modal `POST /api/prediction/admin/groups`).
- `/admin/groups/:groupId` **Cài đặt group**:
  - Combo bet-type Á/Âu → `PUT /api/prediction/admin/groups/{id}/bet-type`.
  - Thành viên + thêm member: autocomplete dropdown (lọc prefix trên list `GET /admin/users`), submit `POST /api/prediction/admin/groups/{id}/members`.
  - Lịch sử nạp tiền + form nạp: ô chọn thành viên (autocomplete lọc trong group) + số tiền → `POST /api/bff/admin/groups/{id}/deposits`. Sau khi xong refetch lịch sử.

---

## File chính sẽ tạo / sửa

**Backend — sửa:**
- `services/prediction-service/app/models.py`, `schemas.py`, `security.py`, `admin_auth.py`, `api/auth.py`, `api/admin.py`
- `services/prediction-service/app/migrations/versions/0004_user_is_admin.py` (mới)
- `services/fixture-service/app/api/fixtures.py`, `schemas.py`, `config.py`
- `services/ledger-service/src/main/java/.../service/{AccountRef.java, LedgerService.java, SettlementService.java}`
- `services/ledger-service/src/main/java/.../api/{AccountController.java, JournalEntryController.java}` (filter endpoints)
- `services/ledger-service/src/test/java/.../LedgerIT.java`, `PostingServiceTest.java`
- `gateway/nginx.conf`, `docker-compose.yml`

**Backend — mới:**
- `services/bff-service/` (toàn bộ: `app/`, `Dockerfile`, `requirements.txt`, `tests/`)

**Frontend — thay toàn bộ `web/`:**
- `web/package.json`, `vite.config.js`, `Dockerfile`, `index.html`
- `web/src/{main.jsx, App.jsx, api/client.js, context/*, components/*, pages/*, styles/*}`

---

## Verification (end-to-end)

1. `docker compose down -v && docker compose up --build` — reset DB + build toàn bộ. Confirm bff-service và web (React build) chạy.
2. Migration prediction tự áp `0004_user_is_admin`; seed tạo `admin/admin` với `is_admin=true`.
3. Login bằng `admin` → màn hình `/admin` hiển thị (route guard pass); login bằng user thường → guard redirect.
4. Trong `/admin`: tạo group mới, đổi bet-type Á/Âu, thêm 2-3 thành viên (autocomplete hoạt động), đổi password 1 user → login lại bằng password mới OK.
5. Trong `/admin/groups/:id`: nạp tiền cho 1 thành viên → lịch sử nạp xuất hiện ở Cài đặt group, Trang chính, và Chi tiết người chơi; "còn phải đóng" giảm đúng (lost − deposited).
6. Tạo vài pick (qua API hoặc UI nếu có), `POST /admin/matches/{id}/force-lock`, set result qua fixture admin → leaderboard cập nhật `money_lost`/`win_rate`/`form`; chi tiết trận hiện pie chart % chọn đội + danh sách người LOST + tổng tiền.
7. Trang chính: đổi group trong `GroupSelector` → bảng leaderboard đổi theo; sort các cột; `Countdown` chạy đúng đến `lock_at` (kickoff − 15 phút).
8. Chi tiết người chơi: pie W/L đúng, lịch sử pick mới→cũ, 3 thẻ tiền khớp leaderboard.
9. Backend test:
   - `cd services/prediction-service && pytest`
   - `cd services/fixture-service && pytest`
   - `cd services/bff-service && pytest`
   - `cd services/ledger-service && mvn test` (cần `LedgerIT` & `PostingServiceTest` đã update assertions).
