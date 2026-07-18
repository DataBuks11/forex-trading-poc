from fastapi import APIRouter, Depends, Query
from repositories.activity_repo import get_activity_logs
from middleware import get_current_user, TokenData

router = APIRouter(prefix="/api/activity", tags=["Activity Log"])


@router.get("")
def activity_log(user: TokenData = Depends(get_current_user),
                 limit: int = Query(50, ge=1, le=200)):
    """Get recent activity log entries."""
    return get_activity_logs(user.user_id, limit)
