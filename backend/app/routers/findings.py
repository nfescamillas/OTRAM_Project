from fastapi import APIRouter, Depends, Request

from ..auth import get_current_user
from ..models import Finding, FindingStatus, Severity, UserRecord


router = APIRouter(prefix="/findings", tags=["Findings"])


@router.get("", response_model=list[Finding], operation_id="listFindings")
def list_findings(
    request: Request,
    siteId: str | None = None,
    status: FindingStatus | None = None,
    severity: Severity | None = None,
    user: UserRecord = Depends(get_current_user),
) -> list[Finding]:
    return request.app.state.store.list_findings(user, site_id=siteId, status=status, severity=severity)
