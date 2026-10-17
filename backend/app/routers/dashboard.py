from fastapi import APIRouter, Depends, Request

from ..auth import get_current_user
from ..models import DashboardSummary, UserRecord
from ..store import StoreError


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary, operation_id="getDashboardSummary")
def get_summary(request: Request, siteId: str | None = None,
                user: UserRecord = Depends(get_current_user)) -> DashboardSummary:
    if siteId and siteId not in {site.id for site in request.app.state.store.list_sites(user)}:
        raise StoreError(404, "NOT_FOUND", "The requested site was not found.")
    return request.app.state.store.dashboard(user, site_id=siteId)
