#!/usr/bin/env bash
#
# Prediction League -- end-to-end demo of the settlement saga.
#
# Drives the full choreography across all three services:
#   Prediction (pick + lock) -> PickLocked -> Fixture (project + settle)
#   -> MatchSettled (transactional outbox) -> Ledger (double-entry posting).
#
# Prerequisite: the stack is running -> `docker compose up -d`
# Re-runnable: each run uses a fresh match and fresh users, and asserts only
# about its own players (so leftover state from earlier runs is harmless).
#
set -uo pipefail

GW="http://localhost:8080"
ADMIN_KEY="${ADMIN_API_KEY:-dev-admin-key-change-me}"
TS="$(date +%s)"
PASS=0
FAIL=0

step()  { echo; echo "=== $1 ==="; }
field() { echo "$1" | grep -oE "\"$2\"[ ]*:[ ]*(\"[^\"]*\"|[^,}]*)" | head -1 | sed -E "s/\"$2\"[ ]*:[ ]*//; s/^\"//; s/\"$//"; }
check() {
  if [ "$2" = "$3" ]; then echo "  PASS: $1"; PASS=$((PASS + 1));
  else echo "  FAIL: $1 (expected '$3', got '$2')"; FAIL=$((FAIL + 1)); fi
}
check_ge() {
  if [ -n "$2" ] && [ "$2" -ge "$3" ] 2>/dev/null; then echo "  PASS: $1"; PASS=$((PASS + 1));
  else echo "  FAIL: $1 (expected >= $3, got '$2')"; FAIL=$((FAIL + 1)); fi
}

step "1. Find a scheduled match"
FIXTURES="$(curl -s "$GW/api/fixture/fixtures")"
MATCH_OBJ="$(echo "$FIXTURES" | grep -oE '\{[^{}]*\}' | grep '"status": *"SCHEDULED"' | head -1)"
if [ -z "$MATCH_OBJ" ]; then
  echo "  no SCHEDULED match left -- run: docker compose down -v && docker compose up -d"
  exit 1
fi
MATCH_ID="$(field "$MATCH_OBJ" id)"
echo "  using match $MATCH_ID"

step "2. Register two players"
ALICE="$(curl -s -X POST "$GW/api/prediction/auth/register" -H 'Content-Type: application/json' \
  -d "{\"email\":\"alice+$TS@demo.com\",\"display_name\":\"Alice\",\"password\":\"secret123\"}")"
BOB="$(curl -s -X POST "$GW/api/prediction/auth/register" -H 'Content-Type: application/json' \
  -d "{\"email\":\"bob+$TS@demo.com\",\"display_name\":\"Bob\",\"password\":\"secret123\"}")"
ATOK="$(field "$ALICE" access_token)"; AUID="$(field "$ALICE" user_id)"
BTOK="$(field "$BOB" access_token)";   BUID="$(field "$BOB" user_id)"
echo "  alice=$AUID  bob=$BUID"

step "3. Create a group; Bob joins"
GROUP="$(curl -s -X POST "$GW/api/prediction/groups" -H "Authorization: Bearer $ATOK" \
  -H 'Content-Type: application/json' -d '{"name":"Demo Group"}')"
GID="$(field "$GROUP" id)"
curl -s -X POST "$GW/api/prediction/groups/$GID/join" -H "Authorization: Bearer $BTOK" >/dev/null
echo "  group=$GID"

step "4. Alice predicts HOME; Bob makes no pick (auto-loss)"
curl -s -X POST "$GW/api/prediction/picks" -H "Authorization: Bearer $ATOK" \
  -H 'Content-Type: application/json' \
  -d "{\"group_id\":\"$GID\",\"match_id\":\"$MATCH_ID\",\"predicted_outcome\":\"HOME\"}" >/dev/null
echo "  Alice picked HOME"

step "5. Lock the match -> publishes PickLocked (one event per group)"
LOCK="$(curl -s -X POST "$GW/api/prediction/admin/matches/$MATCH_ID/force-lock" -H "X-Admin-Api-Key: $ADMIN_KEY")"
check_ge "PickLocked event(s) published" "$(field "$LOCK" events_published)" "1"
sleep 4

step "6. Fixture projected the locked picks"
PICKS="$(curl -s "$GW/api/fixture/fixtures/$MATCH_ID/picks")"
ALICE_PICK="$(echo "$PICKS" | grep -oE "\{[^{}]*\"user_id\": *\"$AUID\"[^{}]*\}")"
BOB_PICK="$(echo "$PICKS" | grep -oE "\{[^{}]*\"user_id\": *\"$BUID\"[^{}]*\}")"
check "Alice's pick projected as HOME" "$(field "$ALICE_PICK" predicted_outcome)" "HOME"
check "Bob projected as an auto-loss" "$(field "$BOB_PICK" auto_loss)" "true"

step "7. Admin enters the result 2-0 (HOME win)"
RESULT="$(curl -s -X POST "$GW/api/fixture/admin/matches/$MATCH_ID/result" \
  -H "X-Admin-Api-Key: $ADMIN_KEY" -H 'Content-Type: application/json' -d '{"home_score":2,"away_score":0}')"
check "match settled" "$(field "$RESULT" status)" "settled"
echo "  waiting for outbox -> MatchSettled -> Ledger ..."
sleep 9

step "8. Ledger posted the settlement"
BOB_ACC="$(curl -s "$GW/api/ledger/accounts/PLAYER/$BUID")"
check "Bob (lost) debited his 10000 stake" "$(field "$BOB_ACC" balance_minor)" "-10000"
ALICE_CODE="$(curl -s -o /dev/null -w '%{http_code}' "$GW/api/ledger/accounts/PLAYER/$AUID")"
check "Alice (won) has no posting" "$ALICE_CODE" "404"

step "9. Safety: re-entering the result is rejected"
DUP_CODE="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$GW/api/fixture/admin/matches/$MATCH_ID/result" \
  -H "X-Admin-Api-Key: $ADMIN_KEY" -H 'Content-Type: application/json' -d '{"home_score":2,"away_score":0}')"
check "double settlement rejected (409)" "$DUP_CODE" "409"

echo
echo "================================"
echo "  PASSED: $PASS   FAILED: $FAIL"
echo "================================"
[ "$FAIL" -eq 0 ] || exit 1
