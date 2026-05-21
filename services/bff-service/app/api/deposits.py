from fastapi import APIRouter, Depends

from app.aggregation import deposit_items
from app.auth import bearer_token, get_current_user, require_admin
from app.clients import ledger, prediction
from app.schemas import DepositIn, DepositItem

router = APIRouter(tags=["deposits"])


@router.get("/groups/{group_id}/deposits", response_model=list[DepositItem])
def group_deposits(
    group_id: str,
    _user: dict = Depends(get_current_user),
    token: str = Depends(bearer_token),
) -> list[DepositItem]:
    """Every recorded deposit in a group, newest first."""
    members = prediction.get_group_members(group_id, token)
    names = {m["user_id"]: m["display_name"] for m in members}
    return deposit_items(ledger.get_deposits(group_id), names)


@router.post("/admin/groups/{group_id}/deposits", status_code=201)
def create_deposit(
    group_id: str,
    body: DepositIn,
    _admin: dict = Depends(require_admin),
) -> dict:
    """Record a cash pay-in for a group member. Proxied to the ledger."""
    return ledger.post_deposit(group_id, body.depositor, body.amount_minor)
